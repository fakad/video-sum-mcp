#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础提取器接口 - 定义所有平台提取器的统一接口
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("video-sum-mcp.base_extractor")

class BaseExtractor(ABC):
    """视频内容提取器基类"""
    
    def __init__(self, use_proxy: bool = False):
        """
        初始化提取器基类
        
        参数:
            use_proxy: 是否使用代理
        """
        self.use_proxy = use_proxy
        self.session = None
        self.platform_name = self._get_platform_name()
        
        if use_proxy:
            # 配置代理
            import requests
            self.session = requests.Session()
            # TODO: 根据需要配置代理设置
            # self.session.proxies = {'http': 'proxy_url', 'https': 'proxy_url'}
    
    @abstractmethod
    def _get_platform_name(self) -> str:
        """
        获取平台名称
        
        返回:
            平台名称字符串
        """
        pass
    
    @abstractmethod
    def extract(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """
        提取视频内容
        
        参数:
            url: 视频URL
            context_text: 上下文文本（可选）
            
        返回:
            包含视频内容的字典，格式：
            {
                "platform": str,
                "url": str,
                "metadata": dict,
                "content": str,
                "status": str  # "success" 或 "error"
            }
        """
        pass
    
    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        验证URL是否受此提取器支持
        
        参数:
            url: 视频URL
            
        返回:
            是否支持此URL
        """
        pass
    
    def get_supported_url_patterns(self) -> list:
        """
        获取支持的URL模式（正则表达式）
        
        返回:
            URL模式列表
        """
        return []
    
    def get_platform_config(self) -> Dict[str, Any]:
        """
        获取平台特定配置
        
        返回:
            平台配置字典
        """
        return {
            "name": self.platform_name,
            "use_proxy": self.use_proxy,
            "supported_patterns": self.get_supported_url_patterns()
        }
    
    def _create_error_result(self, url: str, error_message: str) -> Dict[str, Any]:
        """
        创建错误结果
        
        参数:
            url: 原始URL
            error_message: 错误信息
            
        返回:
            错误结果字典
        """
        return {
            "platform": self.platform_name,
            "url": url,
            "status": "error",
            "message": error_message,
            "metadata": {},
            "content": ""
        }
    
    def _create_success_result(self, url: str, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """
        创建成功结果
        
        参数:
            url: 原始URL
            metadata: 元数据
            content: 内容文本
            
        返回:
            成功结果字典
        """
        return {
            "platform": self.platform_name,
            "url": url,
            "status": "success",
            "metadata": metadata,
            "content": content
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(platform={self.platform_name})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"{self.__class__.__name__}(platform={self.platform_name}, use_proxy={self.use_proxy})" 