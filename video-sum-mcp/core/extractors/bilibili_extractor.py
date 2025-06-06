#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
B站(Bilibili)视频提取器 - 独立的B站平台内容提取模块
"""

import logging
import re
from typing import Dict, Any
from .base_extractor import BaseExtractor

logger = logging.getLogger("video-sum-mcp.bilibili_extractor")

class BilibiliExtractor(BaseExtractor):
    """哔哩哔哩(Bilibili)视频提取器"""
    
    def _get_platform_name(self) -> str:
        """获取平台名称"""
        return "bilibili"
    
    def get_supported_url_patterns(self) -> list:
        """获取支持的URL模式"""
        return [
            r"^https?://(?:www\.)?bilibili\.com/video/([a-zA-Z0-9]+)",
            r"^https?://b23\.tv/([a-zA-Z0-9]+)"
        ]
    
    def validate_url(self, url: str) -> bool:
        """验证是否为Bilibili URL"""
        bilibili_patterns = self.get_supported_url_patterns()
        
        for pattern in bilibili_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def _extract_bvid(self, url: str) -> str:
        """提取BV号"""
        # 直接匹配 BV 开头的ID
        match = re.search(r'BV([a-zA-Z0-9]+)', url)
        if match:
            return f"BV{match.group(1)}"
        
        # 匹配短链接
        if "b23.tv" in url:
            # 对于短链接，需要解析重定向后的URL
            import requests
            try:
                response = requests.head(url, allow_redirects=True)
                if response.status_code == 200:
                    redirect_url = response.url
                    return self._extract_bvid(redirect_url)
            except Exception as e:
                logger.error(f"解析短链接失败: {str(e)}")
        
        logger.error(f"无法从URL中提取BV号: {url}")
        raise ValueError(f"无法从URL中提取BV号: {url}")
    
    def extract(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """提取Bilibili视频内容"""
        logger.info(f"开始提取Bilibili视频: {url}")
        
        try:
            # 提取BV号
            bvid = self._extract_bvid(url)
            logger.info(f"提取到BV号: {bvid}")
            
            # 使用bilibili-api-python库提取视频信息
            from bilibili_api import video, sync
            
            # 创建视频对象
            v = video.Video(bvid=bvid)
            
            # 获取视频基本信息
            info = sync(v.get_info())
            
            # 提取视频信息
            title = info.get('title', '未知标题')
            author = info.get('owner', {}).get('name', '未知作者')
            description = info.get('desc', '')
            duration = info.get('duration', 0)
            
            logger.info(f"视频标题: {title}")
            logger.info(f"视频作者: {author}")
            logger.info(f"视频时长: {duration}秒")
            
            # 获取标签
            tags = []
            try:
                tag_info = sync(v.get_tags())
                for tag in tag_info:
                    tags.append(tag.get('tag_name', ''))
                logger.info(f"提取到{len(tags)}个标签")
            except Exception as e:
                logger.warning(f"获取标签失败: {str(e)}")
            
            # 构建内容文本
            content_text = f"标题: {title}\n作者: {author}\n\n"
            content_text += f"简介:\n{description}\n\n"
            if tags:
                content_text += f"标签: {', '.join(tags)}\n"
            
            # 尝试获取视频分P信息
            try:
                pages = sync(v.get_pages())
                if len(pages) > 1:
                    content_text += "\n分P信息:\n"
                    for page in pages:
                        content_text += f"P{page.get('page', 0)}: {page.get('part', '')} ({page.get('duration', 0)}秒)\n"
            except Exception as e:
                logger.warning(f"获取分P信息失败: {str(e)}")
            
            # 构建元数据
            metadata = {
                "title": title,
                "author": author,
                "description": description,
                "duration": duration,
                "bvid": bvid,
                "pubdate": info.get('pubdate', 0),
                "view_count": info.get('stat', {}).get('view', 0),
                "cover_url": info.get('pic', ''),
                "tags": tags
            }
            
            # 返回成功结果
            result = self._create_success_result(url, metadata, content_text)
            
            logger.info(f"成功提取Bilibili视频: {title}")
            return result
            
        except Exception as e:
            error_msg = f"提取Bilibili视频内容失败: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return self._create_error_result(url, error_msg) 