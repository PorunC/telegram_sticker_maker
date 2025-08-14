#!/usr/bin/env python3
"""
兼容性入口点 - start_web.py

保持原有的启动方式，重定向到新的模块化结构。
"""

import sys
from pathlib import Path

# 确保可以导入web模块
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入并运行Web应用
from web.app import main

if __name__ == '__main__':
    main()