"""
MCP请求处理器模块

包含所有MCP工具方法的具体实现逻辑。
"""

import asyncio
import json
import sys
import os
from pathlib import Path
import logging

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from main import (
        process_video, 
        continue_processing, 
        list_supported_platforms, 
        list_supported_formats, 
        configure
    )
    # 导入批量处理相关模块
    from tools.async_batch_processor import AsyncBatchProcessor, BatchProcessingResult
    from core.extractors.video_extractor import VideoExtractor
    from core.managers.cache_manager import get_cache_manager
except ImportError as e:
    print(f"导入错误: {e}", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)


class MCPHandlers:
    """MCP请求处理器类"""
    
    def __init__(self):
        """初始化处理器"""
        pass
    
    async def handle_process_video(self, url: str, output_format: str = "markdown", use_proxy: bool = False):
        """
        处理视频URL工具
        
        参数:
            url: 视频URL
            output_format: 输出格式
            use_proxy: 是否使用代理
        """
        try:
            logger.info(f"处理视频: {url}")
            
            # 调用同步的process_video函数
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, process_video, url)
            
            if result:
                return {
                    "success": True,
                    "result": result,
                    "message": f"视频处理成功: {url}"
                }
            else:
                return {
                    "success": False,
                    "error": "处理失败，未返回有效结果",
                    "message": f"视频处理失败: {url}"
                }
                
        except Exception as e:
            logger.error(f"处理视频失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"视频处理出错: {url}"
            }
    
    async def handle_continue_processing(self, video_id: str, llm_response: str, output_format: str = "markdown"):
        """
        继续处理视频工具
        
        参数:
            video_id: 视频ID
            llm_response: LLM响应
            output_format: 输出格式
        """
        try:
            logger.info(f"继续处理视频: {video_id}")
            
            # 调用同步的continue_processing函数
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, continue_processing, video_id, llm_response)
            
            if result:
                return {
                    "success": True,
                    "result": result,
                    "message": f"视频继续处理成功: {video_id}"
                }
            else:
                return {
                    "success": False,
                    "error": "继续处理失败",
                    "message": f"视频继续处理失败: {video_id}"
                }
                
        except Exception as e:
            logger.error(f"继续处理视频失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"视频继续处理出错: {video_id}"
            }
    
    async def handle_list_supported_platforms(self):
        """列出支持的平台工具"""
        try:
            platforms = list_supported_platforms()
            return {
                "success": True,
                "platforms": platforms,
                "message": "成功获取支持的平台列表"
            }
        except Exception as e:
            logger.error(f"获取平台列表失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "获取平台列表失败"
            }
    
    async def handle_list_supported_formats(self):
        """列出支持的格式工具"""
        try:
            formats = list_supported_formats()
            return {
                "success": True,
                "formats": formats,
                "message": "成功获取支持的格式列表"
            }
        except Exception as e:
            logger.error(f"获取格式列表失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "获取格式列表失败"
            }
    
    async def handle_configure(self, api_key: str = None, proxy: str = None, output_dir: str = None):
        """配置工具"""
        try:
            config_params = {}
            if api_key:
                config_params['api_key'] = api_key
            if proxy:
                config_params['proxy'] = proxy
            if output_dir:
                config_params['output_dir'] = output_dir
            
            # 调用同步的configure函数
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, configure, config_params)
            
            return {
                "success": True,
                "config": config_params,
                "message": "配置更新成功"
            }
        except Exception as e:
            logger.error(f"配置更新失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "配置更新失败"
            }
    
    async def handle_batch_process_videos(self, urls, max_concurrent=3, use_cache=True, 
                                        output_format="markdown", save_results=False, output_file=None):
        """
        批量处理视频工具
        
        参数:
            urls: URL列表
            max_concurrent: 最大并发数
            use_cache: 是否使用缓存
            output_format: 输出格式
            save_results: 是否保存结果
            output_file: 输出文件路径
        """
        try:
            logger.info(f"开始批量处理 {len(urls)} 个视频")
            
            # 创建批量处理器
            processor = AsyncBatchProcessor(
                max_concurrent=max_concurrent,
                use_cache=use_cache,
                cache_config={'cache_dir': 'temp/cache'},
                progress_config={'type': 'console', 'show_details': False}
            )
            
            # 定义异步处理函数
            async def process_video_async(url, **kwargs):
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, process_video, url)
                    
                    if result:
                        return {
                            "url": url,
                            "status": "success",
                            "title": result.get("title", ""),
                            "summary": result.get("summary", ""),
                            "knowledge_graph": result.get("knowledge_graph", {}),
                            "metadata": result.get("metadata", {})
                        }
                    else:
                        return {
                            "url": url,
                            "status": "error",
                            "error": "处理失败：未返回有效结果"
                        }
                except Exception as e:
                    return {
                        "url": url,
                        "status": "error", 
                        "error": str(e)
                    }
            
            # 执行批量处理
            result = await processor.process_urls(
                urls, 
                process_video_async, 
                f"批量处理 {len(urls)} 个视频"
            )
            
            # 准备返回结果
            response_data = {
                "success": True,
                "total_urls": result.total_urls,
                "successful_urls": result.successful_urls,
                "failed_urls": result.failed_urls,
                "cached_urls": result.cached_urls,
                "success_rate": result.success_rate,
                "elapsed_time": result.elapsed_time,
                "results": result.results,
                "message": f"批量处理完成，成功率: {result.success_rate:.1f}%"
            }
            
            # 如果需要保存结果
            if save_results and output_file:
                try:
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 保存为JSON格式
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
                    
                    response_data["saved_to"] = str(output_path)
                    response_data["message"] += f"，结果已保存到: {output_path}"
                    
                except Exception as save_error:
                    logger.error(f"保存结果失败: {save_error}")
                    response_data["save_error"] = str(save_error)
            
            return response_data
            
        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"批量处理失败: {str(e)}"
            }
    
    async def handle_get_batch_cache_stats(self, cache_dir="temp/cache"):
        """获取批量处理缓存统计"""
        try:
            cache_manager = get_cache_manager()
            stats = await cache_manager.get_stats()
            
            return {
                "success": True,
                "cache_stats": stats,
                "message": "成功获取缓存统计信息"
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "获取缓存统计失败"
            }
    
    async def handle_cleanup_batch_cache(self, cache_dir="temp/cache", clear_all=False):
        """清理批量处理缓存"""
        try:
            cache_manager = get_cache_manager()
            
            if clear_all:
                cleaned_count = await cache_manager.clear_all()
                message = f"清空了 {cleaned_count} 个缓存文件"
            else:
                cleaned_count = await cache_manager.cleanup_expired()
                message = f"清理了 {cleaned_count} 个过期缓存文件"
            
            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "message": message
            }
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "清理缓存失败"
            }


def create_mcp_handlers() -> MCPHandlers:
    """创建MCP处理器实例"""
    return MCPHandlers()


