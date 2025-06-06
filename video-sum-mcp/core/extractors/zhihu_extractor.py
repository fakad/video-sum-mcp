#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知乎提取器 - 独立的知乎平台内容提取模块
"""

import logging
import re
from typing import Dict, Any, Tuple
from .base_extractor import BaseExtractor

logger = logging.getLogger("video-sum-mcp.zhihu_extractor")

class ZhihuExtractor(BaseExtractor):
    """知乎内容提取器"""
    
    def _get_platform_name(self) -> str:
        """获取平台名称"""
        return "zhihu"
    
    def get_supported_url_patterns(self) -> list:
        """获取支持的URL模式"""
        return [
            r"^https?://(?:www\.)?zhihu\.com/question/(\d+)/answer/(\d+)",
            r"^https?://(?:www\.)?zhihu\.com/question/(\d+)",
            r"^https?://zhuanlan\.zhihu\.com/p/(\d+)",
            r"^https?://(?:www\.)?zhihu\.com/pin/(\d+)"
        ]
    
    def validate_url(self, url: str) -> bool:
        """验证是否为知乎URL"""
        zhihu_patterns = self.get_supported_url_patterns()
        
        for pattern in zhihu_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def _extract_content_id(self, url: str) -> Tuple[str, str]:
        """提取内容ID和类型"""
        # 回答
        answer_match = re.search(r'/question/(\d+)/answer/(\d+)', url)
        if answer_match:
            question_id, answer_id = answer_match.groups()
            return f"{question_id}-{answer_id}", "answer"
        
        # 问题
        question_match = re.search(r'/question/(\d+)', url)
        if question_match:
            question_id = question_match.group(1)
            return question_id, "question"
        
        # 专栏文章
        zhuanlan_match = re.search(r'/p/(\d+)', url)
        if zhuanlan_match:
            article_id = zhuanlan_match.group(1)
            return article_id, "article"
        
        # 想法
        pin_match = re.search(r'/pin/(\d+)', url)
        if pin_match:
            pin_id = pin_match.group(1)
            return pin_id, "pin"
        
        logger.error(f"无法从URL中提取内容ID: {url}")
        raise ValueError(f"无法从URL中提取内容ID: {url}")
    
    def _get_content_info_from_web(self, url: str, content_type: str) -> Dict[str, Any]:
        """从网页版知乎获取内容信息"""
        from core.services.safe_crawler import get_safe_requester
        from bs4 import BeautifulSoup
        import json
        
        safe_requester = get_safe_requester()
        
        try:
            # 使用桌面端User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.zhihu.com/',
            }
            
            response = safe_requester.get(url, headers=headers)
            
            if not response or response.status_code != 200:
                logger.warning(f"请求失败，状态码: {response.status_code if response else 'None'}")
                return self._get_default_content_info(content_type)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 尝试从页面标题获取信息
            title_tag = soup.find('title')
            title = title_tag.text if title_tag else "知乎内容"
            
            # 检查是否为有效页面
            if '知乎' not in title and 'zhihu' not in title.lower():
                logger.warning("可能不是有效的知乎页面")
            
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
                            
                            # 从JSON中提取内容信息
                            content_data = self._extract_content_data_from_json(data, content_type)
                            if content_data:
                                extracted_data.update(content_data)
                                break
                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(f"解析JSON失败: {str(e)}")
                        continue
            
            # 如果JSON解析失败，尝试从HTML中提取基本信息
            if not extracted_data:
                extracted_data = self._extract_from_html(soup, content_type)
            
            # 整合最终结果
            final_title = extracted_data.get('title') or title or "知乎内容"
            final_author = extracted_data.get('author') or "未知作者"
            final_content = extracted_data.get('content') or description or ""
            
            return {
                'title': final_title,
                'author': final_author,
                'content': final_content,
                'excerpt': extracted_data.get('excerpt', ''),
                'voteup_count': extracted_data.get('voteup_count', 0),
                'comment_count': extracted_data.get('comment_count', 0),
                'view_count': extracted_data.get('view_count', 0),
                'created_time': extracted_data.get('created_time', ''),
                'updated_time': extracted_data.get('updated_time', ''),
                'topics': extracted_data.get('topics', [])
            }
            
        except Exception as e:
            logger.error(f"从网页提取知乎内容失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_default_content_info(content_type)
    
    def _extract_content_data_from_json(self, data: dict, content_type: str) -> dict:
        """从JSON数据中提取内容信息"""
        extracted = {}
        
        try:
            # 根据内容类型查找不同的数据结构
            if content_type == "answer":
                # 查找回答数据
                answers = self._find_in_data(data, ['answers'])
                if answers:
                    # 获取第一个回答的信息
                    first_answer = next(iter(answers.values()), {})
                    if first_answer:
                        extracted['title'] = first_answer.get('question', {}).get('title', '')
                        extracted['content'] = first_answer.get('content', '')
                        extracted['excerpt'] = first_answer.get('excerpt', '')
                        extracted['voteup_count'] = first_answer.get('voteup_count', 0)
                        extracted['comment_count'] = first_answer.get('comment_count', 0)
                        
                        # 提取作者信息
                        author_info = first_answer.get('author', {})
                        extracted['author'] = author_info.get('name', '未知作者')
                        
                        # 提取时间信息
                        extracted['created_time'] = first_answer.get('created_time', '')
                        extracted['updated_time'] = first_answer.get('updated_time', '')
            
            elif content_type == "question":
                # 查找问题数据
                questions = self._find_in_data(data, ['questions'])
                if questions:
                    first_question = next(iter(questions.values()), {})
                    if first_question:
                        extracted['title'] = first_question.get('title', '')
                        extracted['content'] = first_question.get('detail', '')
                        extracted['excerpt'] = first_question.get('excerpt', '')
                        extracted['view_count'] = first_question.get('visit_count', 0)
                        extracted['comment_count'] = first_question.get('comment_count', 0)
                        
                        # 提取作者信息
                        author_info = first_question.get('author', {})
                        extracted['author'] = author_info.get('name', '未知作者')
                        
                        # 提取话题信息
                        topics = first_question.get('topics', [])
                        extracted['topics'] = [topic.get('name', '') for topic in topics]
                        
                        # 提取时间信息
                        extracted['created_time'] = first_question.get('created', '')
                        extracted['updated_time'] = first_question.get('updated_time', '')
            
            elif content_type == "article":
                # 查找专栏文章数据
                articles = self._find_in_data(data, ['articles'])
                if articles:
                    first_article = next(iter(articles.values()), {})
                    if first_article:
                        extracted['title'] = first_article.get('title', '')
                        extracted['content'] = first_article.get('content', '')
                        extracted['excerpt'] = first_article.get('excerpt', '')
                        extracted['voteup_count'] = first_article.get('voteup_count', 0)
                        extracted['comment_count'] = first_article.get('comment_count', 0)
                        
                        # 提取作者信息
                        author_info = first_article.get('author', {})
                        extracted['author'] = author_info.get('name', '未知作者')
                        
                        # 提取时间信息
                        extracted['created_time'] = first_article.get('created', '')
                        extracted['updated_time'] = first_article.get('updated', '')
            
            elif content_type == "pin":
                # 查找想法数据
                pins = self._find_in_data(data, ['pins'])
                if pins:
                    first_pin = next(iter(pins.values()), {})
                    if first_pin:
                        extracted['title'] = "知乎想法"
                        extracted['content'] = first_pin.get('content', '')
                        extracted['excerpt'] = first_pin.get('excerpt_new', '')
                        extracted['voteup_count'] = first_pin.get('like_count', 0)
                        extracted['comment_count'] = first_pin.get('comment_count', 0)
                        
                        # 提取作者信息
                        author_info = first_pin.get('author', {})
                        extracted['author'] = author_info.get('name', '未知作者')
                        
                        # 提取时间信息
                        extracted['created_time'] = first_pin.get('created', '')
                        extracted['updated_time'] = first_pin.get('updated', '')
            
            logger.info(f"从JSON提取到数据: {list(extracted.keys())}")
        
        except Exception as e:
            logger.warning(f"JSON数据提取异常: {str(e)}")
        
        return extracted
    
    def _find_in_data(self, data: dict, keys: list) -> dict:
        """在嵌套数据中查找指定键的值"""
        def search_recursive(obj, target_keys):
            if isinstance(obj, dict):
                for key in target_keys:
                    if key in obj:
                        return obj[key]
                for value in obj.values():
                    result = search_recursive(value, target_keys)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search_recursive(item, target_keys)
                    if result:
                        return result
            return None
        
        return search_recursive(data, keys) or {}
    
    def _extract_from_html(self, soup, content_type: str) -> dict:
        """从HTML中提取基本信息"""
        extracted = {}
        
        try:
            # 提取标题
            title_selectors = [
                'meta[property="og:title"]',
                'meta[name="twitter:title"]',
                'h1.QuestionHeader-title',
                'h1',
                'title'
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'title':
                        title = element.get_text().strip()
                    elif element.name in ['h1']:
                        title = element.get_text().strip()
                    else:
                        title = element.get('content', '').strip()
                    
                    if title and '知乎' not in title:
                        extracted['title'] = title
                        break
            
            # 提取描述/内容
            content_selectors = [
                'meta[property="og:description"]',
                'meta[name="description"]',
                '.RichContent-inner',
                '.QuestionRichText',
                '.Post-RichText'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        content = element.get('content', '').strip()
                    else:
                        content = element.get_text().strip()
                    
                    if content:
                        extracted['content'] = content
                        break
            
            # 提取作者信息
            author_selectors = [
                '.AuthorInfo-name a',
                '.UserLink-link',
                '.author-link-line a'
            ]
            
            for selector in author_selectors:
                element = soup.select_one(selector)
                if element:
                    author = element.get_text().strip()
                    if author:
                        extracted['author'] = author
                        break
            
            logger.info(f"从HTML提取到数据: {list(extracted.keys())}")
        
        except Exception as e:
            logger.warning(f"HTML数据提取异常: {str(e)}")
        
        return extracted
    
    def _get_default_content_info(self, content_type: str) -> Dict[str, Any]:
        """获取默认内容信息"""
        type_names = {
            "answer": "知乎回答",
            "question": "知乎问题",
            "article": "知乎专栏",
            "pin": "知乎想法"
        }
        
        return {
            'title': type_names.get(content_type, '知乎内容'),
            'author': '未知作者',
            'content': '',
            'excerpt': '',
            'voteup_count': 0,
            'comment_count': 0,
            'view_count': 0,
            'created_time': '',
            'updated_time': '',
            'topics': []
        }
    
    def extract(self, url: str, context_text: str = "") -> Dict[str, Any]:
        """提取知乎内容"""
        logger.info(f"开始提取知乎内容: {url}")
        
        try:
            # 提取内容ID和类型
            content_id, content_type = self._extract_content_id(url)
            logger.info(f"提取到内容ID: {content_id}, 类型: {content_type}")
            
            # 获取内容信息
            content_info = self._get_content_info_from_web(url, content_type)
            
            # 检查提取结果质量
            if self._is_low_quality_zhihu_content(content_info):
                logger.warning("提取内容质量不佳")
                if context_text.strip():
                    # 如果有上下文，可以尝试提取基础信息
                    content_info['title'] = f"知乎{content_type}（来自上下文）"
                    content_info['content'] = context_text.strip()
            
            # 构建内容文本
            title = content_info.get('title', '知乎内容')
            author = content_info.get('author', '未知作者')
            content = content_info.get('content', '')
            excerpt = content_info.get('excerpt', '')
            
            content_text = f"标题: {title}\n作者: {author}\n类型: {content_type}\n\n"
            
            if excerpt and excerpt != content:
                content_text += f"摘要:\n{excerpt}\n\n"
            
            if content:
                content_text += f"内容:\n{content}\n\n"
            
            # 添加话题信息
            topics = content_info.get('topics', [])
            if topics:
                content_text += f"相关话题: {', '.join(topics)}\n"
            
            # 添加互动数据
            if content_info.get('voteup_count', 0) > 0:
                content_text += f"赞同数: {content_info['voteup_count']:,}\n"
            if content_info.get('comment_count', 0) > 0:
                content_text += f"评论数: {content_info['comment_count']:,}\n"
            if content_info.get('view_count', 0) > 0:
                content_text += f"浏览量: {content_info['view_count']:,}\n"
            
            # 构建元数据
            metadata = {
                "title": title,
                "author": author,
                "content": content,
                "excerpt": excerpt,
                "content_id": content_id,
                "content_type": content_type,
                "voteup_count": content_info.get('voteup_count', 0),
                "comment_count": content_info.get('comment_count', 0),
                "view_count": content_info.get('view_count', 0),
                "created_time": content_info.get('created_time', ''),
                "updated_time": content_info.get('updated_time', ''),
                "topics": topics
            }
            
            # 返回成功结果
            result = self._create_success_result(url, metadata, content_text)
            
            logger.info(f"成功提取知乎内容: {title}")
            return result
            
        except Exception as e:
            error_msg = f"提取知乎内容失败: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return self._create_error_result(url, error_msg)
    
    def _is_low_quality_zhihu_content(self, content_info: Dict[str, Any]) -> bool:
        """检查是否为低质量知乎内容"""
        title = content_info.get('title', '').lower()
        
        # 低质量标题关键词
        low_quality_keywords = [
            '知乎', 'zhihu', '未知', '默认',
            'error', '404', '页面'
        ]
        
        for keyword in low_quality_keywords:
            if keyword in title:
                return True
        
        # 检查是否有实际内容
        if not content_info.get('content') and not content_info.get('excerpt'):
            return True
        
        return False 