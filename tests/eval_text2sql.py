"""Text-to-SQL 轻量评估：跑一组问题，检查生成的 SQL 是否命中关键字段。

用法：python tests/eval_text2sql.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.sql_question_agent_pg import SqlQuestionAgentAg

# 每个用例：问题 + 期望 SQL 里应出现的关键字段（命中即算通过）
CASES = [
    {"q": "统计不同学历层级的就业率", "must_have": ["degree_level", "employment_rate"]},
    {"q": "哪些专业毕业后1年收入中位数最高", "must_have": ["degree_field", "median_earnings_1yr"]},
    {"q": "不同州的毕业生人数", "must_have": ["institution_state", "total_graduates"]},
    {"q": "各就业行业的平均收入", "must_have": ["industry", "median_earnings"]},
    {"q": "就业率最高的10个专业", "must_have": ["degree_field", "employment_rate"]},
    {"q": "不同学历层级毕业后5年的收入中位数", "must_have": ["degree_level", "median_earnings_5yr"]},
]


async def evaluate():
    agent = SqlQuestionAgentAg()
    passed = 0
    for i, case in enumerate(CASES, 1):
        collected = []
        async for event in agent.agent.astream_events(
            {"messages": [{"role": "user", "content": case["q"]}]},
            {"configurable": {"thread_id": f"eval-{i}"}},
            version="v2",
        ):
            if event["event"] == "on_tool_start":
                collected.append(str(event["data"].get("input", "")))

        sql_text = " ".join(collected).lower()
        hit = all(k.lower() in sql_text for k in case["must_have"]) and bool(collected)
        passed += hit
        print(f"[{'PASS' if hit else 'FAIL'}] {case['q']}")
        print(f"        SQL片段: {sql_text[:160]}")

    total = len(CASES)
    print(f"\nText-to-SQL 准确率: {passed}/{total} = {passed / total * 100:.1f}%")


if __name__ == "__main__":
    asyncio.run(evaluate())