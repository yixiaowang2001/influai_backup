#!/usr/bin/env python3
"""
InfluAI Backend Server 启动脚本
"""

import uvicorn
from backend.main import app

if __name__ == "__main__":
    print("正在启动 InfluAI Backend Server...")
    print("API文档地址: http://localhost:8000/docs")
    print("健康检查: http://localhost:8000/health")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下启用热重载
        log_level="info"
    ) 