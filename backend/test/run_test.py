#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InfluAI 评论生成测试运行脚本

快速启动测试的便捷脚本
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入测试模块
from test_comment_generation import main

if __name__ == "__main__":
    print("🚀 启动 InfluAI 评论生成测试...")
    main()
