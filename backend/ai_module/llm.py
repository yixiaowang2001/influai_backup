from openai import OpenAI

from backend.configs import API_KEY
from backend.utils import get_logger

logger = get_logger("backend.ai_module.llm")
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def chat(
        system_prompt: str,
        user_prompt: str,
        model_name: str = "qwen-turbo",
        temperature: float = 0.5,
        max_tokens: int = 512
) -> str:
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        extra_body={"enable_thinking": False},
        temperature=temperature,
        max_tokens=max_tokens
    )
    return completion.choices[0].message.content


if __name__ == "__main__":
    print(chat("你是一个助手", "你好"))
