import os
import cohere
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("COHERE_API_KEY")

client = cohere.Client(API_KEY)

def parse_command(text: str) -> str:
    system_prompt = (
        "사용자의 명령을 다음 중 하나의 동작으로 단답형으로 변환해줘:\n"
        "- forward\n- backward\n- left\n- right\n- stop\n\n"
        "그 외에는 unknown으로 답해줘.\n"
        f"명령어: {text}"
    )
    response = client.chat(
        message=system_prompt,
        model="command-r",
        temperature=0.2,
    )
    return response.text.strip().lower()
