#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安全爬虫模块 - 提供安全的网络请求功能，防止对目标网站造成过大压力
"""

import time
import logging
import requests
from typing import Optional, Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import json
from http.cookiejar import CookieJar

logger = logging.getLogger("video-sum-mcp.safe_crawler")

class SafeRequester:
    """安全请求器，包含频率控制和重试机制"""
    
    def __init__(self, min_delay: float = 1.0, max_retries: int = 3):
        """
        初始化安全请求器
        
        参数:
            min_delay: 最小请求间隔（秒）
            max_retries: 最大重试次数
        """
        self.min_delay = min_delay
        self.max_retries = max_retries
        self.last_request_time = {}  # 记录每个域名的最后请求时间
        
        # 更真实的User-Agent池 - 2024最新版本
        self.user_agents = [
            # Chrome Windows 最新版本
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Chrome macOS 最新版本
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            
            # Firefox 最新版本
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0',
            
            # Safari 最新版本
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            
            # Edge 最新版本
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
        ]
        
        # 移动端User-Agent - 抖音常用
        self.mobile_user_agents = [
            # iPhone 最新版本
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            
            # Android Chrome 最新版本
            'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
            
            # 抖音APP内置浏览器模拟
            'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/122.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
        ]
        
        # 平台特定的User-Agent策略
        self.platform_user_agents = {
            'douyin.com': self.mobile_user_agents,  # 抖音优先使用移动端
            'v.douyin.com': self.mobile_user_agents,
            'xiaohongshu.com': self.mobile_user_agents + self.user_agents[:3],  # 小红书混用
            'zhihu.com': self.user_agents,  # 知乎使用桌面端
            'bilibili.com': self.user_agents,  # B站使用桌面端
        }
        
        # 创建session并启用cookie管理
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,  # 增加退避时间
            status_forcelist=[429, 500, 502, 503, 504, 403, 502],
            respect_retry_after_header=True,
            raise_on_status=False  # 不要抛出异常，让我们自己处理
        )
        
        # 应用重试策略
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置基础请求头
        self._set_base_headers()
        
        # 为每个域名维护cookie jar
        self.domain_cookies = {}
    
    def _set_base_headers(self):
        """设置基础请求头（不包含User-Agent）"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
    
    def _get_domain(self, url: str) -> str:
        """从URL中提取域名"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def _get_platform_specific_user_agent(self, url: str) -> str:
        """根据URL获取平台特定的User-Agent"""
        import random
        domain = self._get_domain(url)
        
        # 检查是否有平台特定的User-Agent
        for platform_domain, agents in self.platform_user_agents.items():
            if platform_domain in domain:
                return random.choice(agents)
        
        # 如果没有特定的，使用通用的
        return random.choice(self.user_agents)
    
    def _get_platform_specific_headers(self, url: str) -> dict:
        """根据URL获取平台特定的请求头"""
        domain = self._get_domain(url)
        headers = {}
        
        # 根据平台设置特定的请求头
        if 'douyin.com' in domain:
            headers.update({
                'Referer': 'https://www.douyin.com/',
                'Sec-Fetch-Site': 'same-origin',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            })
        elif 'xiaohongshu.com' in domain:
            headers.update({
                'Referer': 'https://www.xiaohongshu.com/',
                'Sec-Fetch-Site': 'same-origin',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            })
        elif 'zhihu.com' in domain:
            headers.update({
                'Referer': 'https://www.zhihu.com/',
                'Sec-Fetch-Site': 'same-origin',
            })
        elif 'bilibili.com' in domain:
            headers.update({
                'Referer': 'https://www.bilibili.com/',
                'Sec-Fetch-Site': 'same-origin',
            })
        
        return headers
    
    def _wait_if_needed(self, domain: str):
        """如果需要，等待一段时间以避免请求过于频繁"""
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.min_delay:
                wait_time = self.min_delay - elapsed
                logger.info(f"等待 {wait_time:.1f} 秒以避免请求过于频繁 (域名: {domain})")
                time.sleep(wait_time)
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        安全的GET请求
        
        参数:
            url: 请求URL
            **kwargs: 其他requests参数
            
        返回:
            Response对象或None（如果请求失败）
        """
        domain = self._get_domain(url)
        self._wait_if_needed(domain)
        
        try:
            # 设置默认超时
            kwargs.setdefault('timeout', 10)
            
            # 动态设置User-Agent和平台特定请求头
            request_headers = kwargs.get('headers', {})
            request_headers['User-Agent'] = self._get_platform_specific_user_agent(url)
            request_headers.update(self._get_platform_specific_headers(url))
            kwargs['headers'] = request_headers
            
            logger.info(f"发送GET请求: {url}")
            logger.debug(f"使用User-Agent: {request_headers['User-Agent']}")
            
            response = self.session.get(url, **kwargs)
            
            # 更新最后请求时间
            self.last_request_time[domain] = time.time()
            
            # 检查状态码
            if response.status_code == 200:
                logger.info(f"请求成功: {url} (状态码: {response.status_code})")
                return response
            elif response.status_code == 404:
                logger.warning(f"页面不存在: {url} (状态码: {response.status_code})")
                return response  # 404也返回，由调用者处理
            elif response.status_code == 403:
                logger.warning(f"请求被拒绝，可能遭遇反爬虫: {url} (状态码: {response.status_code})")
                return response
            elif response.status_code == 429:
                logger.warning(f"请求频率过高: {url} (状态码: {response.status_code})")
                return response
            else:
                logger.warning(f"请求返回非200状态码: {url} (状态码: {response.status_code})")
                return response
                
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {url}")
        except requests.exceptions.ConnectionError:
            logger.error(f"连接错误: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {url} - {str(e)}")
        except Exception as e:
            logger.error(f"未知错误: {url} - {str(e)}")
        
        return None
    
    def head(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        安全的HEAD请求（用于获取重定向信息）
        
        参数:
            url: 请求URL
            **kwargs: 其他requests参数
            
        返回:
            Response对象或None（如果请求失败）
        """
        domain = self._get_domain(url)
        self._wait_if_needed(domain)
        
        try:
            # 设置默认超时
            kwargs.setdefault('timeout', 10)
            
            logger.info(f"发送HEAD请求: {url}")
            response = self.session.head(url, **kwargs)
            
            # 更新最后请求时间
            self.last_request_time[domain] = time.time()
            
            logger.info(f"HEAD请求完成: {url} (状态码: {response.status_code})")
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"HEAD请求超时: {url}")
        except requests.exceptions.ConnectionError:
            logger.error(f"HEAD连接错误: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"HEAD请求异常: {url} - {str(e)}")
        except Exception as e:
            logger.error(f"HEAD未知错误: {url} - {str(e)}")
        
        return None

    def _get_enhanced_douyin_headers(self, url: str, referer: str = None) -> dict:
        """获取增强的抖音请求头"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referer else 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?1',  # 移动端标识
            'sec-ch-ua-platform': '"Android"',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        if referer:
            headers['Referer'] = referer
        
        # 随机添加一些可选的请求头
        optional_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Priority': 'u=0, i',
        }
        
        # 50% 概率添加可选请求头
        for key, value in optional_headers.items():
            if random.random() > 0.5:
                headers[key] = value
        
        return headers
    
    def _simulate_user_behavior(self, domain: str):
        """模拟用户行为，添加随机延时"""
        if domain in self.last_request_time:
            # 随机延时 1.5 - 4.0 秒，模拟人类浏览行为
            base_delay = max(self.min_delay, 1.5)
            random_delay = base_delay + random.uniform(0, 2.5)
            
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < random_delay:
                wait_time = random_delay - elapsed
                logger.info(f"模拟人类浏览，等待 {wait_time:.1f} 秒 (域名: {domain})")
                time.sleep(wait_time)
    
    def get_with_enhanced_protection(self, url: str, **kwargs) -> requests.Response:
        """
        使用增强保护模式发送GET请求
        
        参数:
            url: 请求URL
            **kwargs: 其他请求参数
            
        返回:
            requests.Response: 响应对象
        """
        domain = self._get_domain(url)
        self._wait_if_needed(domain)
        
        # 设置默认参数 - 移除不支持的max_redirects参数
        default_kwargs = {
            'timeout': kwargs.get('timeout', 30),
            'allow_redirects': kwargs.get('allow_redirects', True),
            'verify': kwargs.get('verify', True),
        }
        
        # 合并用户提供的参数
        request_kwargs = {**default_kwargs, **kwargs}
        
        logger.info(f"发送增强保护GET请求: {url}")
        
        try:
            response = self.session.get(url, **request_kwargs)
            self._update_last_request_time(domain)
            return response
        except Exception as e:
            logger.error(f"增强保护GET请求失败: {url}, 错误: {e}")
            raise
    
    def _has_valid_session(self, domain: str) -> bool:
        """检查是否有有效的session"""
        return domain in self.domain_cookies and bool(self.domain_cookies[domain])
    
    def _establish_session(self, domain: str):
        """为域名建立session"""
        if 'douyin.com' in domain:
            try:
                # 先访问抖音主页建立session
                main_page_url = 'https://www.douyin.com/'
                headers = {
                    'User-Agent': random.choice(self.mobile_user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                response = self.session.get(main_page_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    logger.info(f"成功建立{domain}的session")
                    self.domain_cookies[domain] = response.cookies
                    time.sleep(random.uniform(1, 3))  # 随机等待
                
            except Exception as e:
                logger.warning(f"建立{domain}的session失败: {str(e)}")
    
    def _is_captcha_page(self, response: requests.Response) -> bool:
        """检测是否为验证码页面"""
        if not response or response.status_code != 200:
            return False
        
        content_lower = response.text.lower()
        captcha_indicators = [
            '验证码中间页',
            'captcha',
            '请输入验证码',
            '安全验证',
            'security check',
            'verify',
            '人机验证',
            '滑动验证',
            'slide to verify'
        ]
        
        return any(indicator in content_lower for indicator in captcha_indicators)

    def _update_last_request_time(self, domain: str):
        """更新域名的最后请求时间"""
        self.last_request_time[domain] = time.time()


# 全局安全请求器实例
_global_safe_requester = None

def get_safe_requester(min_delay: float = 2.0, max_retries: int = 3) -> SafeRequester:
    """
    获取全局安全请求器实例
    
    参数:
        min_delay: 最小请求间隔（秒），默认2秒确保安全
        max_retries: 最大重试次数
        
    返回:
        SafeRequester实例
    """
    global _global_safe_requester
    if _global_safe_requester is None:
        _global_safe_requester = SafeRequester(min_delay=min_delay, max_retries=max_retries)
        logger.info(f"创建安全请求器，最小间隔: {min_delay}秒")
    return _global_safe_requester

def reset_safe_requester():
    """重置全局安全请求器实例"""
    global _global_safe_requester
    _global_safe_requester = None

def batch_process_urls(urls: list, processor_func, batch_size: int = 5, batch_delay: float = 10.0):
    """
    批量处理URL的安全函数，防止对平台造成过大压力
    
    参数:
        urls: URL列表
        processor_func: 处理单个URL的函数
        batch_size: 每批处理的URL数量，默认5个
        batch_delay: 批次间的延迟时间（秒），默认10秒
        
    返回:
        处理结果列表
    """
    import time
    
    results = []
    total_batches = (len(urls) + batch_size - 1) // batch_size
    
    logger.info(f"开始批量处理 {len(urls)} 个URL，分 {total_batches} 批，每批 {batch_size} 个")
    
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"处理第 {batch_num}/{total_batches} 批，包含 {len(batch_urls)} 个URL")
        
        batch_results = []
        for url in batch_urls:
            try:
                result = processor_func(url)
                batch_results.append(result)
                logger.info(f"处理完成: {url}")
            except Exception as e:
                logger.error(f"处理失败: {url} - {str(e)}")
                batch_results.append({
                    "status": "error",
                    "message": str(e),
                    "url": url
                })
        
        results.extend(batch_results)
        
        # 如果还有下一批，等待一段时间
        if i + batch_size < len(urls):
            logger.info(f"批次间等待 {batch_delay} 秒，防止请求过于频繁...")
            time.sleep(batch_delay)
    
    logger.info(f"批量处理完成，共处理 {len(results)} 个URL")
    return results


# ==================== 异步安全请求器 ====================

import asyncio
import aiohttp
from ..utils_modules.platform_strategies import platform_manager, PlatformStrategy

class AsyncSafeRequester:
    """异步安全请求器，支持并发控制和平台特定策略"""
    
    def __init__(self, max_concurrent: int = 3):
        """
        初始化异步安全请求器
        
        参数:
            max_concurrent: 最大并发请求数
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,
            limit_per_host=self.max_concurrent,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=20
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """
        异步GET请求，集成平台策略
        
        参数:
            url: 请求URL
            **kwargs: 其他aiohttp参数
            
        返回:
            ClientResponse对象或None（如果请求失败）
        """
        if not self.session:
            raise RuntimeError("AsyncSafeRequester必须在async with语句中使用")
        
        async with self.semaphore:
            # 根据平台策略等待
            await platform_manager.wait_if_needed(url)
            
            # 获取平台特定的请求策略
            strategy = platform_manager.get_strategy(url)
            headers = strategy.get_headers(url)
            
            # 合并用户提供的headers
            if 'headers' in kwargs:
                headers.update(kwargs['headers'])
            kwargs['headers'] = headers
            
            try:
                logger.info(f"发送异步GET请求: {url}")
                
                async with self.session.get(url, **kwargs) as response:
                    # 读取响应内容以确保连接完全处理
                    await response.read()
                    
                    if response.status == 200:
                        logger.info(f"异步请求成功: {url} (状态码: {response.status})")
                    else:
                        logger.warning(f"异步请求返回非200状态码: {url} (状态码: {response.status})")
                    
                    return response
                    
            except asyncio.TimeoutError:
                logger.error(f"异步请求超时: {url}")
            except aiohttp.ClientError as e:
                logger.error(f"异步请求客户端错误: {url} - {str(e)}")
            except Exception as e:
                logger.error(f"异步请求未知错误: {url} - {str(e)}")
            
            return None
    
    async def head(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """
        异步HEAD请求
        
        参数:
            url: 请求URL
            **kwargs: 其他aiohttp参数
            
        返回:
            ClientResponse对象或None（如果请求失败）
        """
        if not self.session:
            raise RuntimeError("AsyncSafeRequester必须在async with语句中使用")
        
        async with self.semaphore:
            # 根据平台策略等待
            await platform_manager.wait_if_needed(url)
            
            # 获取平台特定的请求策略
            strategy = platform_manager.get_strategy(url)
            headers = strategy.get_headers(url)
            
            # 合并用户提供的headers
            if 'headers' in kwargs:
                headers.update(kwargs['headers'])
            kwargs['headers'] = headers
            
            try:
                logger.info(f"发送异步HEAD请求: {url}")
                
                async with self.session.head(url, **kwargs) as response:
                    logger.info(f"异步HEAD请求完成: {url} (状态码: {response.status})")
                    return response
                    
            except asyncio.TimeoutError:
                logger.error(f"异步HEAD请求超时: {url}")
            except aiohttp.ClientError as e:
                logger.error(f"异步HEAD请求客户端错误: {url} - {str(e)}")
            except Exception as e:
                logger.error(f"异步HEAD请求未知错误: {url} - {str(e)}")
            
            return None


async def async_batch_process_urls(
    urls: List[str], 
    processor_func, 
    max_concurrent: int = 3,
    progress_callback=None
) -> List[Any]:
    """
    异步批量处理URL，支持并发控制和进度回调
    
    参数:
        urls: URL列表
        processor_func: 异步处理单个URL的函数
        max_concurrent: 最大并发数
        progress_callback: 进度回调函数
        
    返回:
        处理结果列表
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_url(url: str, index: int):
        """处理单个URL的包装函数"""
        async with semaphore:
            try:
                if progress_callback:
                    await progress_callback(f"开始处理: {url}", index, len(urls))
                
                result = await processor_func(url)
                
                if progress_callback:
                    await progress_callback(f"完成处理: {url}", index + 1, len(urls))
                
                return result
                
            except Exception as e:
                logger.error(f"异步处理失败: {url} - {str(e)}")
                return {
                    "status": "error",
                    "message": str(e),
                    "url": url
                }
    
    logger.info(f"开始异步批量处理 {len(urls)} 个URL，最大并发: {max_concurrent}")
    
    # 创建所有任务
    tasks = [
        process_single_url(url, i) 
        for i, url in enumerate(urls)
    ]
    
    # 并发执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理异常结果
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"任务异常: {urls[i]} - {str(result)}")
            processed_results.append({
                "status": "error",
                "message": str(result),
                "url": urls[i]
            })
        else:
            processed_results.append(result)
    
    logger.info(f"异步批量处理完成，共处理 {len(processed_results)} 个URL")
    return processed_results


# 全局异步安全请求器实例
_global_async_safe_requester = None

async def get_async_safe_requester(max_concurrent: int = 3) -> AsyncSafeRequester:
    """
    获取全局异步安全请求器实例
    
    参数:
        max_concurrent: 最大并发数
        
    返回:
        AsyncSafeRequester实例
    """
    global _global_async_safe_requester
    if _global_async_safe_requester is None:
        _global_async_safe_requester = AsyncSafeRequester(max_concurrent=max_concurrent)
        logger.info(f"创建异步安全请求器，最大并发: {max_concurrent}")
    return _global_async_safe_requester

def reset_async_safe_requester():
    """重置全局异步安全请求器实例"""
    global _global_async_safe_requester
    _global_async_safe_requester = None 