#!/bin/bash
# ==========================================================
# 博通 (Botong) — RQ Worker 启动脚本
# ==========================================================
# 
# 生产环境使用，启动 RQ Worker 和调度器。
# 确保 Redis 已运行且 REDIS_URL 已配置。
#
# 用法:
#   ./scripts/start_workers.sh              # 前台运行
#   nohup ./scripts/start_workers.sh &       # 后台运行
#
# 环境变量:
#   REDIS_URL       Redis 连接地址（默认 redis://localhost:6379/0）
#   WORKER_COUNT    Worker 进程数（默认 2）
#   QUEUE_NAME      队列名（默认 botong-tasks）
# ==========================================================

set -euo pipefail

REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
WORKER_COUNT="${WORKER_COUNT:-2}"
QUEUE_NAME="${QUEUE_NAME:-botong-tasks}"

echo "=========================================="
echo "  Botong RQ Worker 启动"
echo "=========================================="
echo "  Redis:     ${REDIS_URL}"
echo "  Workers:   ${WORKER_COUNT}"
echo "  Queue:     ${QUEUE_NAME}"
echo "=========================================="

# 检查 Redis 连通性
if ! redis-cli -u "${REDIS_URL}" ping &>/dev/null; then
    echo "❌ Redis 不可达！请检查 REDIS_URL: ${REDIS_URL}"
    echo "   如果使用 LocalTaskQueue 回退方案，无需启动此脚本。"
    exit 1
fi
echo "✅ Redis 连接正常"

# 启动 RQ Worker
echo "🚀 启动 RQ Worker (${WORKER_COUNT} 进程)..."
rq worker \
    --url "${REDIS_URL}" \
    --name "botong-worker" \
    --num-workers "${WORKER_COUNT}" \
    "${QUEUE_NAME}" &

RQ_PID=$!
echo "   Worker PID: ${RQ_PID}"

# 启动 RQ Scheduler
echo "🚀 启动 RQ Scheduler..."
rqscheduler \
    --url "${REDIS_URL}" \
    --queue "${QUEUE_NAME}" &

SCHED_PID=$!
echo "   Scheduler PID: ${SCHED_PID}"

# 注册清理
cleanup() {
    echo ""
    echo "⏹  正在停止 Worker..."
    kill ${RQ_PID} 2>/dev/null || true
    kill ${SCHED_PID} 2>/dev/null || true
    wait ${RQ_PID} ${SCHED_PID} 2>/dev/null || true
    echo "✅  Worker 已停止"
}
trap cleanup EXIT INT TERM

echo ""
echo "✅ 后台任务系统运行中（按 Ctrl+C 停止）"
echo ""

# 等待任一子进程退出
wait -n ${RQ_PID} ${SCHED_PID} 2>/dev/null || true
