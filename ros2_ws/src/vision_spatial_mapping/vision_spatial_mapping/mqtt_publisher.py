from pyaml_env import parse_config
import paho.mqtt.client as mqtt
from pathlib import Path
import time, json

BASE_DIR = Path(__file__).resolve().parent

class MQTTPublisher:
    def __init__(self, config_path: str = None):
        config_file = config_path or BASE_DIR.joinpath("mqtt_config.yaml")
        self.config = parse_config(config_file)

        broker_config = self.config["broker"]
        publisher_config = self.config["publisher"]

        self.host = broker_config["host"]
        self.port = int(broker_config["port"])
        self.username = broker_config["username"]
        self.password = broker_config["password"]

        self.qos = int(publisher_config["qos"])
        self.topic = publisher_config["topic"]
        self.client_id = publisher_config["client_id"]
        
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTv5,
            client_id=self.client_id,
        )
        self.client.username_pw_set(username=self.username, password=self.password)

        # callbacks internally called by paho-mqtt client 
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        self._connect()

    # ===============================
    # MQTT Callbacks
    # ===============================
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"[MQTT] Connected to " f"{self.host}:{self.port}")
        else:
            print(f"[MQTT] Connection failed "f"(reason_code={reason_code})")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            print(f"[MQTT] Unexpected disconnect " f"(reason_code={reason_code})")

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        print(f"[MQTT] Message acknowledged " f"(mid={mid})")

    # ===============================
    # MQTT Connection Lifecycle
    # ===============================
    def _connect(self):
        """
        Connect to RabbitMQ MQTT broker.
        loop_start() launches a background networking thread.
        """

        self.client.connect(host=self.host, port=self.port, keepalive=60)
        self.client.loop_start()

    def disconnect(self):
        """
        Gracefully stop background networking and disconnect.
        """
        
        self.client.loop_stop()
        self.client.disconnect()

    # ===============================
    # Public API
    # ===============================

    def publish(self,payload: dict,topic: str = None) -> bool:
        """
        Publish a JSON payload.

        Args:
            payload:
                Dictionary to serialize and publish.

            topic:
                Optional topic to override default. 
                If None, uses the topic specified in the config.
                
        Returns:
            True if queued successfully.
            False otherwise.
        """

        publish_topic = topic or self.topic

        try:
            message = json.dumps(payload)

            result = self.client.publish(topic=publish_topic, payload=message, qos=self.qos)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT] Queued message " f"to topic='{publish_topic}'")
                return True

            print(f"[MQTT] Publish failed "f"(rc={result.rc})")
            return False

        except Exception as e:
            print(f"[MQTT] Exception while publishing: {e}")
            return False

# ===============================
# Quick smoke-test  
# ===============================
# if __name__ == "__main__":
#     print("Starting MQTT Publisher...")
#     publisher = MQTTPublisher()
#     # time.sleep(1)   # Give the connect callback time to fire
 
#     # publisher.publish({
#     #     "image_url": "g",
#     #     "coordinate": {"x": 1.23, "y": 4.56, "z": 0.0}
#     # })
 
    
#     time.sleep(1)
#     publisher.disconnect()
