#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
媒体提取器管理器 - 统一管理各平台独立提取器的入口
"""

import logging
from typing import Dict, Any, Optional, Type
from ..extractors import (
    BaseExtractor,
    DouyinExtractor,
    BilibiliExtractor,
    XiaohongshuExtractor,
    ZhihuExtractor
)

logger = logging.getLogger("video-sum-mcp.media_extractor_manager")

class MediaExtractorManager:
    """媒体提取器管理器 - 统一各平台提取器的管理和调用"""
    
    def __init__(self, use_proxy: bool = False):
        """
        初始化媒体提取器管理器
        
        参数:
            use_proxy: 是否使用代理
        """
        self.use_proxy = use_proxy
        self._extractors: Dict[str, BaseExtractor] = {}
        self._platform_patterns: Dict[str, BaseExtractor] = {}
        
        # 注册所有支持的平台提取器
        self._register_extractors()
        
        logger.info(f"媒体提取器管理器初始化完成，支持 {len(self._extractors)} 个平台")
    
    def _register_extractors(self):
        """注册所有平台提取器"""
        extractor_classes = [
            DouyinExtractor,
            BilibiliExtractor,
            XiaohongshuExtractor,
            ZhihuExtractor
        ]
        
        for extractor_class in extractor_classes:
            try:
                # 创建提取器实例
                extractor = extractor_class(use_proxy=self.use_proxy)
                platform = extractor.platform_name
                
                # 注册到提取器字典
                self._extractors[platform] = extractor
                
                # 注册URL模式映射
                patterns = extractor.get_supported_url_patterns()
                for pattern in patterns:
                    self._platform_patterns[pattern] = extractor
                
                logger.info(f"已注册 {platform} 提取器，支持 {len(patterns)} 种URL模式")
                
            except Exception as e:
                logger.error(f"注册提取器 {extractor_class.__name__} 失败: {str(e)}")
    
    def get_supported_platforms(self) -> list:
        """获取所有支持的平台列表"""
        return list(self._extractors.keys())
    
    def detect_platform(self, url: str) -> Optional[str]:
        """
        检测URL属于哪个平台
        
        参数:
            url: 视频/内容URL
            
        返回:
            平台名称，如果不支持则返回None
        """
        for extractor in self._extractors.values():
            if extractor.validate_url(url):
                return extractor.platform_name
        
        logger.warning(f"无法识别URL平台: {url}")
        return None
    
    def get_extractor(self, platform: str) -> Optional[BaseExtractor]:
        """
        获取指定平台的提取器
        
        参数:
            platform: 平台名称
            
        返回:
            对应的提取器实例，如果不支持则返回None
        """
        return self._extractors.get(platform)
    
    def get_extractor_by_url(self, url: str) -> Optional[BaseExtractor]:
        """
        根据URL获取对应的提取器
        
        参数:
            url: 视频/内容URL
            
        返回:
            对应的提取器实例，如果不支持则返回None
        """
        platform = self.detect_platform(url)
        if platform:
            return self._extractors.get(platform)
        return None
    
    def extract_content(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """
        提取内容的统一入口
        
        参数:
            url: 视频/内容URL
            context_text: 上下文文本（可选）
            
        返回:
            提取结果字典
        """
        logger.info(f"开始提取内容: {url}")
        
        try:
            # 检测平台并获取提取器
            extractor = self.get_extractor_by_url(url)
            
            if not extractor:
                return self._create_unsupported_result(url)
            
            logger.info(f"使用 {extractor.platform_name} 提取器处理URL")
            
            # 调用对应提取器进行内容提取
            result = extractor.extract(url, context_text)
            
            # 在结果中添加管理器信息
            result['extractor_info'] = {
                'platform': extractor.platform_name,
                'manager_version': '1.0',
                'use_proxy': self.use_proxy
            }
            
            logger.info(f"内容提取完成: {extractor.platform_name}")
            return result
            
        except Exception as e:
            error_msg = f"内容提取过程中出现异常: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            
            return {
                "platform": "unknown",
                "url": url,
                "status": "error",
                "message": error_msg,
                "metadata": {},
                "content": "",
                "extractor_info": {
                    'manager_version': '1.0',
                    'use_proxy': self.use_proxy
                }
            }
    
    def _create_unsupported_result(self, url: str) -> Dict[str, Any]:
        """创建不支持的URL的结果"""
        return {
            "platform": "unsupported",
            "url": url,
            "status": "error",
            "message": f"不支持的URL类型。支持的平台: {', '.join(self.get_supported_platforms())}",
            "metadata": {},
            "content": "",
            "extractor_info": {
                'supported_platforms': self.get_supported_platforms(),
                'manager_version': '1.0',
                'use_proxy': self.use_proxy
            }
        }
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取所有平台的详细信息"""
        platform_info = {}
        
        for platform, extractor in self._extractors.items():
            config = extractor.get_platform_config()
            platform_info[platform] = {
                'name': config['name'],
                'supported_patterns': config['supported_patterns'],
                'use_proxy': config['use_proxy'],
                'extractor_class': extractor.__class__.__name__
            }
        
        return platform_info
    
    def validate_url(self, url: str) -> bool:
        """
        验证URL是否被支持
        
        参数:
            url: 要验证的URL
            
        返回:
            是否支持此URL
        """
        return self.detect_platform(url) is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            'total_extractors': len(self._extractors),
            'supported_platforms': self.get_supported_platforms(),
            'total_patterns': len(self._platform_patterns),
            'use_proxy': self.use_proxy,
            'manager_version': '1.0'
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        platforms = ', '.join(self.get_supported_platforms())
        return f"MediaExtractorManager(platforms=[{platforms}], use_proxy={self.use_proxy})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"MediaExtractorManager(extractors={len(self._extractors)}, patterns={len(self._platform_patterns)}, use_proxy={self.use_proxy})" 