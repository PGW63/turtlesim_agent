import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import cohere
import json
import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()

class TurtlesimLLMAgent(Node):
    def __init__(self):
        super().__init__('turtlesim_llm_agent_node')

        # Cohere client
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise RuntimeError("COHERE_API_KEY not found in environment variables")
        self.client = cohere.Client(api_key)

        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.get_logger().info('💬 거북이 LLM 에이전트 시작됨')

        self.run_input_loop()

    def run_input_loop(self):
        def input_thread():
            while rclpy.ok():
                cmd_input = input("🚀 명령어를 입력하세요: ")
                twist, duration = self.generate_twist_and_duration_from_text(cmd_input)
                if twist:
                    self.get_logger().info(f"🌀 {duration}초간 움직인 후 정지합니다.")
                    threading.Thread(target=self.publish_for_duration, args=(twist, duration)).start()
                else:
                    self.get_logger().warn("⚠️ Twist 명령 생성 실패")

        threading.Thread(target=input_thread, daemon=True).start()

    def publish_for_duration(self, twist: Twist, duration: float):
        rate = self.create_rate(10.0)  # 10Hz
        end_time = time.time() + duration
        while time.time() < end_time and rclpy.ok():
            self.publisher_.publish(twist)
            rate.sleep()
        self.publisher_.publish(Twist())  # 정지
        self.get_logger().info("✅ 정지 완료")

    def generate_twist_and_duration_from_text(self, text: str):
        prompt = (
            "너는 ROS2 거북이 로봇을 제어하는 에이전트야.\n"
            "사용자의 명령을 Twist 메시지와 duration(초)으로 변환해줘.\n"
            "결과는 반드시 JSON 형태로만 출력해. 형식은 다음과 같아:\n"
            '{"twist": {"linear": {"x": float, "y": float, "z": float}, "angular": {"x": float, "y": float, "z": float}}, "duration": float}\n'
            "예시:\n"
            "예시:\n"
            '"작은 원을 그려줘" → {"twist": {"linear": {"x": 1.5, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 1.5}}, "duration": 4.2}\n'
            '"천천히 큰 원을 그려줘" → {"twist": {"linear": {"x": 1.0, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.5}}, "duration": 12.0}\n'
            '"반시계 방향으로 두 바퀴 돌아줘" → {"twist": {"linear": {"x": 2.0, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 2.0}}, "duration": 6.28}\n'
            '"앞으로 가"-> {"twist": {"linear": {"x":1.0, "y":0,0, "z":0.0}, "angular": {"x":0.0, "y":0.0, "z":0.0}}, "duration" : 1.0}\n'
            '"별 하나 그려줘" → {"twist": {"linear": {"x": 1.5, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 2.0}}, "duration": 6.5}\n'
            f"명령어: {text}"
        )
        try:
            response = self.client.chat(message=prompt, model="command-r", temperature=0.3)
            parsed = json.loads(response.text.strip())
            twist = Twist()
            twist.linear.x = float(parsed["twist"]["linear"].get("x", 0.0))
            twist.linear.y = float(parsed["twist"]["linear"].get("y", 0.0))
            twist.linear.z = float(parsed["twist"]["linear"].get("z", 0.0))
            twist.angular.x = float(parsed["twist"]["angular"].get("x", 0.0))
            twist.angular.y = float(parsed["twist"]["angular"].get("y", 0.0))
            twist.angular.z = float(parsed["twist"]["angular"].get("z", 0.0))
            duration = float(parsed.get("duration", 3.0))
            return twist, duration
        except Exception as e:
            self.get_logger().error(f"JSON 파싱 실패: {e}")
            return None, 0.0

def main(args=None):
    rclpy.init(args=args)
    node = TurtlesimLLMAgent()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
