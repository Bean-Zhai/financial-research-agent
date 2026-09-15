import streamlit as st

from src.agent.llm_agent import (
    ask_agent,
    build_system_prompt,
)
from src.agent.tools import get_available_stocks


st.set_page_config(
    page_title="Financial Research Agent",
    page_icon="📊",
    layout="wide",
)


def initialize_session():
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = [
            {
                "role": "system",
                "content": build_system_prompt(),
            }
        ]

    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []


def clear_conversation():
    st.session_state.agent_messages = [
        {
            "role": "system",
            "content": build_system_prompt(),
        }
    ]

    st.session_state.display_messages = []


initialize_session()


st.title("📊 Financial Research & Data Agent")

st.caption(
    "基于历史市场数据的股票收益、风险、"
    "相关性和波动率分析助手"
)


with st.sidebar:
    st.header("数据库信息")

    stock_result = get_available_stocks()

    if stock_result["success"]:
        st.write(
            f"当前共有 "
            f"{stock_result['number_of_stocks']} 只股票"
        )

        for stock in stock_result["stocks"]:
            st.markdown(
                f"**{stock['ticker']}**  \n"
                f"{stock['start_date']} 至 "
                f"{stock['end_date']}  \n"
                f"{stock['trading_days']} 个交易日"
            )

    else:
        st.error(stock_result["error"])

    st.divider()

    st.header("使用示例")

    st.markdown(
        """
- 比较三只股票2024年的表现
- 哪两只股票的相关性最低？
- 分析NVDA的20日和60日滚动波动率
- 生成三只股票2024年的中文研究报告
"""
    )

    st.divider()

    if st.button(
        "清除对话",
        use_container_width=True,
    ):
        clear_conversation()
        st.rerun()


for message in st.session_state.display_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


question = st.chat_input(
    "请输入你的金融数据分析问题"
)


if question:
    st.session_state.display_messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("正在查询数据并分析……"):
            try:
                answer = ask_agent(
                    question,
                    st.session_state.agent_messages,
                )

                st.markdown(answer)

            except Exception as error:
                answer = f"运行失败：{error}"
                st.error(answer)

    st.session_state.display_messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )