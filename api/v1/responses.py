"""
博通 (Botong) — 统一 API 响应格式
所有 API 端点使用此工具类返回标准化响应
"""

from typing import Any, Optional, Dict, List
from flask import jsonify


class ApiResponse:
    """统一 API 响应"""
    
    @staticmethod
    def success(data: Any = None, message: str = None, meta: Optional[Dict] = None):
        """成功响应 (200)"""
        body = {"code": 200, "success": True}
        if data is not None:
            body["data"] = data
        if message:
            body["message"] = message
        if meta:
            body["meta"] = meta
        return jsonify(body), 200
    
    @staticmethod
    def created(data: Any = None, message: str = "创建成功"):
        """创建成功 (201)"""
        body = {"code": 201, "success": True, "message": message}
        if data is not None:
            body["data"] = data
        return jsonify(body), 201
    
    @staticmethod
    def no_content():
        """无内容 (204)"""
        return "", 204
    
    @staticmethod
    def error(message: str, code: int = 400, details: Any = None):
        """错误响应"""
        body = {"code": code, "success": False, "error": message}
        if details:
            body["details"] = details
        return jsonify(body), code
    
    @staticmethod
    def not_found(message: str = "资源不存在"):
        """404"""
        return ApiResponse.error(message, 404)
    
    @staticmethod
    def bad_request(message: str = "请求参数错误", details: Any = None):
        """400"""
        return ApiResponse.error(message, 400, details)
    
    @staticmethod
    def unauthorized(message: str = "未授权"):
        """401"""
        return ApiResponse.error(message, 401)
    
    @staticmethod
    def forbidden(message: str = "无权访问"):
        """403"""
        return ApiResponse.error(message, 403)
    
    @staticmethod
    def server_error(message: str = "服务器内部错误"):
        """500"""
        return ApiResponse.error(message, 500)
    
    @staticmethod
    def paginated(items: list, total: int, page: int, per_page: int):
        """分页响应"""
        return jsonify({
            "code": 200,
            "success": True,
            "data": items,
            "meta": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": max(1, (total + per_page - 1) // per_page),
            }
        }), 200
    
    @staticmethod
    def list_response(items: list, total: Optional[int] = None):
        """列表响应"""
        body = {"code": 200, "success": True, "data": items}
        if total is not None:
            body["total"] = total
        return jsonify(body), 200
