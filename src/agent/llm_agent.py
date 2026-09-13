import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.agent.tools import (
    analyze_rolling_volatility,
    calculate_correlation,
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
9. 如果用户指定某一年，例如“2024年”，应将开始日期设置为2024-01-01，结束日期设置为2024-12-31。
10. 回答时应使用工具实际返回的首个和最后一个交易日，不要把休市日称为交易日。
11. 股票相关性必须解释为每日收益率之间的相关性，不能表述为股价水平之间的相关性。
12. 较低的相关性通常意味着相对更好的分散化效果，但不能仅凭相关系数作出投资决策。
13. 20日滚动波动率大致反映近期一个月的风险，60日滚动波动率大致反映近期一个季度的风险。
14. 滚动波动率越高表示收益率波动越剧烈，但它不直接代表股票一定会亏损。
15. 回答滚动波动率问题时，应说明峰值日期和窗口长度。
"""


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_available_stocks",
            "description": (
                "查询数据库目前包含哪些股票，"
                "以及每只股票的数据范围和交易日数量。"
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
                "年化波动率、夏普比率和最大回撤。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": (
                            "股票代码，例如AAPL、MSFT或NVDA。"
                        ),
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "分析开始日期，使用YYYY-MM-DD格式。"
                            "用户没有指定时不要传入。"
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                            "分析结束日期，使用YYYY-MM-DD格式。"
                            "用户没有指定时不要传入。"
                        ),
                    },
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
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "比较开始日期，使用YYYY-MM-DD格式。"
                            "用户没有指定时不要传入。"
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                            "比较结束日期，使用YYYY-MM-DD格式。"
                            "用户没有指定时不要传入。"
                        ),
                    },
                },
                "required": ["tickers"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_correlation",
            "description": (
                "计算两只或多只股票每日收益率之间的"
                "相关系数，并找出相关性最高和最低的组合。"
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
                            "需要进行相关性分析的股票代码列表。"
                        ),
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "分析开始日期，使用YYYY-MM-DD格式。"
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                        "   分析结束日期，使用YYYY-MM-DD格式。"
                        ),
                    },
                },
                "required": ["tickers"],
            },
        },
    },
]
TOOL_DEFINITIONS.append(
    {
        "type": "function",
        "function": {
            "name": "analyze_rolling_volatility",
            "description": (
                "计算股票在不同滚动窗口下的年化波动率，"
                "并找出波动率峰值及其日期。"
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
                            "需要分析的股票代码列表。"
                        ),
                    },
                    "windows": {
                        "type": "array",
                        "items": {
                            "type": "integer",
                        },
                        "description": (
                            "滚动窗口，例如20日和60日。"
                            "用户未指定时使用20日和60日。"
                        ),
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "分析开始日期，使用YYYY-MM-DD格式。"
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                            "分析结束日期，使用YYYY-MM-DD格式。"
                        ),
                    },
                },
                "required": ["tickers"],
            },
        },
    }
)

TOOL_FUNCTIONS = {
    "get_available_stocks": get_available_stocks,
    "get_stock_metrics": get_stock_metrics,
    "get_latest_prices": get_latest_prices,
    "compare_stocks": compare_stocks,
    "calculate_correlation": calculate_correlation,
    "analyze_rolling_volatility": analyze_rolling_volatility,
}

def build_system_prompt():
    stock_result = get_available_stocks()

    if not stock_result["success"]:
        return SYSTEM_PROMPT

    available_tickers = [
        stock["ticker"]
        for stock in stock_result["stocks"]
    ]

    ticker_text = ", ".join(available_tickers)

    database_context = f"""

当前数据库实际包含的股票代码为：{ticker_text}。

当用户说“这些股票”“全部股票”或“三只股票”，但没有
明确列出代码时，必须使用上述全部股票。不得自行从常识
中选择或补充其他股票代码。

如果用户明确查询列表之外的股票，可以调用工具验证，
但不能编造不存在的数据。
"""

    return SYSTEM_PROMPT + database_context

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
        "content": build_system_prompt(),
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
                    "content": build_system_prompt(),
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