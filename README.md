# Financial Research & Data Agent

这是一个基于 Python 开发的金融研究智能体项目，结合了历史市场数据、量化分析、大模型工具调用、自动化报告生成和 Streamlit 交互式网页。

用户可以用自然语言提出金融数据问题。大模型会判断用户意图、选择合适的 Python 工具、查询 SQLite 数据库、计算金融指标，并根据真实数据生成回答。

## 核心功能

* 获取并存储历史股票数据
* 使用 SQLite 管理结构化金融数据
* 支持自然语言金融研究问答
* 由大模型自动选择并调用分析工具
* 支持自定义日期区间分析
* 支持多轮对话记忆
* 自动生成中文股票研究报告
* 提供 Streamlit 交互式金融数据网页
* 使用自动化测试验证金融计算与错误处理

## 系统工作流程

```mermaid
flowchart LR
    A[市场数据] --> B[SQLite数据库]
    B --> C[Python分析工具]
    C --> D[大模型Agent]
    D --> E[Streamlit网页]
```

大模型负责理解用户问题并选择工具，所有金融指标均由 Python 根据 SQLite 数据库中的真实数据计算，避免由大模型直接编造数值。

## 金融分析功能

项目目前支持以下分析：

* 区间累计收益率
* 年化波动率
* 夏普比率
* 最大回撤
* 每日收益率相关性
* 20日和60日滚动波动率
* 100美元标准化投资价值变化
* 自定义股票与日期区间比较

夏普比率目前假设无风险利率为0%，年化波动率按照每年252个交易日计算。

## 当前数据集

示例数据库目前包含以下股票的日度历史数据：

* 苹果公司：`AAPL`
* 微软公司：`MSFT`
* 英伟达公司：`NVDA`

当前示例数据区间为：

```text
2022-01-03 至 2025-12-31
```

数据库和分析工具采用动态设计，加载新数据后可以继续支持其他股票。

## 技术栈

* Python
* pandas
* NumPy
* SQLite
* Matplotlib
* Streamlit
* OpenAI兼容的大模型API
* GLM-4-Flash
* pytest
* Git与GitHub

## 项目结构

```text
financial-research-agent/
├── app.py
├── pages/
│   └── 1_Data_Charts.py
├── database/
│   └── schema.sql
├── reports/
│   ├── figures/
│   │   └── stock_performance.png
│   └── stock_analysis_report.md
├── src/
│   ├── agent/
│   │   ├── cli_agent.py
│   │   ├── llm_agent.py
│   │   ├── test_model.py
│   │   └── tools.py
│   ├── analysis/
│   │   ├── calculate_returns.py
│   │   ├── plot_performance.py
│   │   ├── query_prices.py
│   │   └── risk_metrics.py
│   ├── data_pipeline/
│   │   └── fetch_prices.py
│   ├── database/
│   │   ├── create_database.py
│   │   └── load_data.py
│   ├── reporting/
│   │   ├── custom_report.py
│   │   └── generate_report.py
│   └── main.py
├── tests/
│   └── test_tools.py
├── .env.example
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

项目包含一个用于演示和部署的小型SQLite数据库。原始数据、处理过程中的数据文件、API密钥和动态生成的报告不会被Git追踪。

## 安装方法

### 1. 克隆项目

```bash
git clone <repository-url>
cd financial-research-agent
```

请将 `<repository-url>` 替换为实际的 GitHub 仓库地址。

### 2. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 安装依赖

安装项目运行所需依赖：

```powershell
pip install -r requirements.txt
```

如果需要运行测试，则安装开发依赖：

```powershell
pip install -r requirements-dev.txt
```

### 4. 配置环境变量

在项目根目录新建 `.env` 文件：

```text
ZHIPU_API_KEY=your_api_key_here
```

请勿提交 `.env` 文件，也不要公开真实的 API Key。

## 准备数据库

依次运行数据处理程序：

```powershell
python src/data_pipeline/fetch_prices.py
python src/database/create_database.py
python src/database/load_data.py
```

该流程会获取历史股价数据、创建 SQLite 数据库，并将处理后的数据写入数据库。

## 启动网页

运行 Streamlit 网站：

```powershell
streamlit run app.py
```

然后在浏览器中打开：

```text
http://localhost:8501
```

网页目前包含：

* AI金融研究对话界面
* 研究报告下载功能
* 交互式金融数据图表
* 股票筛选功能
* 日期区间选择功能
* 滚动波动率窗口设置

## 启动终端版Agent

运行：

```powershell
python -m src.agent.llm_agent
```

输入：

```text
quit
```

可以退出程序；输入：

```text
clear
```

可以清除当前对话记忆。

## 示例问题

```text
比较AAPL、MSFT和NVDA在2024年的表现。
```

```text
哪两只股票的每日收益率相关性最低？
```

```text
分析NVDA的20日和60日滚动波动率。
```

```text
为数据库中的全部股票生成一份2024年的中文研究报告。
```

Agent同时支持中文和英文问题。

## 自动化测试

运行全部测试：

```powershell
python -m pytest -v
```

当前测试覆盖以下功能：

* 查询数据库中的可用股票
* 自定义日期区间
* 股票代码大小写处理
* 不存在的股票处理
* 错误日期格式处理
* 起止日期颠倒处理
* 每日收益率相关性分析
* 滚动波动率分析

当前测试结果：

```text
8 passed
```

## 计算方法与项目限制

* 所有收益指标均使用调整后收盘价计算。
* 分析结果完全基于历史价格数据。
* 夏普比率目前假设无风险利率为0%。
* 相关性衡量不同股票每日收益率之间的线性关系。
* 滚动波动率不能预测未来股价涨跌方向。
* 当前项目暂未考虑交易成本、税费和滑点。
* 当前项目暂未加入投资组合优化。
* 历史表现不能保证未来收益。

## 后续升级方向

* 加入SPY等市场基准
* 计算Alpha、Beta和Sortino比率
* 加入VaR与CVaR风险指标
* 加入EWMA与GARCH波动率模型
* 接入财经新闻和公司基本面数据
* 加入投资组合优化功能
* 支持下载PDF格式研究报告
* 将Streamlit网站部署为公开应用

## 免责声明

本项目仅用于教育、学习和数据研究，不构成任何投资建议。
