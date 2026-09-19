# 小智 RAG Agent：PSEO 高校毕业生就业与收入数据分析系统

这是一个基于 FastAPI、Vue3、LangChain、LangGraph、MySQL 和大模型接口的智能数据分析项目。系统支持邮箱验证码登录、自然语言查询 PSEO 就业与收入数据、生成分析结论和 ECharts 图表。

## 功能

- 邮箱验证码登录
- PSEO 就业与收入数据自然语言问答
- 就业率、收入中位数、学校、专业、学历、行业维度分析
- ECharts 图表生成
- 聊天记录保存
- CSV / Excel 数据上传导入

## 技术栈

| 模块 | 技术 |
|---|---|
| 后端 | FastAPI、Uvicorn |
| 智能体 | LangChain、LangGraph |
| 模型接口 | OpenAI 兼容接口，例如 DashScope |
| 数据库 | MySQL 8.0 |
| 验证码缓存 | 后端内存缓存 |
| 前端 | Vue3、Vite、ECharts |

## 目录结构

```text
rag-agent-student-employment/
├── agent/                 # 智能体模块
├── chat/                  # 聊天接口
├── data/                  # 示例数据
├── docs/                  # 文档
├── frontend/              # Vue3 前端
├── model/                 # 大模型配置
├── schema/                # Pydantic 参数模型
├── scripts/               # PowerShell 启动脚本
├── static/upload/         # 上传文件目录
├── system/                # 登录和验证码接口
├── tool/                  # MySQL、邮件等工具
├── utils/                 # 日志、文件导入等工具
├── .env.example           # 环境变量模板
├── init_db.py             # 初始化数据库
├── import_data.py         # 导入示例数据
├── main.py                # 后端入口
└── requirement.txt        # 后端依赖
```

## 环境准备

 PyCharm、phpStudy_pro、MySQL 8.0、HBuilderX、HeidiSQL,还需要确认：

- Python 3.10 或以上
- Node.js 18 或以上
- MySQL 8.0 已启动
- 已有可用的 `OPENAI_API_KEY`
- QQ 邮箱 SMTP 授权码，若要使用验证码邮件

## 配置

复制环境变量模板：

```powershell
copy .env.example .env
```

后填写：

```env
OPENAI_API_KEY=你的模型Key
MYSQL_PASSWORD=你的MySQL密码
EMAIL_USER=你的QQ邮箱
EMAIL_PASSWORD=你的QQ邮箱SMTP授权码
```


## 启动后端

```powershell
pip install -r requirements.txt
python init_db.py
python import_data.py
python main.py
```

后端默认运行在：

```text
http://localhost:8000
```

## 启动前端

```powershell
cd frontend
npm install
npm run dev
```

前端默认运行在：

```text
http://localhost:5173
```

## 登录测试

`init_db.py` 会插入几个测试用户。你可以先用 `.env` 中配置的邮箱，或在 `init_db.py` 中添加自己的邮箱后重新初始化。

登录流程依赖：

- MySQL 中存在该邮箱用户
- 邮箱 SMTP 配置正确
- 后端服务保持运行，验证码会临时保存在后端内存中，重启后验证码会失效

## PSEO 数据导入

将下载后的 PSEO CSV/Excel 文件放到 `data/` 目录，例如：

```text
data/pseo_outcomes.csv
```

在 `.env` 中配置：

```text
DATA_FILE_PATH=data/pseo_outcomes.csv
```

然后依次运行：

```powershell
python init_db.py
python import_data.py
```

即可重建 `student_placement` 表并导入 PSEO 数据。导入脚本已内置常见 PSEO 字段映射，缺少的非关键字段会置空，便于先快速跑通。

## 可提问示例

- 统计一下不同学历层级的就业率
- 哪些专业毕业后 1 年收入中位数最高
- 画一个不同州学校的收入中位数柱状图
- 分析不同就业行业的毕业生人数和收入差异


