"""
博通 (Botong) — 验证器

提供 Flask 视图函数的 Pydantic 校验装饰器:
  - @validate_json(schema)   — 校验 JSON body
  - @validate_query(schema)  — 校验 URL 查询参数

用法:
    from api.validators import validate_json, validate_query
    from api.validators.schemas import TicketCreateSchema

    @bp.route("/", methods=["POST"])
    @validate_json(TicketCreateSchema)
    def create_ticket(body: TicketCreateSchema):
        # body 是已验证的 Pydantic 模型实例
        return jsonify(body.model_dump())
"""

import functools
import logging
from typing import Type, Optional, Union, get_type_hints

from flask import request, jsonify
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


def _format_errors(exc: ValidationError) -> dict:
    """将 Pydantic ValidationError 格式化为人类可读的错误字典"""
    errors = {}
    for error in exc.errors():
        loc = ".".join(str(l) for l in error["loc"])
        msg = error["msg"]
        errors[loc] = msg
    return errors


def validate_json(schema: Type[BaseModel]):
    """
    校验 Flask request.get_json() 的 JSON body。

    装饰后的视图函数额外接收 `body` 参数（经验证的 Pydantic 模型实例）。
    如果校验失败，返回 400 和结构化的错误信息。
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json(silent=True) or {}
                body = schema.model_validate(data)
            except ValidationError as e:
                return jsonify({
                    "error": "请求参数校验失败",
                    "details": _format_errors(e),
                }), 400
            except Exception as e:
                logger.error("validate_json error: %s", e)
                return jsonify({"error": "请求体解析失败"}), 400

            return func(*args, body=body, **kwargs)

        return wrapper

    return decorator


def validate_query(schema: Type[BaseModel]):
    """
    校验 Flask request.args 的查询参数。

    装饰后的视图函数额外接收 `query` 参数（经验证的 Pydantic 模型实例）。
    如果校验失败，返回 400 和结构化的错误信息。
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = dict(request.args)
                query = schema.model_validate(data)
            except ValidationError as e:
                return jsonify({
                    "error": "查询参数校验失败",
                    "details": _format_errors(e),
                }), 400
            except Exception as e:
                logger.error("validate_query error: %s", e)
                return jsonify({"error": "查询参数解析失败"}), 400

            return func(*args, query=query, **kwargs)

        return wrapper

    return decorator