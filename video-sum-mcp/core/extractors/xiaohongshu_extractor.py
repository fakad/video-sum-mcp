#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书提取器 - 独立的小红书平台内容提取模块
支持OCR图像文字识别，提取图文笔记中的文字信息
"""

import logging
import re
from typing import Dict, Any, Tuple, List
from .base_extractor import BaseExtractor

logger = logging.getLogger("video-sum-mcp.xiaohongshu_extractor")

class XiaohongshuExtractor(BaseExtractor):
    """小红书内容提取器，支持OCR图像文字识别"""
    
    def __init__(self, use_proxy: bool = False):
        super().__init__(use_proxy=use_proxy)
        self._ocr_enabled = False
        self._ocr = None
    
    def _get_platform_name(self) -> str:
        """获取平台名称"""
        return "xiaohongshu"
    
    def get_supported_url_patterns(self) -> list:
        """获取支持的URL模式"""
        return [
            r"^https?://(?:www\.)?xiaohongshu\.com/explore/([a-f0-9]+)",
            r"^https?://(?:www\.)?xiaohongshu\.com/discovery/item/([a-f0-9]+)",
            r"^https?://xhslink\.com/([a-zA-Z0-9]+)"
        ]
    
    def validate_url(self, url: str) -> bool:
        """验证是否为小红书URL"""
        xiaohongshu_patterns = self.get_supported_url_patterns()
        
        for pattern in xiaohongshu_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def _init_ocr(self):
        """初始化OCR功能"""
        if self._ocr_enabled:
            return
            
        try:
            # 尝试导入PaddleOCR
            from paddleocr import PaddleOCR
            # 初始化OCR，使用CPU版本避免依赖问题
            self._ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)
            self._ocr_enabled = True
            logger.info("PaddleOCR初始化成功")
        except ImportError:
            logger.warning("PaddleOCR未安装，将跳过图像文字识别功能")
            self._ocr_enabled = False
        except Exception as e:
            logger.warning(f"PaddleOCR初始化失败: {str(e)}，将跳过图像文字识别功能")
            self._ocr_enabled = False
    
    def _extract_text_from_image(self, image_url: str) -> str:
        """使用OCR从图像中提取文字"""
        if not self._ocr_enabled:
            return ""
        
        try:
            from core.services.safe_crawler import get_safe_requester
            from PIL import Image
            import io
            
            safe_requester = get_safe_requester()
            
            # 下载图像
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Referer': 'https://www.xiaohongshu.com/'
            }
            
            response = safe_requester.get(image_url, headers=headers, timeout=10)
            if not response or response.status_code != 200:
                logger.warning(f"图像下载失败: {image_url}")
                return ""
            
            # 转换为PIL图像
            image = Image.open(io.BytesIO(response.content))
            
            # 使用OCR提取文字
            result = self._ocr.ocr(image, cls=True)
            
            # 提取文字内容
            extracted_texts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text = line[1][0] if line[1] else ""
                        confidence = line[1][1] if line[1] and len(line[1]) > 1 else 0
                        
                        # 只保留置信度较高的文字
                        if confidence > 0.6 and text.strip():
                            extracted_texts.append(text.strip())
            
            ocr_text = " ".join(extracted_texts)
            if ocr_text:
                logger.info(f"从图像提取到文字: {len(ocr_text)}字符")
            return ocr_text
            
        except Exception as e:
            logger.warning(f"OCR文字提取失败: {str(e)}")
            return ""
    
    def _extract_images_text(self, images: List[str]) -> str:
        """批量提取图像中的文字"""
        if not images:
            return ""
        
        # 初始化OCR
        self._init_ocr()
        
        if not self._ocr_enabled:
            return ""
        
        all_texts = []
        
        for i, image_url in enumerate(images[:5]):  # 最多处理5张图片避免过长
            logger.info(f"正在处理第{i+1}张图片...")
            image_text = self._extract_text_from_image(image_url)
            if image_text:
                all_texts.append(f"图片{i+1}: {image_text}")
        
        return "\n".join(all_texts) if all_texts else ""
    
    def _extract_note_id(self, url: str) -> str:
        """提取笔记ID"""
        patterns = [
            r"/explore/([a-f0-9]+)",
            r"/item/([a-f0-9]+)",
            r"xhslink\.com/([a-zA-Z0-9]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                note_id = match.group(1)
                logger.info(f"提取到笔记ID: {note_id}")
                return note_id
        
        logger.error(f"无法从URL中提取笔记ID: {url}")
        raise ValueError(f"无法从URL中提取笔记ID: {url}")
    
    def _detect_content_type(self, url: str, content_info: Dict[str, Any]) -> str:
        """检测内容类型：视频或图文"""
        # 基于内容信息判断
        if content_info.get('video_url'):
            return "video"
        elif content_info.get('images'):
            return "note"
        else:
            # 默认返回笔记类型
            return "note"
    
    def _get_note_info_from_web(self, url: str) -> Dict[str, Any]:
        """从网页版小红书获取笔记信息"""
        from core.services.safe_crawler import get_safe_requester
        from bs4 import BeautifulSoup
        import json
        
        safe_requester = get_safe_requester()
        
        try:
            # 使用移动端User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.xiaohongshu.com/',
            }
            
            response = safe_requester.get(url, headers=headers)
            
            if not response or response.status_code != 200:
                logger.warning(f"请求失败，状态码: {response.status_code if response else 'None'}")
                return self._get_default_note_info()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 尝试从页面标题获取信息
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else "小红书笔记"
            
            # 检查是否为有效页面
            if '小红书' not in title and 'xiaohongshu' not in title.lower():
                logger.warning("可能不是有效的小红书页面")
            
            # 尝试从meta标签获取信息
            description = ""
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                description = desc_tag.get('content', '')
            
            # 尝试从JSON数据中提取详细信息
            extracted_data = {}
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if not script.string:
                    continue
                
                # 查找包含初始状态的JSON数据
                if 'window.__INITIAL_STATE__' in script.string:
                    try:
                        # 提取JSON数据
                        json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', script.string, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            data = json.loads(json_str)
                            
                            # 从JSON中提取笔记信息
                            note_data = self._extract_note_data_from_json(data)
                            if note_data:
                                extracted_data.update(note_data)
                                break
                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(f"解析JSON失败: {str(e)}")
                        continue
            
            # 如果JSON解析失败，尝试从HTML中提取基本信息
            if not extracted_data:
                extracted_data = self._extract_from_html(soup)
            
            # 整合最终结果
            final_title = extracted_data.get('title') or title or "小红书笔记"
            final_author = extracted_data.get('author') or "未知作者"
            final_description = extracted_data.get('description') or description or ""
            
            return {
                'title': final_title,
                'author': final_author,
                'description': final_description,
                'images': extracted_data.get('images', []),
                'video_url': extracted_data.get('video_url', ''),
                'like_count': extracted_data.get('like_count', 0),
                'comment_count': extracted_data.get('comment_count', 0),
                'share_count': extracted_data.get('share_count', 0),
                'collect_count': extracted_data.get('collect_count', 0),
                'tags': extracted_data.get('tags', []),
                'publish_time': extracted_data.get('publish_time', '')
            }
            
        except Exception as e:
            logger.error(f"从网页提取小红书内容失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_default_note_info()
    
    def _extract_note_data_from_json(self, data: dict) -> dict:
        """从JSON数据中提取笔记信息"""
        extracted = {}
        
        try:
            # 递归搜索笔记数据
            def find_note_data(obj, path=""):
                if isinstance(obj, dict):
                    # 查找包含笔记信息的对象
                    if 'title' in obj and 'user' in obj:
                        return obj
                    elif 'noteDetailMap' in obj:
                        note_map = obj['noteDetailMap']
                        if note_map:
                            # 获取第一个笔记的详细信息
                            first_note = next(iter(note_map.values()), {})
                            return first_note.get('note', {})
                    
                    # 递归搜索
                    for key, value in obj.items():
                        result = find_note_data(value, f"{path}.{key}")
                        if result:
                            return result
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        result = find_note_data(item, f"{path}[{i}]")
                        if result:
                            return result
                return None
            
            note_data = find_note_data(data)
            
            if note_data:
                # 提取标题
                if 'title' in note_data:
                    extracted['title'] = note_data['title']
                
                # 提取作者信息
                if 'user' in note_data:
                    user_info = note_data['user']
                    extracted['author'] = user_info.get('nickname', user_info.get('id', '未知作者'))
                
                # 提取描述
                if 'desc' in note_data:
                    extracted['description'] = note_data['desc']
                
                # 提取图片
                if 'imageList' in note_data:
                    images = []
                    for img in note_data['imageList']:
                        if 'urlDefault' in img:
                            images.append(img['urlDefault'])
                    extracted['images'] = images
                
                # 提取视频信息
                if 'video' in note_data:
                    video_info = note_data['video']
                    if 'consumer' in video_info and 'originVideoKey' in video_info['consumer']:
                        extracted['video_url'] = video_info['consumer']['originVideoKey']
                
                # 提取互动数据
                if 'interactInfo' in note_data:
                    interact = note_data['interactInfo']
                    extracted['like_count'] = interact.get('likedCount', 0)
                    extracted['comment_count'] = interact.get('commentCount', 0)
                    extracted['share_count'] = interact.get('shareCount', 0)
                    extracted['collect_count'] = interact.get('collectedCount', 0)
                
                # 提取标签
                if 'tagList' in note_data:
                    tags = []
                    for tag in note_data['tagList']:
                        if 'name' in tag:
                            tags.append(tag['name'])
                    extracted['tags'] = tags
                
                # 提取发布时间
                if 'time' in note_data:
                    extracted['publish_time'] = note_data['time']
                
                logger.info(f"从JSON提取到数据: {list(extracted.keys())}")
        
        except Exception as e:
            logger.warning(f"JSON数据提取异常: {str(e)}")
        
        return extracted
    
    def _extract_from_html(self, soup) -> dict:
        """从HTML中提取基本信息"""
        extracted = {}
        
        try:
            # 提取标题
            title_selectors = [
                'meta[property="og:title"]',
                'meta[name="twitter:title"]',
                'title'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'title':
                        title = element.get_text().strip()
                    else:
                        title = element.get('content', '').strip()
                    
                    if title and '小红书' not in title:
                        extracted['title'] = title
                        break
            
            # 提取描述
            desc_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]'
            ]
            
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get('content', '').strip()
                    if description:
                        extracted['description'] = description
                        break
            
            # 提取图片
            img_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]'
            ]
            
            images = []
            for selector in img_selectors:
                elements = soup.select(selector)
                for element in elements:
                    img_url = element.get('content', '').strip()
                    if img_url and img_url not in images:
                        images.append(img_url)
            
            if images:
                extracted['images'] = images
            
            logger.info(f"从HTML提取到数据: {list(extracted.keys())}")
        
        except Exception as e:
            logger.warning(f"HTML数据提取异常: {str(e)}")
        
        return extracted
    
    def _get_default_note_info(self) -> Dict[str, Any]:
        """获取默认笔记信息"""
        return {
            'title': '小红书笔记',
            'author': '未知作者',
            'description': '',
            'images': [],
            'video_url': '',
            'like_count': 0,
            'comment_count': 0,
            'share_count': 0,
            'collect_count': 0,
            'tags': [],
            'publish_time': ''
        }
    
    def _extract_from_context(self, context_text: str, note_id: str) -> Dict[str, Any]:
        """从上下文文本中提取笔记信息"""
        extracted = {}
        
        try:
            lines = context_text.split('\n')
            
            # 尝试从上下文中提取标题和描述
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 查找标题相关信息
                if any(keyword in line for keyword in ['标题', 'title', '主题']):
                    # 提取冒号后的内容作为标题
                    if ':' in line or '：' in line:
                        separator = ':' if ':' in line else '：'
                        title = line.split(separator, 1)[-1].strip()
                        if title and len(title) > 2:
                            extracted['title'] = title
                
                # 查找作者信息
                if any(keyword in line for keyword in ['作者', 'author', '博主']):
                    if ':' in line or '：' in line:
                        separator = ':' if ':' in line else '：'
                        author = line.split(separator, 1)[-1].strip()
                        if author and len(author) > 1:
                            extracted['author'] = author
                
                # 将长段文本作为描述
                if len(line) > 20 and not any(char in line for char in [':', '：', '#']):
                    if 'description' not in extracted:
                        extracted['description'] = line
                    else:
                        extracted['description'] += '\n' + line
            
            logger.info(f"从上下文提取到数据: {list(extracted.keys())}")
            
        except Exception as e:
            logger.warning(f"上下文数据提取异常: {str(e)}")
        
        return extracted
    
    def extract(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """提取小红书笔记内容，包括OCR图像文字识别"""
        logger.info(f"开始提取小红书笔记: {url}")
        
        try:
            # 提取笔记ID
            note_id = self._extract_note_id(url)
            logger.info(f"提取到笔记ID: {note_id}")
            
            # 获取笔记信息
            content_info = self._get_note_info_from_web(url)
            
            # 检测内容类型
            content_type = self._detect_content_type(url, content_info)
            
            # 检查提取结果质量
            if self._is_low_quality_note_content(content_info):
                logger.warning("提取内容质量不佳，尝试从上下文提取")
                if context_text.strip():
                    context_extraction = self._extract_from_context(context_text, note_id)
                    content_info.update(context_extraction)
                else:
                    content_info = self._get_default_note_info()
            
            # 提取图像中的文字（新增OCR功能）
            images_text = ""
            if content_info.get('images'):
                logger.info(f"发现{len(content_info['images'])}张图片，开始OCR文字识别...")
                images_text = self._extract_images_text(content_info['images'])
            
            # 构建内容文本
            title = content_info.get('title', '小红书笔记')
            author = content_info.get('author', '未知作者')
            description = content_info.get('description', '')
            tags = content_info.get('tags', [])
            
            content_text = f"标题: {title}\n作者: {author}\n\n"
            
            if description:
                content_text += f"笔记描述:\n{description}\n\n"
            
            if tags:
                content_text += f"标签: {', '.join(tags)}\n\n"
            
            # 添加OCR提取的图像文字
            if images_text:
                content_text += f"图片文字内容:\n{images_text}\n\n"
            
            # 添加统计信息
            if content_info.get('like_count', 0) > 0:
                content_text += f"点赞数: {content_info['like_count']:,}\n"
            if content_info.get('collect_count', 0) > 0:
                content_text += f"收藏数: {content_info['collect_count']:,}\n"
            if content_info.get('comment_count', 0) > 0:
                content_text += f"评论数: {content_info['comment_count']:,}\n"
            
            # 构建元数据
            metadata = {
                "title": title,
                "author": author,
                "description": description,
                "note_id": note_id,
                "content_type": content_type,
                "images": content_info.get('images', []),
                "images_text": images_text,  # 新增图像文字字段
                "video_url": content_info.get('video_url', ''),
                "like_count": content_info.get('like_count', 0),
                "collect_count": content_info.get('collect_count', 0),
                "comment_count": content_info.get('comment_count', 0),
                "share_count": content_info.get('share_count', 0),
                "tags": tags,
                "publish_time": content_info.get('publish_time', '')
            }
            
            # 返回成功结果
            result = self._create_success_result(url, metadata, content_text)
            
            logger.info(f"成功提取小红书笔记: {title}")
            if images_text:
                logger.info(f"OCR提取到图像文字: {len(images_text)}字符")
            
            return result
            
        except Exception as e:
            error_msg = f"提取小红书笔记内容失败: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return self._create_error_result(url, error_msg)
    
    def _is_low_quality_note_content(self, content_info: Dict[str, Any]) -> bool:
        """检查是否为低质量笔记内容"""
        title = content_info.get('title', '').lower()
        
        # 低质量标题关键词
        low_quality_keywords = [
            '小红书', 'xiaohongshu', '未知', '默认',
            'error', '404', '页面'
        ]
        
        for keyword in low_quality_keywords:
            if keyword in title:
                return True
        
        # 检查是否有实际内容
        if not content_info.get('description') and not content_info.get('images'):
            return True
        
        return False 