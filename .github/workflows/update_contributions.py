#!/usr/bin/env python3
"""Fetch merged PRs by ech0hol on bytedance/deer-flow and update README.md contributions section."""

import httpx
import json
import re
import os
from datetime import datetime

# Fetch all merged PRs by ech0hol on bytedance/deer-flow
prs = []
page = 1
while True:
    resp = httpx.get(
        "https://api.github.com/repos/bytedance/deer-flow/pulls",
        params={
            "state": "closed",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
            "page": page,
        },
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "ech0hol",
        },
        timeout=30,
    )
    data = resp.json()
    if not data:
        break
    for pr in data:
        if pr.get("merged_at") and pr["user"]["login"] == "ech0hol":
            prs.append(pr)
    if len(data) < 100:
        break
    page += 1

# Sort by merged_at ascending
prs.sort(key=lambda p: p["merged_at"])

# Translate PR descriptions to Chinese
def translate(title, body):
    """Map known PR titles to Chinese descriptions."""
    mapping = {
        "fix(frontend): prevent user message bubble overflow with long unbreakable strings": "修复前端用户消息气泡长文本溢出问题",
        "fix(runtime): propagate interrupt through SSE values events for LangGraph SDK": "修复 SSE 序列化管道吞掉 __interrupt__ 信号，恢复 human-in-the-loop 中断能力",
        "fix(smoke-test): add auth-aware frontend checks with login support": "增强冒烟测试认证流程支持",
        "fix(security): inject system context as SystemMessage for role isolation (#3630)": "设计角色隔离方案，将系统上下文注入为 SystemMessage 防止 prompt injection",
        "fix(security): add input sanitization middleware for prompt-injection defense (#3630)": "新建输入净化中间件转义用户输入中的框架保留标签，防御 prompt injection",
        "fix(memory): filter hide_from_ui HumanMessages from memory builder": "过滤 hide_from_ui 的 HumanMessage 避免污染记忆构建",
        "fix(agents): coalesce SystemMessages before LLM request": "合并多轮对话累积的 SystemMessage，修复严格后端 400 报错",
        "fix(middleware): prevent ID-swap recursive injection and orphan peer compression": "修复 ID-swap 消息替换的递归注入和摘要误压缩问题，补充 peer rescue 机制",
        "feat(skills): per-user custom skill isolation with sandbox mounting": "实现用户级自定义 Skill 隔离与沙箱挂载",
    }
    for en, zh in mapping.items():
        if en.lower() in title.lower():
            return zh
    # Fallback: try to extract type prefix
    if title.startswith("fix("):
        return f"修复{title.split('):', 1)[-1].strip() if '):' in title else title}"
    if title.startswith("feat("):
        return f"新增{title.split('):', 1)[-1].strip() if '):' in title else title}"
    return title

# Build table rows
cn_rows = ""
en_rows = ""
for pr in prs:
    num = pr["number"]
    url = pr["html_url"]
    title = pr["title"].strip()
    cn_title = translate(title, pr.get("body", ""))

    cn_rows += f"| [#{num}]({url}) | {cn_title} | ✅ Merged |\n"
    en_rows += f"| [#{num}]({url}) | {title} | ✅ Merged |\n"

today = datetime.utcnow().strftime("%Y-%m-%d")
total = len(prs)

md = f"""<!--START_SECTION:contributions-->
<!-- Auto-generated on {today} by .github/workflows/update-contributions.yml -->
<!-- Total merged PRs: {total} -->

### 已合并的 Pull Requests

| PR | 描述 | 状态 |
|----|------|------|
{cn_rows}
### Merged Pull Requests

| PR | Description | Status |
|----|-------------|--------|
{en_rows}
<!--END_SECTION:contributions-->
"""

# Read current README.md
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

# Replace the contributions section
pattern = r'<!--START_SECTION:contributions-->.*?<!--END_SECTION:contributions-->'
new_readme = re.sub(pattern, md.strip(), readme, flags=re.DOTALL)

if new_readme == readme:
    print("No changes needed")
else:
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)
    print(f"Updated README with {total} merged PRs")
