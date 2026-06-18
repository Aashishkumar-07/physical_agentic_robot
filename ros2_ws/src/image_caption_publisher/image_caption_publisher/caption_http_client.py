from typing import Optional
import httpx
import cv2

class HttpClient:
    """
    The ROS2 executor acts as the application's event loop and blocks
    the main thread via rclpy.spin(). It listens for ROS2 events and
    invokes the corresponding callbacks.

    Python coroutines are not natively scheduled by the standard ROS2
    executor. So, a dedicated worker thread is used for HTTP client

    Only one caption request is made at a time. A new image is not
    sent until the previous caption response is received, therefore a
    simple blocking HTTP client is sufficient and asyncio is not needed.   
     """ 

    def __init__(self,timeout: float = 2.0):
        """
        Using HTTP/2 to reuse the same socket connection for multiple requests.

        HTTP/2 automatically compresses request headers (HPACK). For image 
        uploads, payload size dominates header size, so the benefit is 
        relatively small compared to image compression.
        """
        self.client = httpx.Client(http2=True,timeout=timeout)

    def generate_caption(self, cv_image) -> Optional[str]:
        """
        Images are currently sent at their original quality. If network bandwidth becomes a bottleneck, 
        JPEG quality can be reduced during encoding to decrease payload size.
        """
        try :
            success, encoded_image = cv2.imencode(".jpg",cv_image) # Expects BGR image
            if not success:
                print("Failed to encode image")
                return "Error in generating caption"
            image_bytes = encoded_image.tobytes()

            response = self.client.post(
                "http://127.0.0.1:8000/caption",
                content=image_bytes,
                headers={"Content-Type": "image/jpeg"} 
            )

            if response.status_code != 200:
                print(f"HTTP request failed with status code: {response.status_code}")
                return "Error in generating caption"

            payload = response.json()
            if payload["changed"]:
                return payload["caption"]
            return None
            
        except Exception as e:
            print(f"Error in HTTP request: {e}")
            return "Error in generating caption"

    def close(self):
        self.client.close()