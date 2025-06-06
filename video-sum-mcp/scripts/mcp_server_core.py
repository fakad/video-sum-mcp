"""
MCP服务器核心模块

包含CursorMCPServer核心类和服务器启动逻辑。
"""

import asyncio
import json
import sys
import os
from pathlib import Path
import logging

from .mcp_handlers import MCPHandlers, create_mcp_handlers

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CursorMCPServer:
    """Cursor专用MCP服务器"""
    
    def __init__(self):
        """初始化MCP服务器"""
        self.handlers = create_mcp_handlers()
        self.tools = self._define_tools()
        
    def _define_tools(self):
        """定义所有可用工具"""
        return [
            {
                "name": "process_video",
                "description": "处理视频URL，提取内容进行AI分析",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "视频URL，支持B站、抖音、小红书、知乎等平台"
                        },
                        "output_format": {
                            "type": "string",
                            "description": "输出格式，支持markdown等，默认为markdown",
                            "default": "markdown"
                        },
                        "use_proxy": {
                            "type": "boolean",
                            "description": "是否使用代理，默认为false",
                            "default": False
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "continue_processing", 
                "description": "继续处理视频，将LLM结果保存并生成知识图谱",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "video_id": {
                            "type": "string",
                            "description": "视频唯一标识"
                        },
                        "llm_response": {
                            "type": "string",
                            "description": "LLM响应文本"
                        },
                        "output_format": {
                            "type": "string",
                            "description": "输出格式，默认为markdown",
                            "default": "markdown"
                        }
                    },
                    "required": ["video_id", "llm_response"]
                }
            },
            {
                "name": "list_supported_platforms",
                "description": "列出支持的视频平台",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_supported_formats",
                "description": "列出支持的输出格式",
                "inputSchema": {
                    "type": "object", 
                    "properties": {}
                }
            },
            {
                "name": "configure",
                "description": "配置工具参数",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "LLM API密钥（可选）"
                        },
                        "proxy": {
                            "type": "string",
                            "description": "代理服务器地址（可选）"
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "输出目录（可选）"
                        }
                    }
                }
            },
            {
                "name": "batch_process_videos",
                "description": "批量处理多个视频URL，支持异步并发处理",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要处理的视频URL列表"
                        },
                        "max_concurrent": {
                            "type": "integer",
                            "description": "最大并发数，默认为3",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 10
                        },
                        "use_cache": {
                            "type": "boolean",
                            "description": "是否使用缓存，默认为true",
                            "default": True
                        },
                        "output_format": {
                            "type": "string",
                            "description": "输出格式，默认为markdown",
                            "default": "markdown"
                        },
                        "save_results": {
                            "type": "boolean",
                            "description": "是否保存结果到文件，默认为false",
                            "default": False
                        },
                        "output_file": {
                            "type": "string",
                            "description": "输出文件路径（当save_results为true时使用）"
                        }
                    },
                    "required": ["urls"]
                }
            },
            {
                "name": "get_batch_cache_stats",
                "description": "获取批量处理缓存统计信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cache_dir": {
                            "type": "string",
                            "description": "缓存目录，默认为temp/cache",
                            "default": "temp/cache"
                        }
                    }
                }
            },
            {
                "name": "cleanup_batch_cache",
                "description": "清理批量处理的过期缓存",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cache_dir": {
                            "type": "string",
                            "description": "缓存目录，默认为temp/cache",
                            "default": "temp/cache"
                        },
                        "clear_all": {
                            "type": "boolean",
                            "description": "是否清空所有缓存，默认为false（只清理过期缓存）",
                            "default": False
                        }
                    }
                }
            }
        ]
    
    async def handle_message(self, message):
        """处理MCP消息"""
        try:
            if message.get("method") == "tools/list":
                return {
                    "tools": self.tools
                }
            elif message.get("method") == "tools/call":
                params = message.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = await self.call_tool(tool_name, arguments)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"未知方法: {message.get('method')}"
                    }
                }
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": f"内部错误: {str(e)}"
                }
            }
    
    async def call_tool(self, tool_name, arguments):
        """调用指定工具"""
        try:
            if tool_name == "process_video":
                return await self.handlers.handle_process_video(**arguments)
            
            elif tool_name == "continue_processing":
                return await self.handlers.handle_continue_processing(**arguments)
            
            elif tool_name == "list_supported_platforms":
                return await self.handlers.handle_list_supported_platforms()
            
            elif tool_name == "list_supported_formats":
                return await self.handlers.handle_list_supported_formats()
            
            elif tool_name == "configure":
                return await self.handlers.handle_configure(**arguments)
            
            elif tool_name == "batch_process_videos":
                return await self.handlers.handle_batch_process_videos(**arguments)
            
            elif tool_name == "get_batch_cache_stats":
                return await self.handlers.handle_get_batch_cache_stats(**arguments)
            
            elif tool_name == "cleanup_batch_cache":
                return await self.handlers.handle_cleanup_batch_cache(**arguments)
            
            else:
                return {
                    "success": False,
                    "error": f"未知工具: {tool_name}",
                    "message": f"工具 '{tool_name}' 不存在"
                }
                
        except Exception as e:
            logger.error(f"调用工具 {tool_name} 失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"工具 '{tool_name}' 执行失败"
            }
    
    async def run(self):
        """启动MCP服务器"""
        logger.info("🚀 Video-Sum MCP 服务器启动")
        logger.info(f"支持的工具数量: {len(self.tools)}")
        
        try:
            while True:
                try:
                    # 从标准输入读取JSON-RPC消息
                    line = sys.stdin.readline()
                    if not line:
                        break
                    
                    message = json.loads(line.strip())
                    response = await self.handle_message(message)
                    
                    # 将响应写入标准输出
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {e}")
                    error_response = {
                        "error": {
                            "code": -32700,
                            "message": f"解析错误: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
                except Exception as e:
                    logger.error(f"处理请求时发生错误: {e}")
                    error_response = {
                        "error": {
                            "code": -32603,
                            "message": f"内部错误: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
        except KeyboardInterrupt:
            logger.info("服务器收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"服务器运行时发生致命错误: {e}")
        finally:
            logger.info("Video-Sum MCP 服务器已关闭")


def create_mcp_server() -> CursorMCPServer:
    """创建MCP服务器实例"""
    return CursorMCPServer()


async def start_server():
    """启动MCP服务器"""
    server = create_mcp_server()
    await server.run()


