#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
媒体提取核心模块 - 向后兼容的统一接口
此模块已重构为使用新的独立平台提取器架构，但保持原有API兼容性
"""

import logging
from typing import Dict, Any, List
from .managers.media_extractor_manager import MediaExtractorManager

# 设置日志
logger = logging.getLogger("video-sum-mcp.media_extractor")

class MediaExtractor:
    """
    媒体提取器 - 向后兼容的统一接口
    
    此类是对新架构的封装，保持与原有代码的兼容性
    内部使用 MediaExtractorManager 来处理各平台的提取任务
    """
    
    def __init__(self, use_proxy: bool = False):
        """
        初始化媒体提取器
        
        参数:
            use_proxy: 是否使用代理
        """
        self.use_proxy = use_proxy
        
        # 使用新的管理器架构
        self.manager = MediaExtractorManager(use_proxy=use_proxy)
        
        logger.info(f"MediaExtractor 初始化完成 (兼容模式)")
        logger.info(f"支持的平台: {', '.join(self.manager.get_supported_platforms())}")
    
    def extract(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """
        提取视频内容 - 向后兼容接口
        
        参数:
            url: 视频URL
            context_text: 上下文文本（可选）
            
        返回:
            包含视频内容的字典，格式与原版本兼容
        """
        logger.info(f"MediaExtractor.extract() 被调用: {url}")
        
        try:
            # 使用新的管理器进行提取
            result = self.manager.extract_content(url, context_text)
            
            # 确保返回格式与原版本兼容
            if result.get('status') == 'success':
                logger.info(f"提取成功: {result.get('platform', 'unknown')}")
            else:
                logger.warning(f"提取失败: {result.get('message', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"MediaExtractor.extract() 异常: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "message": error_msg,
                "url": url,
                "platform": "unknown",
                "metadata": {},
                "content": ""
            }
    
    def get_supported_platforms(self) -> List[str]:
        """
        获取支持的平台列表 - 向后兼容接口
        
        返回:
            支持的平台名称列表
        """
        return self.manager.get_supported_platforms()
    
    def validate_url(self, url: str) -> bool:
        """
        验证URL是否被支持 - 向后兼容接口
        
        参数:
            url: 要验证的URL
            
        返回:
            是否支持此URL
        """
        return self.manager.validate_url(url)
    
    def detect_platform(self, url: str) -> str:
        """
        检测URL平台 - 向后兼容接口
        
        参数:
            url: 视频URL
            
        返回:
            平台名称，如果不支持则返回 "unknown"
        """
        platform = self.manager.detect_platform(url)
        return platform if platform else "unknown"
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        获取平台信息 - 新增功能
        
        返回:
            各平台的详细信息
        """
        return self.manager.get_platform_info()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息 - 新增功能
        
        返回:
            提取器统计信息
        """
        stats = self.manager.get_statistics()
        stats['compatibility_mode'] = True
        return stats
    
    @property
    def extractors(self):
        """向后兼容属性：访问内部提取器"""
        return self.manager._extractors
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"MediaExtractor(compatibility_mode=True, platforms={len(self.manager.get_supported_platforms())})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"MediaExtractor(manager={self.manager}, use_proxy={self.use_proxy})"


# 向后兼容：导出原有的提取器类
# 现在这些类指向新的独立模块
from .extractors import (
    BaseExtractor,
    DouyinExtractor,
    BilibiliExtractor,
    XiaohongshuExtractor,
    ZhihuExtractor
)

# 向后兼容：保持原有的类导出
__all__ = [
    'MediaExtractor',
    'BaseExtractor',
    'DouyinExtractor',
    'BilibiliExtractor',
    'XiaohongshuExtractor',
    'ZhihuExtractor'
] 