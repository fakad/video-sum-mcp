#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NLP内容处理模块
基于jieba和其他NLP技术，从视频内容中提取关键信息，支持动态知识图谱生成
"""

import jieba
import jieba.analyse
import re
import logging
from typing import List, Dict, Any, Set, Tuple
from collections import Counter, defaultdict

logger = logging.getLogger("video-sum-mcp.nlp_processor")

class ContentAnalyzer:
    """内容分析器：提取关键词、主题、实体等"""
    
    def __init__(self):
        """初始化内容分析器"""
        # 设置jieba
        jieba.setLogLevel(logging.WARNING)  # 减少jieba的日志输出
        
        # 停用词列表
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
            '这个', '这些', '那', '那个', '那些', '什么', '为什么', '怎么', '怎么样', '如何', '可以', '能够', '应该', '需要', '想要', '希望', '觉得', '认为', '知道', '了解', '学习',
            '但是', '因为', '所以', '如果', '虽然', '不过', '或者', '还是', '又', '再', '更', '最', '非常', '特别', '尤其', '特别是', '比如', '例如', '像', '一样', '一种', '各种',
            '视频', '内容', '今天', '大家', '我们', '他们', '它们', '这里', '那里', '现在', '以前', '以后', '时候', '开始', '结束', '继续', '然后', '接下来', '首先', '最后', '总之',
        }
        
        # 实体类型关键词
        self.entity_patterns = {
            'person': ['老师', '专家', '博士', '教授', '创始人', '总裁', 'CEO', 'CTO', '经理', '主管', '同事', '朋友'],
            'organization': ['公司', '企业', '机构', '组织', '团队', '部门', '学校', '大学', '研究院', '实验室'],
            'concept': ['方法', '技巧', '策略', '原理', '理论', '模式', '框架', '体系', '流程', '步骤'],
            'tool': ['工具', '软件', '平台', '系统', '应用', '程序', '设备', '技术'],
            'skill': ['技能', '能力', '经验', '知识', '素质', '水平', '实力', '专业'],
            'goal': ['目标', '目的', '计划', '规划', '愿景', '梦想', '期望', '成果']
        }
        
        # 主题领域关键词
        self.domain_keywords = {
            'technology': {
                'weight': 1.0,
                'keywords': [
                    '编程', '开发', '代码', '程序', '软件', '技术', '算法', '架构', '系统', '平台',
                    'AI', '人工智能', '机器学习', '深度学习', 'Python', 'Java', 'JavaScript',
                    '前端', '后端', '数据库', '网络', '云计算', '大数据', '区块链', '工具', 'IDE',
                    'API', '框架', '库', '开源', 'Github', '版本控制', '测试', '部署', '运维'
                ]
            },
            'business': {
                'weight': 1.0,
                'keywords': [
                    '商业', '创业', '营销', '销售', '客户', '市场', '品牌', '运营', '策略', '商务',
                    '合作', '竞争', '产品', '服务', '用户', '体验', '需求', '痛点', '商业模式',
                    '盈利', '收入', '成本', '效率', '增长', '扩张', '转型', '创新', '商业计划'
                ]
            },
            'finance': {
                'weight': 1.0,
                'keywords': [
                    '金融', '投资', '理财', '股票', '基金', '债券', '证券', '期货', '保险', '银行',
                    '资产', '财富', '收益', '风险', '回报', '资本', '融资', '上市', 'IPO', '估值',
                    '财务', '会计', '预算', '现金流', '利润', '成本', '税务', '审计', '报表'
                ]
            },
            'management': {
                'weight': 1.0,
                'keywords': [
                    '管理', '领导', '团队', '组织', '人事', '招聘', '培训', '绩效', '考核', '激励',
                    '沟通', '协作', '决策', '执行', '监督', '反馈', '改进', '文化', '价值观',
                    '愿景', '使命', '战略', '规划', '目标', 'KPI', 'OKR', '流程', '制度', '规范'
                ]
            },
            'education': {
                'weight': 1.0,
                'keywords': [
                    '教育', '学习', '培训', '课程', '教学', '知识', '技能', '能力', '素质', '方法',
                    '技巧', '经验', '实践', '理论', '原理', '概念', '思维', '认知', '理解', '掌握',
                    '提升', '成长', '发展', '进步', '突破', '创新', '思考', '分析', '解决', '应用'
                ]
            },
            'personal_development': {
                'weight': 1.0,
                'keywords': [
                    '职业', '发展', '成长', '规划', '目标', '习惯', '思维', '心理', '情商', '沟通',
                    '人际关系', '社交', '影响力', '自信', '自律', '时间管理', '效率', '专注',
                    '学习能力', '适应能力', '创造力', '执行力', '领导力', '决策力', '抗压力'
                ]
            },
            'lifestyle': {
                'weight': 0.8,
                'keywords': [
                    '生活', '健康', '饮食', '运动', '健身', '美食', '旅行', '娱乐', '休闲', '兴趣',
                    '爱好', '家庭', '朋友', '社交', '时尚', '购物', '消费', '家居', '装修', '文化'
                ]
            }
        }
        
        # 关系词汇
        self.relation_patterns = {
            'cause_effect': ['因为', '所以', '导致', '造成', '引起', '产生', '带来', '结果', '影响'],
            'comparison': ['比较', '对比', '相比', '不同', '相同', '区别', '差异', '优势', '劣势'],
            'sequence': ['首先', '然后', '接着', '最后', '步骤', '阶段', '过程', '顺序', '流程'],
            'method': ['方法', '技巧', '策略', '方式', '手段', '途径', '办法', '措施', '方案'],
            'importance': ['重要', '关键', '核心', '主要', '关键点', '要点', '重点', '焦点']
        }
    
    def analyze_content(self, title: str, description: str, content: str) -> Dict[str, Any]:
        """
        全面分析内容，提取关键信息
        
        返回:
            包含关键词、主题、实体、关系等信息的字典
        """
        # 合并所有文本
        full_text = f"{title} {description} {content}".strip()
        
        if len(full_text) < 10:
            return {
                'keywords': [],
                'topics': [],
                'entities': {},
                'key_phrases': [],
                'themes': [],
                'domain': 'unknown',
                'summary': '内容过短，无法进行有效分析'
            }
        
        logger.info(f"开始分析内容，文本长度: {len(full_text)}")
        
        # 1. 提取关键词
        keywords = self._extract_keywords(full_text)
        logger.info(f"提取到 {len(keywords)} 个关键词")
        
        # 2. 识别主题领域
        domain, domain_score = self._identify_domain(full_text, keywords)
        logger.info(f"识别主题领域: {domain} (分数: {domain_score:.2f})")
        
        # 3. 提取实体
        entities = self._extract_entities(full_text, keywords)
        logger.info(f"提取到实体: {len(entities)} 类")
        
        # 4. 提取关键短语
        key_phrases = self._extract_key_phrases(full_text, keywords)
        logger.info(f"提取到 {len(key_phrases)} 个关键短语")
        
        # 5. 识别主题
        themes = self._identify_themes(title, full_text, keywords, domain)
        logger.info(f"识别到 {len(themes)} 个主题")
        
        # 6. 生成摘要
        summary = self._generate_summary(title, full_text, keywords, themes)
        
        return {
            'keywords': keywords[:20],  # 限制数量
            'topics': themes,
            'entities': entities,
            'key_phrases': key_phrases[:15],  # 限制数量
            'themes': themes,
            'domain': domain,
            'domain_score': domain_score,
            'summary': summary,
            'text_length': len(full_text),
            'keyword_density': len(keywords) / max(len(full_text.split()), 1) * 100
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        try:
            # 使用TF-IDF提取关键词
            keywords_tfidf = jieba.analyse.extract_tags(
                text, 
                topK=30, 
                withWeight=False,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vd', 'vn', 'a', 'ad', 'an')
            )
            
            # 使用TextRank提取关键词
            keywords_textrank = jieba.analyse.textrank(
                text, 
                topK=20, 
                withWeight=False,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vd', 'vn', 'a', 'ad', 'an')
            )
            
            # 合并去重
            all_keywords = list(set(keywords_tfidf + keywords_textrank))
            
            # 过滤停用词和短词
            filtered_keywords = [
                kw for kw in all_keywords 
                if kw not in self.stop_words and len(kw) >= 2 and not kw.isdigit()
            ]
            
            return filtered_keywords
            
        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            # 简单的词频统计作为备选方案
            words = jieba.lcut(text)
            word_freq = Counter([w for w in words if len(w) >= 2 and w not in self.stop_words])
            return [word for word, freq in word_freq.most_common(20)]
    
    def _identify_domain(self, text: str, keywords: List[str]) -> Tuple[str, float]:
        """识别内容所属的主题领域"""
        domain_scores = {}
        text_lower = text.lower()
        keywords_str = ' '.join(keywords).lower()
        combined_text = f"{text_lower} {keywords_str}"
        
        for domain, config in self.domain_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in config['keywords']:
                # 在文本中查找关键词
                if keyword.lower() in combined_text:
                    score += config['weight']
                    matched_keywords.append(keyword)
            
            # 标题权重加倍
            title_words = text[:100].lower()  # 假设标题在前100字符
            for keyword in config['keywords']:
                if keyword.lower() in title_words:
                    score += config['weight']
            
            domain_scores[domain] = {
                'score': score,
                'matched_keywords': matched_keywords
            }
        
        if not domain_scores or max(d['score'] for d in domain_scores.values()) == 0:
            return 'general', 0.0
        
        best_domain = max(domain_scores, key=lambda x: domain_scores[x]['score'])
        best_score = domain_scores[best_domain]['score']
        
        return best_domain, best_score
    
    def _extract_entities(self, text: str, keywords: List[str]) -> Dict[str, List[str]]:
        """提取命名实体"""
        entities = defaultdict(list)
        
        # 使用关键词匹配提取实体
        for entity_type, patterns in self.entity_patterns.items():
            for keyword in keywords:
                for pattern in patterns:
                    if pattern in keyword or keyword in pattern:
                        if keyword not in entities[entity_type]:
                            entities[entity_type].append(keyword)
        
        # 使用正则表达式提取特定实体
        # 人名模式（简单）
        person_pattern = r'[A-Za-z]+(?:\s+[A-Za-z]+)*|[\u4e00-\u9fff]{2,4}(?:老师|专家|博士|教授|总裁|CEO|经理)'
        persons = re.findall(person_pattern, text)
        entities['person'].extend([p for p in persons if len(p) > 1])
        
        # 公司/组织名称
        org_pattern = r'[\u4e00-\u9fff]+(?:公司|企业|集团|科技|技术|系统|平台|机构|组织|大学|学院)'
        orgs = re.findall(org_pattern, text)
        entities['organization'].extend([o for o in orgs if len(o) > 2])
        
        # 去重并限制数量
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))[:10]
        
        return dict(entities)
    
    def _extract_key_phrases(self, text: str, keywords: List[str]) -> List[str]:
        """提取关键短语"""
        phrases = []
        
        # 基于关键词构建短语
        sentences = re.split(r'[。！？；\n]', text)
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
                
            # 如果句子包含关键词，并且长度适中，就作为关键短语
            sentence_keywords = [kw for kw in keywords if kw in sentence]
            if len(sentence_keywords) >= 1 and 10 <= len(sentence.strip()) <= 100:
                phrases.append(sentence.strip())
        
        # 去重并排序
        phrases = list(set(phrases))
        phrases.sort(key=len)
        
        return phrases[:15]
    
    def _identify_themes(self, title: str, text: str, keywords: List[str], domain: str) -> List[str]:
        """识别内容主题"""
        themes = []
        
        # 基于关键词聚类识别主题
        keyword_groups = self._group_keywords(keywords, domain)
        
        for group_name, group_keywords in keyword_groups.items():
            if len(group_keywords) >= 2:  # 至少2个相关关键词才算一个主题
                theme = f"{group_name}：{', '.join(group_keywords[:5])}"
                themes.append(theme)
        
        # 如果主题过少，基于文本内容添加
        if len(themes) < 3:
            # 查找关系模式
            for relation_type, patterns in self.relation_patterns.items():
                found_patterns = [p for p in patterns if p in text]
                if found_patterns:
                    theme = f"{relation_type.replace('_', '')}相关内容：{', '.join(found_patterns[:3])}"
                    themes.append(theme)
        
        return themes[:8]  # 限制主题数量
    
    def _group_keywords(self, keywords: List[str], domain: str) -> Dict[str, List[str]]:
        """对关键词进行语义分组"""
        groups = defaultdict(list)
        
        # 基于领域知识分组
        if domain in self.domain_keywords:
            domain_kws = self.domain_keywords[domain]['keywords']
            
            # 技术相关
            tech_kws = [kw for kw in keywords if any(tech in kw for tech in ['技术', '方法', '工具', '系统', '平台'])]
            if tech_kws:
                groups['技术方法'] = tech_kws
            
            # 概念相关
            concept_kws = [kw for kw in keywords if any(concept in kw for concept in ['概念', '理论', '原理', '思维', '模式'])]
            if concept_kws:
                groups['核心概念'] = concept_kws
            
            # 实践相关
            practice_kws = [kw for kw in keywords if any(practice in kw for practice in ['实践', '应用', '操作', '执行', '实施'])]
            if practice_kws:
                groups['实践应用'] = practice_kws
            
            # 管理相关
            mgmt_kws = [kw for kw in keywords if any(mgmt in kw for mgmt in ['管理', '策略', '规划', '组织', '团队'])]
            if mgmt_kws:
                groups['管理策略'] = mgmt_kws
        
        # 未分组的关键词
        grouped_kws = set()
        for group_kws in groups.values():
            grouped_kws.update(group_kws)
        
        remaining_kws = [kw for kw in keywords if kw not in grouped_kws]
        if remaining_kws:
            groups['其他关键点'] = remaining_kws
        
        return groups
    
    def _generate_summary(self, title: str, text: str, keywords: List[str], themes: List[str]) -> str:
        """生成内容摘要"""
        try:
            # 提取关键句子
            sentences = re.split(r'[。！？；\n]', text)
            
            # 评分句子重要性
            sentence_scores = []
            for sentence in sentences:
                if len(sentence.strip()) < 10:
                    continue
                
                score = 0
                # 包含关键词加分
                for keyword in keywords[:10]:  # 只考虑前10个关键词
                    if keyword in sentence:
                        score += 1
                
                # 句子长度适中加分
                if 20 <= len(sentence) <= 100:
                    score += 1
                
                # 包含主题词加分
                for theme in themes:
                    theme_words = theme.split('：')[1].split('，') if '：' in theme else []
                    for word in theme_words:
                        if word in sentence:
                            score += 0.5
                
                sentence_scores.append((sentence.strip(), score))
            
            # 选择得分最高的句子
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in sentence_scores[:3] if s[1] > 0]
            
            if top_sentences:
                summary = '。'.join(top_sentences)
                if len(summary) > 200:
                    summary = summary[:200] + '...'
                return summary
            else:
                # 如果没有合适的句子，使用标题和关键词
                return f"主要内容围绕{title}展开，涉及{', '.join(keywords[:5])}等关键概念。"
                
        except Exception as e:
            logger.error(f"摘要生成失败: {str(e)}")
            return f"内容主要讨论{title}相关话题。"


# DynamicKnowledgeGenerator 类已移除，功能已整合到 core.knowledge_graph_processor.KnowledgeGraphProcessor 