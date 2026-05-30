#!/usr/bin/env python3
"""
批量将 .qoder/skills 下的技能注册到 MCP（HTTP API）。
用法：
  export MCP_API_URL=http://localhost:8080
  export MCP_API_KEY=your_key
  python3 scripts/register_mcp_skills.py
"""
import os
import glob
import json
import requests

MCP_URL = os.environ.get("MCP_API_URL", "http://localhost:8080")
API_KEY = os.environ.get("MCP_API_KEY", "")
HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}

def load_skill(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # 简单从 frontmatter 读取 title
    name = os.path.splitext(os.path.basename(md_path))[0]
    desc = ""
    for line in text.splitlines():
        if line.strip().startswith('## 简介'):
            desc = '\n'.join(text.splitlines()[text.splitlines().index(line)+1:text.splitlines().index(line)+5]).strip()
            break
    return {
        "name": name,
        "description": desc or name,
        "entrypoint": f"file://{md_path}"
    }

def register(skill):
    url = MCP_URL.rstrip('/') + '/api/v1/skills/register'
    resp = requests.post(url, json=skill, headers={**HEADERS, 'Content-Type': 'application/json'})
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

def main():
    skills = glob.glob('.qoder/skills/*.md')
    if not skills:
        print('未找到技能文件于 .qoder/skills/')
        return
    for s in skills:
        skill = load_skill(s)
        code, body = register(skill)
        print(f"注册 {skill['name']}: {code} -> {body}")

if __name__ == '__main__':
    main()
