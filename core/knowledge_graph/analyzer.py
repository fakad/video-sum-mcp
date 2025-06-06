#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内容分析器模块
负责文本分析、关键词提取、实体识别等功能
"""

import logging
from typing import Dict, Any, List, Tuple
import jieba
import re
from collections import Counter

logger = logging.getLogger("video-sum-mcp.knowledge_graph.analyzer")

class ContentAnalyzer:
    """
    内容分析器
    提供文本分析、关键词提取、实体识别等功能
    """
    
    def __init__(self):
        """初始化分析器"""
        self.domain_keywords = {
            'technology': ['技术', '软件', '开发', '编程', '代码', '系统', '平台', '工具', 'AI', '算法', '数据', '网络'],
            'business': ['商业', '营销', '管理', '创业', '投资', '品牌', '策略', '运营', '市场', '销售'],
            'education': ['教育', '学习', '培训', '课程', '知识', '技能', '方法', '思维', '成长', '发展'],
            'lifestyle': ['生活', '健康', '美食', '旅行', '时尚', '文化', '艺术', '娱乐', '运动', '心理'],
            'finance': ['金融', '投资', '理财', '股票', '基金', '保险', '贷款', '财务', '经济', '货币']
        }
        
    def analyze_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析内容，提取关键信息
        
        参数:
            content_data: 内容数据
            
        返回:
            分析结果字典
        """
        metadata = content_data.get('metadata', {})
        title = metadata.get('title', '未知标题')
        description = metadata.get('description', '')
        content = content_data.get('content', '')
        
        # 合并所有文本用于分析
        full_text = f"{title} {description} {content}".strip()
        
        logger.info(f"开始分析内容: {title}")
        
        # 提取关键词
        keywords = self._extract_keywords(full_text)
        
        # 识别领域
        domain, domain_score = self._identify_domain(full_text, keywords)
        
        # 提取实体
        entities = self._extract_entities(full_text, keywords)
        
        # 提取关键短语
        key_phrases = self._extract_key_phrases(full_text, keywords)
        
        # 识别主题
        themes = self._identify_themes(title, full_text, keywords, domain)
        
        # 分组关键词
        keyword_groups = self._group_keywords(keywords, domain)
        
        # 生成摘要
        summary = self._generate_summary(title, full_text, keywords, themes)
        
        return {
            'title': title,
            'keywords': keywords,
            'domain': domain,
            'domain_score': domain_score,
            'entities': entities,
            'key_phrases': key_phrases,
            'themes': themes,
            'keyword_groups': keyword_groups,
            'summary': summary,
            'text_length': len(full_text)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        try:
            # 使用jieba分词
            words = jieba.lcut(text)
            
            # 过滤无意义词汇
            stop_words = {
                '的', '是', '在', '有', '和', '就', '不', '了', '与', '也', '上', '为', '个', '我', '你', '他', '她', '它',
                '这', '那', '其', '之', '以', '及', '等', '很', '更', '最', '还', '都', '要', '可', '能', '会', '而',
                '但', '或', '如', '若', '因', '由', '对', '从', '到', '把', '被', '让', '使', '给', '向', '往',
                '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '万', '年', '月', '日'
            }
            
            # 过滤并排序
            meaningful_words = []
            for word in words:
                if (len(word) > 1 and 
                    word not in stop_words and 
                    not word.isdigit() and 
                    not re.match(r'^[a-zA-Z]+$', word)):
                    meaningful_words.append(word)
            
            # 统计频率并返回前20个
            word_freq = Counter(meaningful_words)
            return [word for word, freq in word_freq.most_common(20)]
            
        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            return []
    
    def _identify_domain(self, text: str, keywords: List[str]) -> Tuple[str, float]:
        """识别内容领域"""
        domain_scores = {}
        
        for domain, domain_words in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                for domain_word in domain_words:
                    if domain_word in keyword or keyword in domain_word:
                        score += 1
            domain_scores[domain] = score
        
        if not domain_scores or max(domain_scores.values()) == 0:
            return 'general', 0.0
        
        best_domain = max(domain_scores, key=domain_scores.get)
        best_score = domain_scores[best_domain]
        
        return best_domain, best_score / len(keywords) if keywords else 0.0
    
    def _extract_entities(self, text: str, keywords: List[str]) -> Dict[str, List[str]]:
        """提取实体"""
        entities = {
            'person': [],
            'organization': [],
            'concept': [],
            'tool': [],
            'skill': []
        }
        
        # 基于关键词模式识别实体
        for keyword in keywords:
            if any(indicator in keyword for indicator in ['公司', '组织', '机构', '平台']):
                entities['organization'].append(keyword)
            elif any(indicator in keyword for indicator in ['工具', '软件', '系统', '平台']):
                entities['tool'].append(keyword)
            elif any(indicator in keyword for indicator in ['技能', '能力', '方法', '技术']):
                entities['skill'].append(keyword)
            elif any(indicator in keyword for indicator in ['概念', '理论', '模式', '原理']):
                entities['concept'].append(keyword)
        
        # 限制每类实体数量
        for entity_type in entities:
            entities[entity_type] = entities[entity_type][:5]
        
        return entities
    
    def _extract_key_phrases(self, text: str, keywords: List[str]) -> List[str]:
        """提取关键短语"""
        key_phrases = []
        
        try:
            # 简单的关键短语提取：寻找包含关键词的短语
            sentences = re.split(r'[。！？\n]', text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10 or len(sentence) > 100:
                    continue
                
                keyword_count = sum(1 for keyword in keywords if keyword in sentence)
                if keyword_count >= 2:  # 包含至少2个关键词的句子
                    key_phrases.append(sentence)
            
            return key_phrases[:10]
            
        except Exception as e:
            logger.error(f"关键短语提取失败: {str(e)}")
            return []
    
    def _identify_themes(self, title: str, text: str, keywords: List[str], domain: str) -> List[str]:
        """识别主题"""
        themes = []
        
        # 基于标题生成主题
        if title and title != '未知标题':
            themes.append(f"{title}：核心主题")
        
        # 基于领域生成主题
        domain_themes = {
            'technology': '技术创新与应用',
            'business': '商业策略与运营',
            'education': '学习成长与发展',
            'lifestyle': '生活方式与文化',
            'finance': '金融理财与投资'
        }
        
        if domain in domain_themes:
            themes.append(f"{domain_themes[domain]}：领域主题")
        
        # 基于关键词生成主题
        for keyword in keywords[:3]:
            themes.append(f"{keyword}相关应用：实践主题")
        
        return themes[:5]
    
    def _group_keywords(self, keywords: List[str], domain: str) -> Dict[str, List[str]]:
        """对关键词进行分组"""
        groups = {
            'core': [],
            'method': [],
            'tool': [],
            'application': []
        }
        
        for keyword in keywords:
            if any(indicator in keyword for indicator in ['方法', '技巧', '策略', '方式']):
                groups['method'].append(keyword)
            elif any(indicator in keyword for indicator in ['工具', '软件', '平台', '系统']):
                groups['tool'].append(keyword)
            elif any(indicator in keyword for indicator in ['应用', '实践', '使用', '操作']):
                groups['application'].append(keyword)
            else:
                groups['core'].append(keyword)
        
        # 限制每组数量
        for group in groups:
            groups[group] = groups[group][:5]
        
        return groups
    
    def _generate_summary(self, title: str, text: str, keywords: List[str], themes: List[str]) -> str:
        """生成内容摘要"""
        try:
            if not text or len(text) < 50:
                return f"关于{title}的简要内容。"
            
            # 基于关键词和主题生成摘要
            if keywords:
                return f"主要内容围绕{title}展开，涉及{', '.join(keywords[:5])}等关键概念。"
            else:
                return f"内容主要讨论{title}相关话题。"
                
        except Exception as e:
            logger.error(f"摘要生成失败: {str(e)}")
            return f"内容主要讨论{title}相关话题。" 