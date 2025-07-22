#!/bin/bash

# 设置环境变量
export DATABASE_URL="sqlite:///./test.db"
export OPENAI_API_KEY="${OPENAI_API_KEY:-test_key}"
export BEEHIIV_API_KEY="test_key"
export BEEHIIV_PUBLICATION_ID="test_id"
export REDIS_URL="redis://localhost:6379"
export FRONTEND_URL="http://localhost:3000"

# 激活虚拟环境
source test_env/bin/activate

# 启动服务器
echo "🚀 启动Podcast API服务器..."
echo "📡 访问地址: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000