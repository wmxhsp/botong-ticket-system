#!/usr/bin/env node
/**
 * SearXNG MCP Server
 * 为博通工单系统提供搜索能力的 MCP 服务器
 * 使用标准输入输出 (stdio) 与 MCP 客户端通信
 */

const SEARXNG_URL = process.env.SEARXNG_URL || 'http://localhost:8080';

// 简单的 MCP 服务器实现，不依赖外部 SDK
class SearXNGMcpServer {
  constructor() {
    this.tools = [
      {
        name: 'searxng_search',
        description: '使用 SearXNG 进行网络搜索，支持中文和多种搜索引擎',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: '搜索关键词',
            },
            category: {
              type: 'string',
              description: '搜索类别',
              enum: ['general', 'images', 'videos', 'news', 'it', 'science'],
              default: 'general',
            },
            language: {
              type: 'string',
              description: '搜索语言',
              enum: ['zh-CN', 'zh-TW', 'en', 'ja', 'ko'],
              default: 'zh-CN',
            },
            time_range: {
              type: 'string',
              description: '时间范围',
              enum: ['day', 'week', 'month', 'year'],
            },
            page: {
              type: 'number',
              description: '页码',
              default: 1,
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'searxng_image_search',
        description: '使用 SearXNG 进行图片搜索',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: '搜索关键词',
            },
            language: {
              type: 'string',
              description: '搜索语言',
              default: 'zh-CN',
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'searxng_news_search',
        description: '使用 SearXNG 进行新闻搜索',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: '搜索关键词',
            },
            time_range: {
              type: 'string',
              description: '时间范围',
              enum: ['day', 'week', 'month'],
              default: 'week',
            },
          },
          required: ['query'],
        },
      },
    ];
  }

  // 发送 MCP 响应
  sendResponse(id, result) {
    const response = {
      jsonrpc: '2.0',
      id,
      result,
    };
    console.log(JSON.stringify(response));
  }

  // 发送 MCP 错误响应
  sendError(id, code, message) {
    const response = {
      jsonrpc: '2.0',
      id,
      error: {
        code,
        message,
      },
    };
    console.log(JSON.stringify(response));
  }

  // 处理初始化请求
  handleInitialize(id) {
    this.sendResponse(id, {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: {},
      },
      serverInfo: {
        name: 'searxng-search',
        version: '1.0.0',
      },
    });
  }

  // 处理工具列表请求
  handleListTools(id) {
    this.sendResponse(id, {
      tools: this.tools,
    });
  }

  // 处理工具调用
  async handleCallTool(id, name, args) {
    try {
      let result;
      switch (name) {
        case 'searxng_search':
          result = await this.search(args);
          break;
        case 'searxng_image_search':
          result = await this.imageSearch(args);
          break;
        case 'searxng_news_search':
          result = await this.newsSearch(args);
          break;
        default:
          throw new Error(`未知工具: ${name}`);
      }
      this.sendResponse(id, result);
    } catch (error) {
      this.sendResponse(id, {
        content: [
          {
            type: 'text',
            text: `搜索错误: ${error.message}`,
          },
        ],
        isError: true,
      });
    }
  }

  async search(args) {
    const { query, category = 'general', language = 'zh-CN', time_range, page = 1 } = args;
    
    const params = new URLSearchParams({
      q: query,
      format: 'json',
      language: language,
      pageno: page.toString(),
    });

    if (category && category !== 'general') {
      params.append('categories', category);
    }

    if (time_range) {
      params.append('time_range', time_range);
    }

    const url = `${SEARXNG_URL}/search?${params.toString()}`;
    
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`SearXNG 请求失败: ${response.status}`);
    }

    const data = await response.json();
    
    const results = data.results || [];
    const formattedResults = results.slice(0, 10).map((result, index) => ({
      index: index + 1,
      title: result.title,
      url: result.url,
      content: result.content,
      engine: result.engine,
    }));

    const output = {
      query: query,
      total_results: data.number_of_results || results.length,
      results: formattedResults,
      engines: data.engines || [],
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(output, null, 2),
        },
      ],
    };
  }

  async imageSearch(args) {
    const { query, language = 'zh-CN' } = args;
    
    const params = new URLSearchParams({
      q: query,
      format: 'json',
      language: language,
      categories: 'images',
    });

    const url = `${SEARXNG_URL}/search?${params.toString()}`;
    
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`SearXNG 图片搜索请求失败: ${response.status}`);
    }

    const data = await response.json();
    
    const results = data.results || [];
    const formattedResults = results.slice(0, 10).map((result, index) => ({
      index: index + 1,
      title: result.title,
      url: result.url,
      thumbnail: result.thumbnail,
      img_src: result.img_src,
      engine: result.engine,
    }));

    const output = {
      query: query,
      total_results: results.length,
      results: formattedResults,
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(output, null, 2),
        },
      ],
    };
  }

  async newsSearch(args) {
    const { query, time_range = 'week' } = args;
    
    const params = new URLSearchParams({
      q: query,
      format: 'json',
      categories: 'news',
      time_range: time_range,
    });

    const url = `${SEARXNG_URL}/search?${params.toString()}`;
    
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`SearXNG 新闻搜索请求失败: ${response.status}`);
    }

    const data = await response.json();
    
    const results = data.results || [];
    const formattedResults = results.slice(0, 10).map((result, index) => ({
      index: index + 1,
      title: result.title,
      url: result.url,
      content: result.content,
      publishedDate: result.publishedDate,
      engine: result.engine,
    }));

    const output = {
      query: query,
      total_results: results.length,
      time_range: time_range,
      results: formattedResults,
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(output, null, 2),
        },
      ],
    };
  }

  // 处理输入行
  async processLine(line) {
    try {
      const message = JSON.parse(line);
      const { id, method, params } = message;

      switch (method) {
        case 'initialize':
          this.handleInitialize(id);
          break;
        case 'tools/list':
          this.handleListTools(id);
          break;
        case 'tools/call':
          await this.handleCallTool(id, params.name, params.arguments);
          break;
        default:
          this.sendError(id, -32601, `未知方法: ${method}`);
      }
    } catch (error) {
      console.error('处理消息时出错:', error);
    }
  }

  // 启动服务器
  run() {
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: false,
    });

    rl.on('line', (line) => {
      this.processLine(line);
    });

    console.error('SearXNG MCP Server running on stdio');
  }
}

// 启动服务器
const server = new SearXNGMcpServer();
server.run();