#!/bin/bash
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/.qoder/repowiki"
DST="$REPO_ROOT/.trae/repowiki"

if [ ! -d "$SRC" ]; then
  echo "❌ 源目录不存在: $SRC"
  echo "   请先在 Trae 中打开项目以生成 RepoWiki"
  exit 1
fi

SRC_COUNT=$(find "$SRC" -type f | wc -l | tr -d ' ')
if [ "$SRC_COUNT" -eq 0 ]; then
  echo "❌ 源目录为空，无内容可同步"
  exit 1
fi

rm -rf "$DST"
cp -R "$SRC" "$DST"

DST_COUNT=$(find "$DST" -type f | wc -l | tr -d ' ')

if [ "$SRC_COUNT" -eq "$DST_COUNT" ]; then
  echo "✅ RepoWiki 同步完成: $SRC_COUNT 个文件"
  echo "   源: $SRC"
  echo "   目标: $DST"
else
  echo "⚠️  文件数量不一致: 源 $SRC_COUNT, 目标 $DST_COUNT"
  exit 1
fi
