#!/bin/bash
# xAgent 本地部署更新脚本
# 在服务器上执行：停止服务 → 重新构建镜像 → 启动服务

set -e

echo "=========================================="
echo "  xAgent 部署更新"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}[1/4] 停止现有服务...${NC}"
docker-compose down || true

echo -e "${GREEN}[2/4] 构建后端镜像...${NC}"
docker build -t xagent-backend ./backend

echo -e "${GREEN}[3/4] 构建前端镜像...${NC}"
docker build -t xagent-frontend ./frontend

echo -e "${GREEN}[4/4] 启动服务...${NC}"
docker-compose up -d

echo ""
sleep 3
echo -e "${GREEN}服务状态:${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}=========================================="
echo "  部署完成！"
echo "==========================================${NC}"
echo ""
echo "查看日志: docker-compose logs -f"
