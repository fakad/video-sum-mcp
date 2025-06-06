#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
抖音视频提取器 - 独立的抖音平台内容提取模块
"""

import logging
import re
import time
from typing import Dict, Any, Optional, Tuple
from .base_extractor import BaseExtractor

logger = logging.getLogger("video-sum-mcp.douyin_extractor")

class DouyinExtractor(BaseExtractor):
    """抖音视频提取器"""
    
    def _get_platform_name(self) -> str:
        """获取平台名称"""
        return "douyin"
    
    def get_supported_url_patterns(self) -> list:
        """获取支持的URL模式"""
        return [
            r"^https?://(?:www\.)?douyin\.com/video/(\d+)",
            r"^https?://v\.douyin\.com/([a-zA-Z0-9]+)/?",
            r"^https?://(?:www\.)?iesdouyin\.com/share/video/(\d+)",
            r"^https?://(?:www\.)?douyin\.com/user/.*modal_id=(\d+)"
        ]
    
    def validate_url(self, url: str) -> bool:
        """验证是否为抖音URL"""
        douyin_patterns = self.get_supported_url_patterns()
        
        for pattern in douyin_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def _extract_video_id(self, url: str) -> str:
        """提取视频ID - 增强版本支持短链接"""
        # 处理短链接重定向
        if "v.douyin.com" in url:
            try:
                redirect_url, video_id = self._resolve_douyin_short_url(url)
                if video_id:
                    logger.info(f"从短链接解析到视频ID: {video_id}")
                    self._redirect_url = redirect_url
                    return video_id
                elif redirect_url != url:
                    logger.info(f"短链接重定向: {url} -> {redirect_url}")
                    self._redirect_url = redirect_url
                    url = redirect_url
            except Exception as e:
                logger.warning(f"短链接解析失败: {str(e)}")
        
        # 从重定向后的URL中提取视频ID
        patterns = [
            r"/video/(\d+)",
            r"video/(\d+)",
            r"aweme/v1/aweme/detail.*?aweme_id=(\d+)",
            r"aweme_id=(\d+)",
            r"item_id=(\d+)",
            r"itemId=(\d+)",
            r"modal_id=(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(f"提取到视频ID: {video_id}")
                return video_id
        
        logger.error(f"无法从URL中提取视频ID: {url}")
        raise ValueError(f"无法从URL中提取视频ID: {url}")
    
    def _resolve_douyin_short_url(self, url: str) -> tuple[str, str]:
        """
        专门处理抖音短链接 (v.douyin.com) - 增强反爬虫版本
        
        参数:
            url: 抖音短链接
            
        返回:
            tuple: (重定向后的URL, 视频ID或None)
        """
        try:
            from core.services.safe_crawler import get_safe_requester
            import time
            import random
            
            logger.info(f"处理抖音短链接: {url}")
            
            safe_requester = get_safe_requester()
            
            # 2024年最新的抖音专用User-Agent池
            user_agents = [
                # 最新iPhone - 抖音APP内置浏览器模拟
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 aweme/31.2.0 JsSdk/1.0 NetType/WIFI Channel/App Store',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1',
                
                # 最新Android - 模拟抖音客户端
                'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
                'Mozilla/5.0 (Linux; Android 13; SM-G998B Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/122.0.0.0 Mobile Safari/537.36',
                'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
                
                # 微信内置浏览器 - 抖音允许分享到微信
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.47(0x18002f2f) NetType/WIFI Language/zh_CN',
                'Mozilla/5.0 (Linux; Android 13; ONEPLUS A9000) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/122.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.47.2560(0x28002F37) WeChatNotes/8.0.47',
            ]
            
            for i, user_agent in enumerate(user_agents):
                try:
                    logger.info(f"尝试User-Agent {i+1}: {user_agent[:50]}...")
                    
                    # 随机等待时间，模拟人类行为
                    wait_time = random.uniform(0.5, 2.0)
                    time.sleep(wait_time)
                    
                    # 根据User-Agent类型设置不同的headers
                    if 'iPhone' in user_agent:
                        headers = {
                            'User-Agent': user_agent,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache',
                        }
                    elif 'MicroMessenger' in user_agent:
                        # 微信内置浏览器特殊配置
                        headers = {
                            'User-Agent': user_agent,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'zh-CN,zh;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Connection': 'keep-alive',
                            'X-Requested-With': 'com.tencent.mm',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                        }
                    else:
                        # Android Chrome 配置
                        headers = {
                            'User-Agent': user_agent,
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                            'Accept-Encoding': 'gzip, deflate, br, zstd',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Sec-Fetch-User': '?1',
                            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                            'sec-ch-ua-mobile': '?1',
                            'sec-ch-ua-platform': '"Android"',
                        }
                    
                    # 第一步：获取重定向（不跟随）
                    response = safe_requester.session.get(
                        url, 
                        headers=headers,
                        allow_redirects=False, 
                        timeout=15,
                        verify=False
                    )
                    
                    logger.info(f"响应状态码: {response.status_code}")
                    
                    if response.status_code in [301, 302, 303, 307, 308]:
                        location = response.headers.get('Location', '')
                        if location:
                            logger.info(f"获取到重定向URL: {location}")
                            
                            # 处理相对路径
                            if location.startswith('/'):
                                from urllib.parse import urljoin
                                location = urljoin(url, location)
                            
                            # 检查重定向的URL是否包含视频ID
                            for pattern in [r"/video/(\d+)", r"video/(\d+)", r"aweme_id=(\d+)", r"item_id=(\d+)"]:
                                match = re.search(pattern, location)
                                if match:
                                    video_id = match.group(1)
                                    logger.info(f"从重定向URL中提取到视频ID: {video_id}")
                                    return location, video_id
                            
                            # 如果重定向URL中没有视频ID，继续跟随重定向
                            if 'douyin.com' in location:
                                final_response = safe_requester.session.get(
                                    location, 
                                    headers=headers,
                                    timeout=15,
                                    verify=False
                                )
                                
                                if final_response.status_code == 200:
                                    # 尝试从最终页面提取视频ID
                                    final_url = final_response.url
                                    video_id = self._extract_video_id_from_url(final_url)
                                    if video_id:
                                        return final_url, video_id
                                    
                                    # 从页面内容中提取
                                    video_id = self._extract_video_id_from_content(final_response.text)
                                    if video_id:
                                        return final_url, video_id
                            
                            return location, None
                    
                    elif response.status_code == 200:
                        # 直接返回内容，尝试提取
                        video_id = self._extract_video_id_from_content(response.text)
                        if video_id:
                            return response.url, video_id
                    
                    else:
                        logger.warning(f"User-Agent {i+1} 失败，状态码: {response.status_code}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"User-Agent {i+1} 异常: {str(e)}")
                    continue
            
            # 所有User-Agent都失败
            logger.error("所有User-Agent尝试都失败")
            return url, None
            
        except Exception as e:
            logger.error(f"抖音短链接解析失败: {url}, 错误: {str(e)}")
            return url, None
    
    def _extract_video_id_from_url(self, url: str) -> str:
        """从URL中提取视频ID"""
        patterns = [
            r"/video/(\d+)",
            r"video/(\d+)",
            r"aweme_id=(\d+)",
            r"item_id=(\d+)",
            r"itemId=(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_video_id_from_content(self, content: str) -> str:
        """从页面内容中提取视频ID"""
        try:
            # 多种提取模式
            patterns = [
                r'"aweme_id":"(\d+)"',
                r'"video_id":"(\d+)"',
                r'"item_id":"(\d+)"',
                r'"itemId":"(\d+)"',
                r'"awemeId":"(\d+)"',
                r'window\.__INITIAL_STATE__.*?"aweme_id":"(\d+)"',
                r'window\.__INITIAL_STATE__.*?"itemId":"(\d+)"',
                r'"aweme":{"aweme_id":"(\d+)"',
                r'aweme_id=(\d+)',
                r'item_id=(\d+)',
                r'/video/(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    video_id = match.group(1)
                    logger.info(f"从页面内容提取到视频ID: {video_id} (模式: {pattern})")
                    return video_id
            
            return None
            
        except Exception as e:
            logger.error(f"从页面内容提取视频ID失败: {str(e)}")
            return None
    
    def _get_video_info_from_web(self, url: str) -> Dict[str, Any]:
        """从网页版抖音获取视频信息 - 增强版"""
        from core.services.safe_crawler import get_safe_requester
        from bs4 import BeautifulSoup
        import json
        
        safe_requester = get_safe_requester()
        
        # 如果有重定向URL，优先使用重定向URL
        actual_url = getattr(self, '_redirect_url', url)
        
        # 多重策略尝试
        strategies = [
            ('enhanced_protection', '增强保护模式'),
            ('standard_mobile', '标准移动端模式'),
            ('desktop_fallback', '桌面端fallback模式')
        ]
        
        for strategy_name, strategy_desc in strategies:
            logger.info(f"尝试策略: {strategy_desc}")
            
            try:
                if strategy_name == 'enhanced_protection':
                    # 使用增强保护模式
                    response = safe_requester.get_with_enhanced_protection(actual_url)
                    
                elif strategy_name == 'standard_mobile':
                    # 标准移动端模式
                    mobile_headers = {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                    }
                    response = safe_requester.get(actual_url, headers=mobile_headers)
                    
                elif strategy_name == 'desktop_fallback':
                    # 桌面端fallback模式
                    desktop_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                    }
                    response = safe_requester.get(actual_url, headers=desktop_headers)
                
                if not response or response.status_code != 200:
                    logger.warning(f"策略 {strategy_desc} 请求失败，状态码: {response.status_code if response else 'None'}")
                    continue
                
                # 记录响应状态用于调试
                logger.info(f"策略 {strategy_desc} 成功 - 状态码: {response.status_code}")
                logger.info(f"响应内容长度: {len(response.content)}")
                logger.info(f"实际请求URL: {actual_url}")
                
                # 检查是否为验证码页面
                if self._is_captcha_response(response):
                    logger.warning(f"策略 {strategy_desc} 遇到验证码页面，尝试下一策略")
                    continue
                
                # 解析内容
                result = self._parse_douyin_response(response, strategy_name)
                
                if result and result.get('title') and result['title'] != '验证码中间页':
                    logger.info(f"策略 {strategy_desc} 成功提取内容")
                    return result
                else:
                    logger.warning(f"策略 {strategy_desc} 内容解析失败，尝试下一策略")
                    
            except Exception as e:
                logger.warning(f"策略 {strategy_desc} 异常: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        # 所有策略都失败，返回默认信息
        logger.error("所有抓取策略都失败")
        return self._get_default_video_info()
    
    def _is_captcha_response(self, response) -> bool:
        """检查响应是否为验证码页面"""
        if not response or response.status_code != 200:
            return True
        
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
            'slide to verify',
            '请完成安全验证',
            '为了确保不是机器人'
        ]
        
        title_element = response.text
        if any(indicator in content_lower for indicator in captcha_indicators):
            return True
        
        # 检查页面标题
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and '验证' in title_tag.text:
                return True
        except:
            pass
        
        return False
    
    def _parse_douyin_response(self, response, strategy_name: str) -> Dict[str, Any]:
        """解析抖音响应内容"""
        from bs4 import BeautifulSoup
        import json
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 尝试从页面标题获取信息
        title_tag = soup.find('title')
        title = title_tag.text if title_tag else "抖音视频"
        logger.info(f"页面标题: {title}")
        
        # 检查是否为有效的抖音页面
        if '验证码中间页' in title or '验证' in title:
            logger.warning("检测到验证码页面")
            return None
        
        # 尝试从meta标签获取描述
        description = ""
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            description = desc_tag.get('content', '')
            logger.info(f"Meta描述: {description[:100]}...")
        
        # 尝试从meta标签获取作者信息
        author = "未知作者"
        author_tag = soup.find('meta', attrs={'name': 'author'})
        if author_tag:
            author = author_tag.get('content', '未知作者')
        
        # 增强的JSON数据提取
        json_data_found = False
        extracted_data = {}
        
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if not script.string:
                continue
            
            # 扩展的JSON数据格式检测
            json_patterns = [
                ('window._ROUTER_DATA', r'window\._ROUTER_DATA\s*=\s*({.+?});?'),
                ('window.__INITIAL_STATE__', r'window\.__INITIAL_STATE__\s*=\s*({.+?});?'),
                ('window.INITIAL_STATE', r'window\.INITIAL_STATE\s*=\s*({.+?});?'),
                ('window._SSR_HYDRATED_DATA', r'window\._SSR_HYDRATED_DATA\s*=\s*({.+?});?'),
                ('window.__INITIAL_SSR_STATE__', r'window\.__INITIAL_SSR_STATE__\s*=\s*({.+?});?'),
                ('window.RENDER_DATA', r'window\.RENDER_DATA\s*=\s*({.+?});?'),
                ('self.__pace_data', r'self\.__pace_data\s*=\s*({.+?});?'),
            ]
            
            for pattern_name, pattern_regex in json_patterns:
                matches = re.findall(pattern_regex, script.string, re.DOTALL)
                
                for match in matches:
                    try:
                        # 清理JSON字符串
                        json_str = match.strip()
                        if json_str.endswith(';'):
                            json_str = json_str[:-1]
                        
                        data = json.loads(json_str)
                        logger.info(f"成功解析JSON数据，模式: {pattern_name}")
                        
                        # 尝试从JSON数据中提取详细信息
                        video_data = self._extract_video_data_from_json(data)
                        if video_data:
                            extracted_data.update(video_data)
                            json_data_found = True
                            logger.info(f"从JSON提取到视频数据: {video_data}")
                        
                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(f"解析JSON失败 ({pattern_name}): {str(e)}")
                        continue
        
        # 如果JSON解析失败，尝试从HTML中提取信息
        if not json_data_found:
            extracted_data = self._extract_from_html_enhanced(soup)
        
        # 整合最终结果
        final_title = extracted_data.get('title') or title or "抖音视频"
        final_author = extracted_data.get('author') or author or "未知作者"
        final_description = extracted_data.get('description') or description or ""
        
        # 清理和验证提取结果
        final_title = self._clean_title(final_title)
        
        if not self._is_valid_extraction(final_title, final_author):
            logger.warning("提取结果质量不佳，返回基础信息")
            return None
        
        return {
            'title': final_title,
            'author': final_author,
            'description': final_description,
            'view_count': extracted_data.get('view_count', 0),
            'like_count': extracted_data.get('like_count', 0),
            'comment_count': extracted_data.get('comment_count', 0),
            'share_count': extracted_data.get('share_count', 0),
            'publish_time': extracted_data.get('publish_time', ''),
            'cover_url': extracted_data.get('cover_url', ''),
            'duration': extracted_data.get('duration', 0)
        }
    
    def _extract_video_data_from_json(self, data: dict) -> dict:
        """从JSON数据中提取视频信息"""
        
        def deep_search(obj, keys):
            """深度搜索嵌套字典"""
            if isinstance(obj, dict):
                for key in keys:
                    if key in obj:
                        return obj[key]
                for value in obj.values():
                    result = deep_search(value, keys)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = deep_search(item, keys)
                    if result:
                        return result
            return None
        
        def find_aweme_data(obj):
            """查找aweme数据结构"""
            if isinstance(obj, dict):
                # 检查是否包含视频相关字段
                if 'desc' in obj and 'author' in obj:
                    return obj
                elif 'aweme_detail' in obj:
                    return obj['aweme_detail']
                elif 'aweme_list' in obj and obj['aweme_list']:
                    return obj['aweme_list'][0]
                
                # 递归搜索
                for value in obj.values():
                    result = find_aweme_data(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_aweme_data(item)
                    if result:
                        return result
            return None
        
        extracted = {}
        
        try:
            # 查找aweme数据
            aweme_data = find_aweme_data(data)
            
            if aweme_data:
                # 提取标题/描述
                if 'desc' in aweme_data:
                    extracted['title'] = aweme_data['desc']
                
                # 提取作者信息
                if 'author' in aweme_data:
                    author_info = aweme_data['author']
                    if isinstance(author_info, dict):
                        extracted['author'] = author_info.get('nickname', author_info.get('unique_id', '未知作者'))
                
                # 提取统计信息
                if 'statistics' in aweme_data:
                    stats = aweme_data['statistics']
                    extracted['view_count'] = stats.get('play_count', 0)
                    extracted['like_count'] = stats.get('digg_count', 0)
                    extracted['comment_count'] = stats.get('comment_count', 0)
                    extracted['share_count'] = stats.get('share_count', 0)
                
                # 提取视频信息
                if 'video' in aweme_data:
                    video_info = aweme_data['video']
                    extracted['duration'] = video_info.get('duration', 0)
                    if 'cover' in video_info:
                        extracted['cover_url'] = video_info['cover'].get('url_list', [''])[0]
                
                # 提取发布时间
                if 'create_time' in aweme_data:
                    extracted['publish_time'] = aweme_data['create_time']
                
                logger.info(f"从JSON提取到数据: {list(extracted.keys())}")
        
        except Exception as e:
            logger.warning(f"JSON数据提取异常: {str(e)}")
        
        return extracted
    
    def _extract_from_html_enhanced(self, soup) -> dict:
        """从HTML中提取信息的增强版"""
        extracted = {}
        
        try:
            # 尝试从多种meta标签中提取标题
            title_selectors = [
                'meta[property="og:title"]',
                'meta[name="twitter:title"]',
                'meta[property="twitter:title"]',
                'title'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'title':
                        title = element.get_text().strip()
                    else:
                        title = element.get('content', '').strip()
                    
                    if title and len(title) > 5:  # 过滤过短的标题
                        extracted['title'] = title
                        break
            
            # 尝试从多种meta标签中提取描述
            desc_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]',
                'meta[name="twitter:description"]'
            ]
            
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get('content', '').strip()
                    if description:
                        extracted['description'] = description
                        break
            
            # 尝试提取作者信息
            author_selectors = [
                'meta[name="author"]',
                'meta[property="og:site_name"]',
                '.author-name',
                '.user-name'
            ]
            
            for selector in author_selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        author = element.get('content', '').strip()
                    else:
                        author = element.get_text().strip()
                    
                    if author:
                        extracted['author'] = author
                        break
            
            # 尝试提取封面图片
            image_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]'
            ]
            
            for selector in image_selectors:
                element = soup.select_one(selector)
                if element:
                    image_url = element.get('content', '').strip()
                    if image_url:
                        extracted['cover_url'] = image_url
                        break
            
            logger.info(f"从HTML提取到数据: {list(extracted.keys())}")
        
        except Exception as e:
            logger.warning(f"HTML数据提取异常: {str(e)}")
        
        return extracted
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        if not title:
            return "抖音视频"
        
        # 移除常见的无用前缀和后缀
        clean_patterns = [
            r'^抖音[\s\-–—]*',
            r'[\s\-–—]*抖音$',
            r'^Douyin[\s\-–—]*',
            r'[\s\-–—]*Douyin$',
            r'^\s*-\s*',
            r'\s*-\s*$',
            r'^\s*·\s*',
            r'\s*·\s*$'
        ]
        
        cleaned = title.strip()
        for pattern in clean_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = cleaned.strip()
        
        # 如果清理后为空，返回原标题
        if not cleaned:
            return title.strip()
        
        return cleaned
    
    def _is_valid_extraction(self, title: str, author: str) -> bool:
        """验证提取结果是否有效"""
        # 检查是否包含无效关键词
        invalid_keywords = [
            '验证码', '中间页', '安全验证', '人机验证',
            'captcha', 'verify', '拦截', '隐患',
            '404', 'not found', 'error'
        ]
        
        title_lower = title.lower()
        for keyword in invalid_keywords:
            if keyword in title_lower:
                return False
        
        # 检查标题是否过短或过于通用
        if len(title.strip()) < 3:
            return False
        
        generic_titles = ['抖音', 'douyin', '视频', '短视频', '未知']
        if title.strip().lower() in generic_titles:
            return False
        
        return True
    
    def _get_default_video_info(self) -> Dict[str, Any]:
        """获取默认视频信息"""
        return {
            'title': '抖音视频',
            'author': '未知作者',
            'description': '',
            'view_count': 0,
            'like_count': 0,
            'comment_count': 0,
            'share_count': 0,
            'publish_time': '',
            'cover_url': '',
            'duration': 0
        }
    
    def extract(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """提取抖音视频内容"""
        logger.info(f"开始提取抖音视频: {url}")
        
        # 检查是否为短链接，如果是则提供建议
        if "v.douyin.com" in url:
            logger.warning(f"检测到抖音短链接，可能遇到反爬虫限制: {url}")
            # 仍然尝试处理，但如果失败则提供详细建议
            try:
                # 尝试处理短链接
                video_id = self._extract_video_id(url)
                # 如果成功获取到video_id，继续处理
            except (ValueError, Exception) as e:
                logger.error(f"短链接处理失败: {str(e)}")
                return {
                    "status": "error",
                    "platform": "douyin",
                    "message": "抖音短链接无法解析，请提供完整链接",
                    "suggestion": {
                        "title": "如何获取抖音完整链接",
                        "steps": [
                            "1. 在抖音App中打开要分析的视频",
                            "2. 点击右下角的'分享'按钮", 
                            "3. 选择'复制链接'或'分享到微信/QQ'",
                            "4. 在浏览器中粘贴并访问该链接",
                            "5. 复制浏览器地址栏中的完整URL（包含video/数字ID的长链接）",
                            "6. 使用该完整URL重新尝试解析"
                        ],
                        "example": "完整链接格式示例: https://www.douyin.com/video/1234567890123456789",
                        "note": "由于抖音的反爬虫机制，短链接会被重定向到主页，无法获取具体视频内容。建议提供完整的分享文本作为context_text参数以辅助内容提取。"
                    },
                    "url": url
                }
        
        try:
            # 提取视频ID
            video_id = self._extract_video_id(url)
            logger.info(f"提取到视频ID: {video_id}")
            
            # 获取视频信息
            content_info = self._get_video_info_from_web(url)
            
            # 检查提取结果质量
            if not self._is_valid_extracted_content(content_info):
                logger.warning("提取内容质量不佳，尝试从上下文提取")
                # 如果提取失败且有上下文，尝试从上下文提取
                if context_text.strip():
                    context_extraction = self._extract_from_context(context_text, video_id)
                    content_info.update(context_extraction)
                else:
                    content_info = self._get_default_video_info()
            
            # 构建内容文本
            title = content_info.get('title', '抖音视频')
            author = content_info.get('author', '未知作者')
            description = content_info.get('description', '')
            
            content_text = f"标题: {title}\n作者: {author}\n\n"
            if description:
                content_text += f"视频描述:\n{description}\n\n"
            
            # 添加统计信息
            if content_info.get('view_count', 0) > 0:
                content_text += f"播放量: {content_info['view_count']:,}\n"
            if content_info.get('like_count', 0) > 0:
                content_text += f"点赞数: {content_info['like_count']:,}\n"
            if content_info.get('comment_count', 0) > 0:
                content_text += f"评论数: {content_info['comment_count']:,}\n"
            
            # 构建元数据
            metadata = {
                "title": title,
                "author": author,
                "description": description,
                "video_id": video_id,
                "view_count": content_info.get('view_count', 0),
                "like_count": content_info.get('like_count', 0),
                "comment_count": content_info.get('comment_count', 0),
                "share_count": content_info.get('share_count', 0),
                "publish_time": content_info.get('publish_time', ''),
                "cover_url": content_info.get('cover_url', ''),
                "duration": content_info.get('duration', 0)
            }
            
            # 返回成功结果
            result = self._create_success_result(url, metadata, content_text)
            
            logger.info(f"成功提取抖音视频: {title}")
            return result
            
        except Exception as e:
            error_msg = f"提取抖音视频内容失败: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return self._create_error_result(url, error_msg)
    
    def _is_valid_extracted_content(self, content_info: Dict[str, Any]) -> bool:
        """检查提取的内容是否有效"""
        if not content_info:
            return False
        
        title = content_info.get('title', '')
        
        # 检查是否为低质量内容
        if self._is_low_quality_content(content_info):
            return False
        
        # 检查标题有效性
        return self._is_valid_extraction(title, content_info.get('author', ''))
    
    def _is_low_quality_content(self, content_info: Dict[str, Any]) -> bool:
        """检查是否为低质量内容"""
        title = content_info.get('title', '').lower()
        
        # 低质量标题关键词
        low_quality_keywords = [
            '验证码', '中间页', '安全验证', '拦截',
            'captcha', 'verify', 'error', '404',
            '未知', '默认', 'default'
        ]
        
        for keyword in low_quality_keywords:
            if keyword in title:
                return True
        
        return False
    
    def _extract_from_context(self, context_text: str, video_id: str) -> Dict[str, str]:
        """从上下文文本中提取视频信息"""
        logger.info("尝试从上下文文本提取信息")
        
        extracted = {}
        
        try:
            # 简单的正则提取模式
            # 提取@用户名的内容作为标题
            title_patterns = [
                r'@([^#\n@]+)',  # @后面到#或换行或下一个@的内容
                r'#([^#\n@]+)#?',  # #话题#的内容
                r'"([^"]+)"',  # 引号内的内容
                r'：(.+?)(?:\n|$)',  # 冒号后的内容
            ]
            
            for pattern in title_patterns:
                matches = re.findall(pattern, context_text)
                if matches:
                    title = matches[0].strip()
                    if len(title) > 5 and not any(x in title.lower() for x in ['链接', 'url', 'http']):
                        extracted['title'] = title
                        break
            
            # 提取作者信息
            author_patterns = [
                r'@([a-zA-Z0-9._]+)',  # @用户名格式
                r'作者[:：]\s*([^\n]+)',  # 明确的作者信息
                r'by\s+([^\n]+)',  # 英文by格式
            ]
            
            for pattern in author_patterns:
                matches = re.findall(pattern, context_text)
                if matches:
                    author = matches[0].strip()
                    if len(author) > 2:
                        extracted['author'] = author
                        break
            
            # 使用整个上下文作为描述
            if context_text.strip():
                extracted['description'] = context_text.strip()
            
            logger.info(f"从上下文提取到: {list(extracted.keys())}")
            
        except Exception as e:
            logger.warning(f"上下文提取异常: {str(e)}")
        
        return extracted 