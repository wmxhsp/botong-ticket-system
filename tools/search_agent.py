#!/usr/bin/env python3
"""
轻量级搜索代理 - 替代 SearXNG
支持百度搜索、必应搜索等国内搜索引擎
无需 Docker，直接 Python 运行
"""

import asyncio
import json
import re
import urllib.parse
import urllib.request
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str


class SearchAgent:
    """搜索代理 - 聚合多个搜索引擎"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    async def search_baidu(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """百度搜索"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.baidu.com/s?wd={encoded_query}&rn={num_results}"

            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')

            results = []
            # 解析百度搜索结果
            pattern = r'<div class="result"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?<span class="content-right_8Zs40"[^>]*>(.*?)</span>.*?</div>'
            matches = re.findall(pattern, html, re.DOTALL)

            for match in matches[:num_results]:
                url, title, snippet = match
                # 清理 HTML 标签
                title = re.sub(r'<[^>]+>', '', title).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()

                if title and url:
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source='baidu'
                    ))

            return results
        except Exception as e:
            print(f"百度搜索失败: {e}")
            return []

    async def search_bing(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """必应搜索"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.bing.com/search?q={encoded_query}&count={num_results}"

            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')

            results = []
            # 解析必应搜索结果
            pattern = r'<li class="b_algo"[^>]*>.*?<h2><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h2>.*?<p>(.*?)</p>.*?</li>'
            matches = re.findall(pattern, html, re.DOTALL)

            for match in matches[:num_results]:
                url, title, snippet = match
                title = re.sub(r'<[^>]+>', '', title).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()

                if title and url:
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source='bing'
                    ))

            return results
        except Exception as e:
            print(f"必应搜索失败: {e}")
            return []

    async def search(self, query: str, engines: List[str] = None, num_results: int = 5) -> Dict:
        """
        聚合搜索
        :param query: 搜索关键词
        :param engines: 搜索引擎列表 ['baidu', 'bing']
        :param num_results: 每个引擎返回结果数
        :return: 搜索结果字典
        """
        if engines is None:
            engines = ['baidu', 'bing']

        all_results = []
        tasks = []

        if 'baidu' in engines:
            tasks.append(self.search_baidu(query, num_results))
        if 'bing' in engines:
            tasks.append(self.search_bing(query, num_results))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        for results in results_list:
            if isinstance(results, list):
                all_results.extend(results)

        # 去重（按 URL）
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return {
            'query': query,
            'engines': engines,
            'total_results': len(unique_results),
            'results': [asdict(r) for r in unique_results[:num_results * len(engines)]]
        }


class SearchHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器 - 提供搜索 API"""

    def __init__(self, search_agent: SearchAgent, *args, **kwargs):
        self.search_agent = search_agent
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理 GET 请求"""
        if self.path.startswith('/search'):
            self.handle_search()
        elif self.path == '/health':
            self.handle_health()
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/search':
            self.handle_search_post()
        else:
            self.send_error(404, 'Not Found')

    def handle_search(self):
        """处理搜索 GET 请求"""
        try:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            query = params.get('q', [''])[0]
            engines = params.get('engines', ['baidu,bing'])[0].split(',')
            num_results = int(params.get('num', ['5'])[0])

            if not query:
                self.send_error(400, 'Missing query parameter "q"')
                return

            result = asyncio.run(self.search_agent.search(query, engines, num_results))

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_error(500, str(e))

    def handle_search_post(self):
        """处理搜索 POST 请求"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            query = data.get('q', '')
            engines = data.get('engines', ['baidu', 'bing'])
            num_results = data.get('num', 5)

            if not query:
                self.send_error(400, 'Missing query parameter "q"')
                return

            result = asyncio.run(self.search_agent.search(query, engines, num_results))

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_error(500, str(e))

    def handle_health(self):
        """健康检查"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())

    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[SearchAgent] {args[0]}")


def create_handler(search_agent):
    """创建处理器工厂"""
    def handler(*args, **kwargs):
        return SearchHandler(search_agent, *args, **kwargs)
    return handler