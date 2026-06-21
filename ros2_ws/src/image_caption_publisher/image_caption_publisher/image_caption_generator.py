import image_caption_publisher.caption_http_client as client
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from rclpy.node import Node
import rclpy

class ImageCaptionGeneratorNode(Node):
    def __init__(self):
        super().__init__('image_caption_generator_node')
        self.get_logger().info('ImageCaptionGenerator Node Starting...')

        # Declare parameters
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('caption_topic', '/visual_memory/caption')
        self.declare_parameter('caption_interval', 0.5) # seconds

        # Get parameters
        self.image_topic = self.get_parameter('image_topic').value
        self.caption_topic = self.get_parameter('caption_topic').value
        self.caption_interval = self.get_parameter('caption_interval').value
        self.http_client = client.HttpClient(timeout=4.0) # Increased timeout to accommodate higher latency on the first caption request.
        
        # Setup
        self.bridge = CvBridge()
        self.current_image = None

        # Publishers & Subscribers & Services
        self.caption_pub = self.create_publisher(String, self.caption_topic, 10)
        self.image_sub = self.create_subscription(Image, self.image_topic, self.image_callback, 10)

        # Timer for periodic captioning (handles rate limiting)
        self.timer = self.create_timer(self.caption_interval, self.caption_timer_callback)
        
    def image_callback(self, msg):
        """Store latest image from Gazebo/camera"""
        try:
            self.current_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().warn(f'Image conversion failed: {e}')
    
    def caption_timer_callback(self):
        """
        Generate caption every X seconds if new image frame 
        available is different from the previous one.
        """
        if self.current_image is None: return 

        if self.http_client.caption_future is not None and self.http_client.caption_future.done():
                caption = self.http_client.caption_future.result()
                self.http_client.caption_future = None

                if caption:
                    msg = String()
                    msg.data = caption
                    self.caption_pub.publish(msg)
                    self.get_logger().info(f'caption generated: {caption}')
    
        if self.http_client.caption_future is None:
            self.http_client.caption_future = self.http_client.executor_pool.submit(self.http_client.generate_caption, self.current_image)

def main(args=None):
    rclpy.init(args=args)
    try:
        node = ImageCaptionGeneratorNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        node.http_client.close()
        rclpy.shutdown()

if __name__ == '__main__':
    main()