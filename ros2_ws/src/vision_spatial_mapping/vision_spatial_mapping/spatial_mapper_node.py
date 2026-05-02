from my_robot_interfaces.srv import GenerateCaption
from my_robot_interfaces.msg import RgbImageDepth
from tf2_geometry_msgs import do_transform_point
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import CameraInfo
from rclpy.duration import Duration
from cv_bridge import CvBridge
from rclpy.node import Node 
import numpy as np
import requests
import tf2_ros
import rclpy
import time
import cv2


class SpatialGroundingNode(Node):
    """ROS2 node to compute transform of 3D center pixel point in map frame from depth image"""

    def __init__(self):
        super().__init__("get_coordinate_node")

        # Declare & Get parameters
        self.declare_parameter('raw_depth_image_topic', '/camera/rgbd')
        self.raw_depth_image_topic = self.get_parameter('raw_depth_image_topic').value

        # Camera instrinsic 
        self.fx, self.fy, self.cx, self.cy =  None, None, None, None

        # Flag to ensure coordinate calculation of 3D point is done after getting intrinisc camera values
        self.received_camera_info = False

        # Need to add parameter for process interval
        self.process_interval_sec = 1 
        self.latest_rgb_image_depth_msg = None

        self.tf_buffer = tf2_ros.Buffer(cache_time=Duration(seconds=15))
        listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.bridge = CvBridge()

        # Create subscriber, publisher, service client and timer
        self.camera_info_subscriber = self.create_subscription(CameraInfo, '/camera/camera_info', self.callback_get_camera_info, 1)
        self.raw_image_depth_subscriber = self.create_subscription(RgbImageDepth, self.raw_depth_image_topic, self.rgbd_callback, 10)
        self.timer = self.create_timer(self.process_interval_sec, self.callback_get_coordinate_in_map)
        self.caption_generator_client = self.create_client(GenerateCaption, 'generate_caption')
        while not self.caption_generator_client.wait_for_service(1.0):
            self.get_logger().warning("Waiting for caption service...")


    def rgbd_callback(self, msg):
        """Store latest image"""
        try:
            self.latest_rgb_image_depth_msg = msg
        except Exception as e:
            self.get_logger().warn(f'Image conversion failed: {e}')

    def callback_get_camera_info(self, msg):
        camera_intrinsic_info = msg.k
        self.get_logger().info(f"camera intrinsic parameter {camera_intrinsic_info}")
        self.fx = msg.k[0]
        self.fy = msg.k[4]
        self.cx = msg.k[2]
        self.cy = msg.k[5]

        self.get_logger().info(f"Camera intrinsics received -> fx: {self.fx:.3f}, fy: {self.fy:.3f}, cx: {self.cx:.3f}, cy: {self.cy:.3f}")

        # Destroy the subscriber once camera_info is obtained
        self.destroy_subscription(self.camera_info_subscriber)
        self.received_camera_info = True

    def callback_get_coordinate_in_map(self):
        if not self.received_camera_info: 
            self.get_logger().warn("Waiting for camera intrinsics...")
            return
        if self.latest_rgb_image_depth_msg is None:
            self.get_logger().warn("Waiting for RgbImageDepth msg...")
            return
        
        try:
            depth = self.latest_rgb_image_depth_msg.depth
            depth_image = self.bridge.imgmsg_to_cv2(depth, desired_encoding='passthrough')
            # self.get_logger().info(f"depth_shape : {depth_image.shape}")
            
            h, w = depth_image.shape
            u = w // 2
            v = h // 2

            # Get depth value at central pixel
            Z = depth_image[v, u]
            # self.get_logger().info(f"Depth value at center pixel (u={u}, v={v}): Z={Z} (type: {type(Z)})")

            # Avoid invalid depth
            if Z == 0 or np.isnan(Z):
                self.get_logger().warn("Depth is zero at selected pixel, skipping...")
                return
            
            # Back-project 2D point (u, v) with depth Z to obtain 3D point coordinates in the camera frame
            X = (u - self.cx) * Z / self.fx
            Y = (v - self.cy) * Z / self.fy

            # Create a PointStamped representing the 3D point in the camera coordinate frame
            p_cam = PointStamped()
            p_cam.header = self.latest_rgb_image_depth_msg.camera_image.header    

            p_cam.point.x = float(X)
            p_cam.point.y = float(Y)
            p_cam.point.z = float(Z)

            self.get_logger().info(f"Point in camera frame: X={X}, Y={Y}, Z={Z}")

            # Lookup transform from camera frame to map frame at the timestamp of the image
            transform_robot = self.tf_buffer.lookup_transform(
                "map",
                p_cam.header.frame_id,
                p_cam.header.stamp,
                Duration(seconds=2)
            )

            # Transform the 3D point from camera frame to map frame
            p_map = do_transform_point(p_cam, transform_robot)
            self.get_logger().info(f"Point in map frame: X={p_map.point.x}, Y={p_map.point.y}, Z={p_map.point.z}")

            self.get_caption_from_image(self.latest_rgb_image_depth_msg.camera_image, p_map) 
               
        except Exception as e:
            self.get_logger().warn(f"Error occurred: {e}")

    def get_caption_from_image(self, image, p_map):
        try:
            req = GenerateCaption.Request()
            req.image = image
        
            self.get_logger().info("Sending image to caption generation service...")
            future = self.caption_generator_client.call_async(req)

            future.add_done_callback(
                lambda f: self.handle_caption_response(f, image, p_map)
            )

        except Exception as e:
            self.get_logger().warn(f"Service call failed: {e}")
    
    def handle_caption_response(self, future, image, p_map):
        try:
            result = future.result()
            if result is None:
                self.get_logger().warn("Caption service returned None")
                return
            if result.caption == '': 
                self.get_logger().warn("Caption generation returned empty string, skipping API call.")
                return
            
            cv_image = self.bridge.imgmsg_to_cv2(image, desired_encoding='bgr8')
            _, buffer = cv2.imencode('.jpg', cv_image)

            # Making http call to clip_faiss_server
            files = {'file': ('image.jpg', buffer.tobytes(), 'image/jpeg')}
            data = {
                'x': str(p_map.point.x),
                'y': str(p_map.point.y),
                'z': str(p_map.point.z),
                'caption' : result.caption
            }
            self.get_logger().info(f"Making API call with data: {data}")
            response = requests.post("http://127.0.0.1:8000/create_embedding", files=files, data=data)
            self.get_logger().info(f"Response: {response.json()}")

            if response.status_code == 200:
                self.get_logger().info(f"Response: {response.json()}")
            else:
                self.get_logger().warn(f"API error: {response.status_code}")

        except Exception as e:
            self.get_logger().warn(f"Request failed: {e}")

def main(args = None):
    rclpy.init(args = args)
    node = SpatialGroundingNode()

    try :
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down node...")
    finally:
        node.destroy_node()  
        node.thread_pool.shutdown(wait=True) 
        rclpy.shutdown()


if __name__ == '__main__':
    main()

