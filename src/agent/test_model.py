import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

api_key = os.getenv("ZHIPU_API_KEY")

if not api_key:
    raise ValueError(
        "没有找到ZHIPU_API_KEY，请检查.env文件。"
    )

client = OpenAI(
    api_key=api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4",
)

response = client.chat.completions.create(
    model="glm-4-flash-250414",
    messages=[
        {
            "role": "system",
            "content": (
                "你是一个金融数据分析助手，"
                "请使用简洁、准确的中文回答。"
            ),
        },
        {
            "role": "user",
            "content": "请用一句话解释什么是夏普比率。",
        },
    ],
    temperature=0.2,
)

answer = response.choices[0].message.content

print("模型连接成功！")
print(f"模型回答：{answer}")
