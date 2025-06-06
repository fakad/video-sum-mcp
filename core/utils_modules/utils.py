#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数模块，提供配置管理和通用工具函数
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional

# 延迟导入避免循环依赖

# 设置日志
logger = logging.getLogger("video-sum-mcp.utils")

def get_config() -> Dict[str, Any]:
    """
    获取配置信息（向后兼容接口）
    
    返回:
        配置字典
    """
    try:
        from .config_manager import get_global_config_manager
        config_manager = get_global_config_manager()
        return config_manager.get_all()
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        # 回退到默认配置
        return {
            "api_key": None,
            "proxy": None,
            "temp_dir": "temp_contents",
            "supported_platforms": ["bilibili", "douyin", "xiaohongshu", "zhihu"],
            "supported_formats": ["markdown", "xmind"]
        }

def update_config(config_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新配置信息（向后兼容接口）
    
    参数:
        config_updates: 要更新的配置项
    
    返回:
        更新后的完整配置
    """
    try:
        from .config_manager import get_global_config_manager
        config_manager = get_global_config_manager()
        
        # 更新运行时配置
        for path, value in config_updates.items():
            config_manager.set(path, value)
        
        logger.info("配置已更新（运行时）")
        return config_manager.get_all()
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        raise

def get_config_value(path: str, default: Any = None) -> Any:
    """
    获取特定配置值
    
    参数:
        path: 配置路径，如 'logging.level' 或 'batch_processing.max_concurrent_requests'
        default: 默认值
    
    返回:
        配置值
    """
    try:
        from .config_manager import get_global_config_manager
        config_manager = get_global_config_manager()
        return config_manager.get(path, default)
    except Exception as e:
        logger.error(f"获取配置值 {path} 失败: {str(e)}")
        return default

def get_platform_config(platform: str) -> Dict[str, Any]:
    """
    获取平台特定配置
    
    参数:
        platform: 平台名称（如 'bilibili', 'douyin'）
    
    返回:
        平台配置字典
    """
    try:
        from .config_manager import get_global_config_manager
        config_manager = get_global_config_manager()
        return config_manager.get_platform_config(platform)
    except Exception as e:
        logger.error(f"获取平台 {platform} 配置失败: {str(e)}")
        return {}

def reload_config():
    """重新加载配置"""
    try:
        from .config_manager import get_global_config_manager
        config_manager = get_global_config_manager()
        config_manager.reload()
        logger.info("配置已重新加载")
    except Exception as e:
        logger.error(f"重新加载配置失败: {str(e)}")
        raise

def ensure_directory(directory: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    参数:
        directory: 目录路径
    
    返回:
        目录的绝对路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"创建目录: {directory}")
    return os.path.abspath(directory)

def generate_video_id(url: str) -> str:
    """
    根据视频URL生成唯一标识
    
    参数:
        url: 视频URL
    
    返回:
        视频唯一标识(MD5哈希)
    """
    return hashlib.md5(url.encode()).hexdigest()

def create_temp_content_file(content: Dict[str, Any], video_id: str) -> str:
    """
    创建暂存视频内容的中间态文件
    
    参数:
        content: 视频内容数据
        video_id: 视频唯一标识
    
    返回:
        临时文件路径
    """
    temp_dir_name = get_config_value("temp_dir", "temp_contents")
    temp_dir = os.path.join(os.getcwd(), temp_dir_name)
    ensure_directory(temp_dir)
    
    temp_file = os.path.join(temp_dir, f"{video_id}.json")
    
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    
    logger.info(f"创建临时内容文件: {temp_file}")
    return temp_file

def read_temp_content_file(video_id: str) -> Dict[str, Any]:
    """
    读取暂存的视频内容
    
    参数:
        video_id: 视频唯一标识
    
    返回:
        视频内容数据
    """
    temp_dir_name = get_config_value("temp_dir", "temp_contents")
    temp_dir = os.path.join(os.getcwd(), temp_dir_name)
    temp_file = os.path.join(temp_dir, f"{video_id}.json")
    
    if not os.path.exists(temp_file):
        error_msg = f"找不到视频 {video_id} 的暂存内容文件"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    with open(temp_file, "r", encoding="utf-8") as f:
        return json.load(f)

def cleanup_temp_content(video_id: str) -> None:
    """
    清理暂存的视频内容文件
    
    参数:
        video_id: 视频唯一标识
    """
    temp_dir_name = get_config_value("temp_dir", "temp_contents")
    temp_dir = os.path.join(os.getcwd(), temp_dir_name)
    temp_file = os.path.join(temp_dir, f"{video_id}.json")
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
        logger.info(f"已清理临时内容文件: {temp_file}")

def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    清理文件名，移除非法字符并限制长度
    
    参数:
        filename: 原始文件名
        max_length: 最大长度限制
    
    返回:
        清理后的文件名
    """
    import re
    
    # 移除或替换非法字符
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # 移除多余的空格和点
    filename = re.sub(r'\s+', '_', filename.strip())
    filename = filename.strip('.')
    
    # 限制长度
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip('_.')
    
    # 确保不为空
    if not filename:
        filename = "untitled"
    
    return filename

def save_document(content: str, filename: str, output_dir: str = "output") -> str:
    """
    保存文档到指定目录
    
    参数:
        content: 文档内容
        filename: 文件名
        output_dir: 输出目录
    
    返回:
        保存的文件路径
    """
    from pathlib import Path
    
    # 确保输出目录存在
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 清理文件名
    clean_filename = sanitize_filename(filename)
    if not clean_filename.endswith('.md'):
        clean_filename += '.md'
    
    # 保存文件
    file_path = output_path / clean_filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"文档已保存: {file_path}")
    return str(file_path) 