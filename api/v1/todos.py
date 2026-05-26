"""
博通 — 待办 API v1
"""

import logging
from flask import Blueprint, request, jsonify

from api.v1.responses import ApiResponse
from infrastructure.di.service_injection import inject_service

logger = logging.getLogger(__name__)

bp_todos = Blueprint('api_v1_todos', __name__, url_prefix='/api/v1/todos')

@bp_todos.route("/", strict_slashes=False)
def list_todos():
    """待办列表"""
    try:
        svc = inject_service("todo_service")
        result = svc.list(
            category=request.args.get("category", ""),
            done=request.args.get("done", type=int),
            date_filter=request.args.get("date", ""),
            keyword=request.args.get("q", ""),
            page=request.args.get("page", 1, type=int),
            per_page=request.args.get("per_page", 50, type=int),
            source_type=request.args.get("source_type", ""),
            source_id=request.args.get("source_id", type=int),
            parent_only=request.args.get("parent_only", type=bool) or False,
        )
        return ApiResponse.list_response(
            items=result.get("todos", []),
            total=result.get("total", 0))
    except Exception as e:
        logger.error(f"list_todos error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/stats")
def todo_stats():
    """待办统计"""
    try:
        svc = inject_service("todo_service")
        stats = svc.stats()
        return ApiResponse.success(stats)
    except Exception as e:
        logger.error(f"todo_stats error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/", methods=["POST"], strict_slashes=False)
def create_todo():
    """创建待办"""
    try:
        svc = inject_service("todo_service")
        data = request.get_json(force=True, silent=True) or {}
        title = data.get("title", "").strip()
        if not title:
            return ApiResponse.bad_request("待办标题不能为空")
        todo = svc.create(
            title=title,
            category=data.get("category", "work"),
            priority=data.get("priority", "M"),
            due_date=data.get("due_date", ""),
            due_time=data.get("due_time", ""),
            description=data.get("description", ""),
            tags=data.get("tags", ""),
            remind=data.get("remind", False),
            source_type=data.get("source_type", ""),
            source_id=data.get("source_id"),
            parent_id=data.get("parent_id"),
            repeat_rule=data.get("repeat_rule", ""),
            estimated_minutes=data.get("estimated_minutes"),
        )
        return ApiResponse.created(todo, message="待办已创建")
    except ValueError as e:
        return ApiResponse.bad_request(str(e))
    except Exception as e:
        logger.error(f"create_todo error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/<int:todo_id>")
def get_todo(todo_id: int):
    """获取待办"""
    try:
        svc = inject_service("todo_service")
        todo = svc.get(todo_id)
        if not todo:
            return ApiResponse.not_found("待办不存在")
        return ApiResponse.success(todo)
    except Exception as e:
        logger.error(f"get_todo error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id: int):
    """更新待办"""
    try:
        svc = inject_service("todo_service")
        data = request.get_json(force=True, silent=True) or {}
        todo = svc.update(todo_id, **data)
        return ApiResponse.success(todo, message="已更新")
    except Exception as e:
        logger.error(f"update_todo error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/<int:todo_id>/toggle", methods=["PUT"])
def toggle_todo(todo_id: int):
    """切换完成状态"""
    try:
        svc = inject_service("todo_service")
        todo = svc.toggle(todo_id)
        if not todo:
            return ApiResponse.not_found("待办不存在")
        return ApiResponse.success(todo,
                                   message="已完成" if todo.get("done") else "已重开")
    except Exception as e:
        logger.error(f"toggle_todo error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id: int):
    """删除待办"""
    try:
        svc = inject_service("todo_service")
        svc.delete(todo_id)
        return ApiResponse.success(message="已删除")
    except Exception as e:
        logger.error(f"delete_todo error: {e}", exc_info=True)
        return ApiResponse.server_error()


# ───── 子任务 ─────

@bp_todos.route("/<int:parent_id>/subtasks", strict_slashes=False)
def list_subtasks(parent_id: int):
    """获取子任务列表"""
    try:
        svc = inject_service("todo_service")
        parent = svc.get(parent_id)
        if not parent:
            return ApiResponse.not_found("父任务不存在")
        return ApiResponse.success({
            "subtasks": parent.get("subtasks", []),
            "progress": parent.get("progress", {}),
        })
    except Exception as e:
        logger.error(f"list_subtasks error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/<int:parent_id>/subtasks", methods=["POST"], strict_slashes=False)
def create_subtask(parent_id: int):
    """创建子任务"""
    try:
        svc = inject_service("todo_service")
        data = request.get_json(force=True, silent=True) or {}
        title = data.get("title", "").strip()
        if not title:
            return ApiResponse.bad_request("子任务标题不能为空")
        subtask = svc.create_subtask(
            parent_id=parent_id,
            title=title,
            priority=data.get("priority", "M"),
            due_date=data.get("due_date", ""),
            description=data.get("description", ""),
            tags=data.get("tags", ""),
        )
        if not subtask:
            return ApiResponse.server_error("创建失败")
        return ApiResponse.created(subtask, message="子任务已创建")
    except ValueError as e:
        return ApiResponse.bad_request(str(e))
    except Exception as e:
        logger.error(f"create_subtask error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/subtasks/<int:subtask_id>/toggle", methods=["PUT"])
def toggle_subtask(subtask_id: int):
    """切换子任务完成状态"""
    try:
        svc = inject_service("todo_service")
        result = svc.toggle_subtask(subtask_id)
        if not result:
            return ApiResponse.not_found("子任务不存在")
        return ApiResponse.success(result, message="子任务状态已切换")
    except Exception as e:
        logger.error(f"toggle_subtask error: {e}", exc_info=True)
        return ApiResponse.server_error()


# ───── 批量操作 ─────

@bp_todos.route("/batch", methods=["PUT"])
def batch_todos():
    """批量操作（完成/删除）"""
    try:
        svc = inject_service("todo_service")
        data = request.get_json(force=True, silent=True) or {}
        action = data.get("action", "")
        ids = data.get("ids", [])
        if not ids:
            return ApiResponse.bad_request("请提供待办ID列表")

        if action == "done":
            result = svc.batch_toggle(ids, done=1)
        elif action == "undone":
            result = svc.batch_toggle(ids, done=0)
        elif action == "delete":
            result = svc.batch_delete(ids)
        else:
            return ApiResponse.bad_request("不支持的操作")

        return ApiResponse.success(result, message="批量操作完成")
    except Exception as e:
        logger.error(f"batch_todos error: {e}", exc_info=True)
        return ApiResponse.server_error()


# ───── 清理已完成 ─────

@bp_todos.route("/cleanup", methods=["POST"])
def cleanup_todos():
    """清理已完成超过N天的待办"""
    try:
        svc = inject_service("todo_service")
        data = request.get_json(force=True, silent=True) or {}
        days = int(data.get("days", 30))
        days = max(7, min(days, 365))
        svc.cleanup_done(days)
        return ApiResponse.success(message=f"已清理 {days} 天前完成的待办")
    except Exception as e:
        logger.error(f"cleanup_todos error: {e}", exc_info=True)
        return ApiResponse.server_error()


# ───── 日期快捷筛选 ─────

@bp_todos.route("/today")
def todo_today():
    """今日到期待办"""
    try:
        svc = inject_service("todo_service")
        result = svc.list(date_filter="today", parent_only=True)
        result["filter"] = "today"
        return jsonify(result)
    except Exception as e:
        logger.error(f"todo_today error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/overdue")
def todo_overdue():
    """已过期待办"""
    try:
        svc = inject_service("todo_service")
        result = svc.list(date_filter="overdue", parent_only=True)
        result["filter"] = "overdue"
        return jsonify(result)
    except Exception as e:
        logger.error(f"todo_overdue error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/upcoming")
def todo_upcoming():
    """近7天待办"""
    try:
        svc = inject_service("todo_service")
        result = svc.list(date_filter="upcoming", parent_only=True)
        result["filter"] = "upcoming"
        return jsonify(result)
    except Exception as e:
        logger.error(f"todo_upcoming error: {e}", exc_info=True)
        return ApiResponse.server_error()


# ───── 关联查询 ─────

@bp_todos.route("/by-ticket/<int:ticket_id>")
def todo_by_ticket(ticket_id: int):
    """获取工单关联的待办"""
    try:
        svc = inject_service("todo_service")
        result = svc.list(source_type="ticket", source_id=ticket_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"todo_by_ticket error: {e}", exc_info=True)
        return ApiResponse.server_error()


@bp_todos.route("/by-source")
def todo_by_source():
    """按关联类型查询待办"""
    try:
        svc = inject_service("todo_service")
        source_type = request.args.get("type", "")
        source_id = request.args.get("id")
        if not source_type:
            return ApiResponse.bad_request("请指定 type 参数")
        result = svc.list(
            source_type=source_type,
            source_id=int(source_id) if source_id else None,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"todo_by_source error: {e}", exc_info=True)
        return ApiResponse.server_error()


def register_blueprint(app):
    """注册 Blueprint"""
    app.register_blueprint(bp_todos)
    logger.info("API v1 待办完整端点已注册")
