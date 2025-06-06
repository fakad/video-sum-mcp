#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
video-sum-mcp Cursor专用MCP服务器 - 兼容性桥接文件

此文件保持向后兼容性，所有功能已重构为模块化组件。
新的组件包括：
- mcp_handlers.py: MCP请求处理器和工具方法实现
- mcp_server_core.py: MCP服务器核心类和启动逻辑
"""

import asyncio
import sys
import os
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 切换工作目录到项目根目录
os.chdir(project_root)

from scripts.mcp_handlers import MCPHandlers, create_mcp_handlers
from scripts.mcp_server_core import CursorMCPServer, create_mcp_server, start_server

# 为了向后兼容，导入所有主要组件
__all__ = [
    'MCPHandlers',
    'CursorMCPServer',
    'create_mcp_handlers', 
    'create_mcp_server',
    'start_server'
]


async def main():
    """主入口函数"""
    await start_server()


if __name__ == "__main__":
    asyncio.run(main()) 