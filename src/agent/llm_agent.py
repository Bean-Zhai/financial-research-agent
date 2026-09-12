import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.agent.tools import (
    compare_stocks,
    get_available_stocks,
    get_latest_prices,
    get_stock_metrics,
)


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

MODEL_NAME = "glm-4-flash-250414"


SYSTEM_PROMPT = """
你是一个金融数据研究助手。

项目使用SQLite数据库保存历史股票数据。不要假设数据库
包含哪些股票，必要时应调用get_available_stocks进行查询。

当用户询问“有哪些股票”“全部股票”或者没有明确给出
股票代码便询问“哪只股票最好”时，应先调用
get_available_stocks。如果还需要比较，再根据查询到的
股票代码调用compare_stocks。

你可以使用工具查询价格、分析单只股票，或者比较多只股票。

要求：
1. 必须根据工具返回的真实数据回答，不能编造数字。
2. 使用简洁、清晰的中文。
3. 百分比需要转换成容易阅读的形式。
4. 明确说明分析基于历史数据，不构成投资建议。
5. 如果用户询问数据库不存在的股票，如TSLA，应明确说明没有数据。
6. 夏普比率越高，表示单位波动风险获得的历史收益越高，不能直接解释为股票本身风险更低。
7. 最大回撤为负数，绝对值越大代表历史亏损幅度越严重。
8. 累计收益率为520%表示期末价值约为期初的6.2倍，或者盈利约为初始投入的5.2倍。
"""


TOOL_DEFINITIONS = [
    {
        "type": "function",
         "function": {
            "name": "get_available_stocks",
            "description": (
                "查询数据库目前包含哪些股票，"
                "以及每只股票的数据日期范围和交易日数量。"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_metrics",
            "description": (
                "查询并计算一只股票的累计收益率、"
                "年化波率、夏普比率和最大回撤。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": (
                            "股票代码，例如AAPL、MSFT或NVDA。"
                        ),
                    }
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_prices",
            "description": (
                "查询一只股票最近若干个交易日的"
                "收盘价和成交量。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "股票代码。",
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "需要查询的交易日数量，默认5天。"
                        ),
                        "default": 5,
                    },
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_stocks",
            "description": (
                "比较多只股票的收益率、波动率、"
                "夏普比率和最大回撤。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": (
                            "需要比较的股票代码列表。"
                        ),
                    }
                },
                "required": ["tickers"],
            },
        },
    },
]


TOOL_FUNCTIONS = {
    "get_available_stocks": get_available_stocks,
    "get_stock_metrics": get_stock_metrics,
    "get_latest_prices": get_latest_prices,
    "compare_stocks": compare_stocks,
}


def execute_tool(tool_name, arguments):
    if tool_name not in TOOL_FUNCTIONS:
        return {
            "success": False,
            "error": f"不存在工具：{tool_name}",
        }

    try:
        parsed_arguments = json.loads(arguments)
        tool_function = TOOL_FUNCTIONS[tool_name]

        return tool_function(**parsed_arguments)

    except (json.JSONDecodeError, TypeError) as error:
        return {
            "success": False,
            "error": f"工具参数错误：{error}",
        }


def ask_agent(question, messages):
    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    for _ in range(5):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.2,
        )

        assistant_message = response.choices[0].message

        messages.append(
            assistant_message.model_dump(
                exclude_none=True
            )
        )

        if not assistant_message.tool_calls:
            return assistant_message.content

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"[调用工具] {tool_name}")
            print(f"[工具参数] {arguments}")

            tool_result = execute_tool(
                tool_name,
                arguments,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                    ),
                }
            )

    return "工具调用次数过多，本次分析已停止。"


def main():
    print("Financial Research LLM Agent")
    print("输入 quit 可以退出。")
    print("输入 clear 可以清除对话记忆。\n")

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    while True:
        question = input("你：").strip()

        if question.lower() in ["quit", "exit", "退出"]:
            print("Agent：再见！")
            break

        if question.lower() in ["clear", "清除"]:
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ]

            print("Agent：对话记忆已清除。\n")
            continue

        if not question:
            continue

        try:
            answer = ask_agent(
                question,
                messages,
            )

            print(f"\nAgent：{answer}\n")

        except Exception as error:
            print(f"\n运行失败：{error}\n")

if __name__ == "__main__":
    main()