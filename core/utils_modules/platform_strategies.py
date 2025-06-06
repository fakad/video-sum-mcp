"""
平台特定请求策略配置系统

为不同视频平台提供差异化的请求策略，包括请求间隔、重试次数、
请求头配置等，以优化安全性和成功率。
"""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlatformStrategy:
    """平台特定的请求策略配置"""
    
    name: str
    # 请求间隔配置
    min_interval: float  # 最小间隔秒数
    max_interval: float  # 最大间隔秒数
    
    # 重试配置
    max_retries: int = 3
    retry_backoff: float = 2.0  # 重试退避因子
    
    # 请求头配置
    user_agents: list = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ])
    
    # 特殊请求头
    extra_headers: Dict[str, str] = field(default_factory=dict)
    
    # 超时配置
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    
    # 并发限制
    max_concurrent: int = 2
    
    # 特殊处理标志
    requires_mobile_ua: bool = False
    requires_referer: bool = False
    
    def get_headers(self, url: str = "") -> Dict[str, str]:
        """获取请求头配置"""
        import random
        
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # 添加特殊头部
        if self.requires_referer and url:
            parsed = urlparse(url)
            headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
            
        if self.requires_mobile_ua:
            headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
        
        # 合并额外头部
        headers.update(self.extra_headers)
        
        return headers
    
    def get_request_interval(self) -> float:
        """获取请求间隔（带随机化）"""
        import random
        return random.uniform(self.min_interval, self.max_interval)


class PlatformStrategyManager:
    """平台策略管理器"""
    
    def __init__(self):
        self._strategies: Dict[str, PlatformStrategy] = {}
        self._last_request_times: Dict[str, float] = {}
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """初始化默认平台策略"""
        
        # 抖音策略：较严格的间隔控制
        self._strategies["douyin"] = PlatformStrategy(
            name="douyin",
            min_interval=6.0,
            max_interval=10.0,
            max_retries=2,
            retry_backoff=3.0,
            extra_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "max-age=0",
            },
            requires_mobile_ua=True,
            requires_referer=True,
            max_concurrent=2,
        )
        
        # 小红书策略：中等间隔
        self._strategies["xiaohongshu"] = PlatformStrategy(
            name="xiaohongshu",
            min_interval=4.0,
            max_interval=7.0,
            max_retries=3,
            retry_backoff=2.0,
            extra_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            },
            requires_referer=True,
            max_concurrent=2,
        )
        
        # 知乎策略：相对宽松
        self._strategies["zhihu"] = PlatformStrategy(
            name="zhihu",
            min_interval=2.0,
            max_interval=4.0,
            max_retries=3,
            retry_backoff=1.5,
            extra_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            max_concurrent=3,
        )
        
        # 默认策略：通用配置
        self._strategies["default"] = PlatformStrategy(
            name="default",
            min_interval=3.0,
            max_interval=5.0,
            max_retries=3,
            retry_backoff=2.0,
            max_concurrent=2,
        )
    
    def detect_platform(self, url: str) -> str:
        """根据URL检测平台类型"""
        url_lower = url.lower()
        
        if "douyin.com" in url_lower or "iesdouyin.com" in url_lower:
            return "douyin"
        elif "xiaohongshu.com" in url_lower or "xhs.com" in url_lower:
            return "xiaohongshu"
        elif "zhihu.com" in url_lower:
            return "zhihu"
        else:
            return "default"
    
    def get_strategy(self, url_or_platform: str) -> PlatformStrategy:
        """获取平台策略"""
        if url_or_platform in self._strategies:
            # 直接平台名称
            platform = url_or_platform
        else:
            # URL，需要检测平台
            platform = self.detect_platform(url_or_platform)
        
        return self._strategies.get(platform, self._strategies["default"])
    
    async def wait_if_needed(self, url: str) -> None:
        """根据平台策略等待适当的时间间隔"""
        platform = self.detect_platform(url)
        strategy = self.get_strategy(platform)
        
        last_time = self._last_request_times.get(platform, 0)
        current_time = time.time()
        
        time_since_last = current_time - last_time
        required_interval = strategy.get_request_interval()
        
        if time_since_last < required_interval:
            wait_time = required_interval - time_since_last
            logger.debug(f"等待 {wait_time:.2f}秒 (平台: {platform})")
            await asyncio.sleep(wait_time)
        
        self._last_request_times[platform] = time.time()
    
    def get_platform_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取各平台的统计信息"""
        stats = {}
        for platform, strategy in self._strategies.items():
            last_request = self._last_request_times.get(platform, 0)
            stats[platform] = {
                "strategy": {
                    "min_interval": strategy.min_interval,
                    "max_interval": strategy.max_interval,
                    "max_concurrent": strategy.max_concurrent,
                    "max_retries": strategy.max_retries,
                },
                "last_request_time": last_request,
                "time_since_last": time.time() - last_request if last_request > 0 else 0,
            }
        return stats
    
    def add_custom_strategy(self, platform: str, strategy: PlatformStrategy) -> None:
        """添加自定义平台策略"""
        self._strategies[platform] = strategy
        logger.info(f"添加自定义策略: {platform}")
    
    def update_strategy(self, platform: str, **kwargs) -> None:
        """更新现有策略的参数"""
        if platform in self._strategies:
            strategy = self._strategies[platform]
            for key, value in kwargs.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
            logger.info(f"更新策略: {platform}")
        else:
            logger.warning(f"平台策略不存在: {platform}")


# 全局策略管理器实例
platform_manager = PlatformStrategyManager() 