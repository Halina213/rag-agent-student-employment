from fastapi import FastAPI
from utils.Logger import Logger
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from system.system_router import system_router
from contextlib import asynccontextmanager
from agent.system_agent import SystemAgent
import sys
from chat.chat_router import chat_router
from agent.echarts_agent import EchartsAgent
from agent.anlyze_agent import AnlyzeAgent
from agent.sql_question_agent_pg import SqlQuestionAgentAg
import asyncio
import os
from fastapi.staticfiles import StaticFiles

logger = Logger.get_logger(__name__)

@asynccontextmanager
async def creat_agent_instance(app: FastAPI):
    app.state.system_agent = SystemAgent()
    app.state.sql_question_agent_pg = SqlQuestionAgentAg()
    app.state.echarts_agent = EchartsAgent()
    app.state.anlyze_agent = AnlyzeAgent()
    logger.info("所有智能体实例创建成功")
    yield
    logger.info("所有智能体实例销毁成功")

app = FastAPI(title="RAG Agent - 大数据智能体客服系统", lifespan=creat_agent_instance)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(system_router)
app.include_router(chat_router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE_DIR, "static/upload"), exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--loop", "asyncio"]
    import subprocess
    subprocess.run(cmd)
