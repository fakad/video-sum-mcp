#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识图谱生成器模块
负责生成知识图谱的结构化表示
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from .utils import KnowledgeGraphUtils

logger = logging.getLogger("video-sum-mcp.knowledge_graph.generator")

class KnowledgeGraphGenerator:
    """
    知识图谱生成器
    根据分析结果生成结构化的知识图谱
    """
    
    def __init__(self):
        """初始化生成器"""
        pass
        
    def generate_knowledge_graph(self, analyzed_data: Dict[str, Any], original_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成知识图谱
        
        参数:
            analyzed_data: 分析结果
            original_content: 原始内容数据
            
        返回:
            知识图谱字典
        """
        logger.info(f"开始生成知识图谱: {analyzed_data.get('title', '未知标题')}")
        
        knowledge_graph = {
            'metadata': self._generate_metadata(analyzed_data, original_content),
            'content_analysis': self._generate_content_analysis(analyzed_data),
            'knowledge_structure': self._generate_knowledge_structure(analyzed_data),
            'relationships': self._generate_relationships(analyzed_data),
            'applications': self._generate_applications(analyzed_data),
            'development_path': self._generate_development_path(analyzed_data)
        }
        
        logger.info(f"知识图谱生成完成: {knowledge_graph['metadata']['title']}")
        return knowledge_graph
    
    def _generate_metadata(self, analyzed_data: Dict[str, Any], original_content: Dict[str, Any]) -> Dict[str, Any]:
        """生成元数据"""
        original_metadata = original_content.get('metadata', {})
        
        metadata = {
            'title': analyzed_data.get('title', '未知标题'),
            'source': original_metadata.get('source_platform', '未知平台'),
            'author': original_metadata.get('author', '未知作者'),
            'created_time': original_metadata.get('created_time', datetime.now().isoformat()),
            'content_type': original_metadata.get('content_type', 'text'),
            'domain': analyzed_data.get('domain', 'general'),
            'domain_confidence': analyzed_data.get('domain_score', 0.0),
            'language': 'zh-CN',
            'tags': analyzed_data.get('keywords', [])[:10],
            'difficulty_level': self._assess_difficulty(analyzed_data),
            'estimated_reading_time': self._estimate_reading_time(analyzed_data.get('text_length', 0))
        }
        
        return metadata
    
    def _generate_content_analysis(self, analyzed_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成内容分析"""
        return {
            'summary': analyzed_data.get('summary', ''),
            'main_themes': analyzed_data.get('themes', []),
            'key_concepts': analyzed_data.get('keywords', [])[:10],
            'entities': analyzed_data.get('entities', {}),
            'key_phrases': analyzed_data.get('key_phrases', []),
            'keyword_groups': analyzed_data.get('keyword_groups', {}),
            'content_structure': {
                'main_points': self._extract_main_points(analyzed_data),
                'supporting_details': self._extract_supporting_details(analyzed_data),
                'examples': self._extract_examples(analyzed_data)
            }
        }
    
    def _generate_knowledge_structure(self, analyzed_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成知识结构"""
        keywords = analyzed_data.get('keywords', [])
        entities = analyzed_data.get('entities', {})
        themes = analyzed_data.get('themes', [])
        
        knowledge_structure = {
            'core_concepts': {
                'primary': keywords[:5] if keywords else [],
                'secondary': keywords[5:10] if len(keywords) > 5 else [],
                'tertiary': keywords[10:15] if len(keywords) > 10 else []
            },
            'concept_hierarchy': self._build_concept_hierarchy(keywords, entities),
            'knowledge_domains': self._categorize_knowledge_domains(analyzed_data),
            'learning_objectives': self._generate_learning_objectives(themes, keywords),
            'prerequisites': self._identify_prerequisites(analyzed_data),
            'related_topics': self._suggest_related_topics(keywords, analyzed_data.get('domain', 'general'))
        }
        
        return knowledge_structure
    
    def _generate_relationships(self, analyzed_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成关系网络"""
        keywords = analyzed_data.get('keywords', [])
        entities = analyzed_data.get('entities', {})
        
        relationships = {
            'concept_relationships': self._build_concept_relationships(keywords),
            'entity_relationships': self._build_entity_relationships(entities),
            'hierarchical_relationships': self._build_hierarchical_relationships(keywords, entities),
            'functional_relationships': self._build_functional_relationships(analyzed_data),
            'dependency_graph': self._build_dependency_graph(keywords, entities)
        }
        
        return relationships
    
    def _generate_applications(self, analyzed_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成应用场景"""
        domain = analyzed_data.get('domain', 'general')
        keywords = analyzed_data.get('keywords', [])
        entities = analyzed_data.get('entities', {})
        
        applications = {
            'practical_uses': self._identify_practical_uses(keywords, domain),
            'use_cases': self._generate_use_cases(keywords, entities, domain),
            'implementation_methods': self._suggest_implementation_methods(keywords, domain),
            'tools_and_resources': entities.get('tool', []) + entities.get('organization', []),
            'success_metrics': self._define_success_metrics(domain, keywords),
            'common_challenges': self._identify_common_challenges(domain, keywords)
        }
        
        return applications
    
    def _generate_development_path(self, analyzed_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成发展路径"""
        keywords = analyzed_data.get('keywords', [])
        domain = analyzed_data.get('domain', 'general')
        
        development_path = {
            'learning_sequence': self._create_learning_sequence(keywords, domain),
            'skill_progression': self._map_skill_progression(keywords, domain),
            'milestones': self._define_milestones(keywords, domain),
            'resources': self._recommend_resources(domain, keywords),
            'next_steps': self._suggest_next_steps(keywords, domain),
            'advanced_topics': self._identify_advanced_topics(keywords, domain)
        }
        
        return development_path
    
    def _assess_difficulty(self, analyzed_data: Dict[str, Any]) -> str:
        """评估内容难度"""
        keywords = analyzed_data.get('keywords', [])
        entities = analyzed_data.get('entities', {})
        
        # 基于关键词复杂度和实体数量评估
        complexity_indicators = sum(1 for keyword in keywords if any(
            indicator in keyword for indicator in ['高级', '复杂', '深入', '专业', '技术']
        ))
        
        total_entities = sum(len(entity_list) for entity_list in entities.values())
        
        if complexity_indicators > 3 or total_entities > 15:
            return 'advanced'
        elif complexity_indicators > 1 or total_entities > 8:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _estimate_reading_time(self, text_length: int) -> str:
        """估算阅读时间"""
        # 假设平均阅读速度为每分钟300个字符
        minutes = text_length / 300
        if minutes < 1:
            return "< 1分钟"
        elif minutes < 60:
            return f"{int(minutes)}分钟"
        else:
            hours = int(minutes / 60)
            remaining_minutes = int(minutes % 60)
            return f"{hours}小时{remaining_minutes}分钟"
    
    # 委托给工具类的方法
    def _extract_main_points(self, analyzed_data: Dict[str, Any]) -> List[str]:
        """提取主要观点"""
        return KnowledgeGraphUtils.extract_main_points(analyzed_data)
    
    def _extract_supporting_details(self, analyzed_data: Dict[str, Any]) -> List[str]:
        """提取支撑细节"""
        return KnowledgeGraphUtils.extract_supporting_details(analyzed_data)
    
    def _extract_examples(self, analyzed_data: Dict[str, Any]) -> List[str]:
        """提取示例"""
        return KnowledgeGraphUtils.extract_examples(analyzed_data)
    
    def _build_concept_hierarchy(self, keywords: List[str], entities: Dict[str, Any]) -> Dict[str, Any]:
        """构建概念层次结构"""
        return KnowledgeGraphUtils.build_concept_hierarchy(keywords, entities)
    
    def _categorize_knowledge_domains(self, analyzed_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """分类知识领域"""
        return KnowledgeGraphUtils.categorize_knowledge_domains(analyzed_data)
    
    def _generate_learning_objectives(self, themes: List[str], keywords: List[str]) -> List[str]:
        """生成学习目标"""
        return KnowledgeGraphUtils.generate_learning_objectives(themes, keywords)
    
    def _identify_prerequisites(self, analyzed_data: Dict[str, Any]) -> List[str]:
        """识别前置条件"""
        return KnowledgeGraphUtils.identify_prerequisites(analyzed_data)
    
    def _suggest_related_topics(self, keywords: List[str], domain: str) -> List[str]:
        """建议相关主题"""
        return KnowledgeGraphUtils.suggest_related_topics(keywords, domain)
    
    def _build_concept_relationships(self, keywords: List[str]) -> List[Dict[str, str]]:
        """构建概念关系"""
        return KnowledgeGraphUtils.build_concept_relationships(keywords)
    
    def _build_entity_relationships(self, entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """构建实体关系"""
        return KnowledgeGraphUtils.build_entity_relationships(entities)
    
    def _build_hierarchical_relationships(self, keywords: List[str], entities: Dict[str, Any]) -> Dict[str, List[str]]:
        """构建层次关系"""
        return KnowledgeGraphUtils.build_hierarchical_relationships(keywords, entities)
    
    def _build_functional_relationships(self, analyzed_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """构建功能关系"""
        return KnowledgeGraphUtils.build_functional_relationships(analyzed_data)
    
    def _build_dependency_graph(self, keywords: List[str], entities: Dict[str, Any]) -> Dict[str, List[str]]:
        """构建依赖图"""
        return KnowledgeGraphUtils.build_dependency_graph(keywords, entities)
    
    def _identify_practical_uses(self, keywords: List[str], domain: str) -> List[str]:
        """识别实际用途"""
        uses = []
        for keyword in keywords[:5]:
            uses.append(f"在{domain}领域应用{keyword}")
            uses.append(f"使用{keyword}解决具体问题")
        return uses[:8]
    
    def _generate_use_cases(self, keywords: List[str], entities: Dict[str, Any], domain: str) -> List[str]:
        """生成用例"""
        use_cases = []
        tools = entities.get('tool', [])
        skills = entities.get('skill', [])
        
        for tool in tools[:3]:
            use_cases.append(f"使用{tool}进行{domain}相关工作")
        for skill in skills[:3]:
            use_cases.append(f"运用{skill}提升{domain}能力")
        
        return use_cases[:6]
    
    def _suggest_implementation_methods(self, keywords: List[str], domain: str) -> List[str]:
        """建议实施方法"""
        methods = []
        for keyword in keywords[:4]:
            methods.append(f"通过学习{keyword}进行实践")
            methods.append(f"结合{keyword}制定行动计划")
        return methods[:6]
    
    def _define_success_metrics(self, domain: str, keywords: List[str]) -> List[str]:
        """定义成功指标"""
        metrics_map = {
            'technology': ['代码质量提升', '开发效率增加', '技术问题解决率'],
            'business': ['业务指标改善', '市场份额增长', '客户满意度提升'],
            'education': ['学习成果评估', '知识掌握程度', '技能应用能力'],
            'finance': ['投资回报率', '风险控制能力', '财务管理水平'],
            'general': ['目标完成度', '能力提升水平', '实践应用效果']
        }
        return metrics_map.get(domain, metrics_map['general'])
    
    def _identify_common_challenges(self, domain: str, keywords: List[str]) -> List[str]:
        """识别常见挑战"""
        challenges_map = {
            'technology': ['技术复杂性', '学习曲线陡峭', '技术更新快速'],
            'business': ['市场竞争激烈', '资源限制', '客户需求变化'],
            'education': ['学习动机维持', '知识应用转化', '个体差异大'],
            'finance': ['市场风险', '信息不对称', '决策时机'],
            'general': ['理论与实践结合', '持续学习需求', '环境变化适应']
        }
        return challenges_map.get(domain, challenges_map['general'])
    
    def _create_learning_sequence(self, keywords: List[str], domain: str) -> List[str]:
        """创建学习序列"""
        sequence = []
        if keywords:
            sequence.append(f"第一阶段：掌握{keywords[0]}基础知识")
            if len(keywords) > 1:
                sequence.append(f"第二阶段：深入理解{keywords[1]}")
            if len(keywords) > 2:
                sequence.append(f"第三阶段：实践应用{keywords[2]}")
            sequence.append(f"第四阶段：综合运用{domain}相关技能")
        return sequence
    
    def _map_skill_progression(self, keywords: List[str], domain: str) -> Dict[str, List[str]]:
        """映射技能进阶"""
        progression = {
            'beginner': keywords[:2] if keywords else [],
            'intermediate': keywords[2:4] if len(keywords) > 2 else [],
            'advanced': keywords[4:6] if len(keywords) > 4 else []
        }
        return progression
    
    def _define_milestones(self, keywords: List[str], domain: str) -> List[str]:
        """定义里程碑"""
        milestones = []
        for i, keyword in enumerate(keywords[:4], 1):
            milestones.append(f"里程碑{i}：熟练掌握{keyword}")
        return milestones
    
    def _recommend_resources(self, domain: str, keywords: List[str]) -> List[str]:
        """推荐资源"""
        resources_map = {
            'technology': ['技术文档', '开源项目', '在线教程', '技术社区'],
            'business': ['商业案例', '行业报告', '专业书籍', '商业网络'],
            'education': ['学习材料', '实践练习', '同伴交流', '导师指导'],
            'finance': ['财经新闻', '投资指南', '专业课程', '模拟交易'],
            'general': ['相关书籍', '在线资源', '实践机会', '专家建议']
        }
        return resources_map.get(domain, resources_map['general'])
    
    def _suggest_next_steps(self, keywords: List[str], domain: str) -> List[str]:
        """建议下一步"""
        next_steps = []
        for keyword in keywords[:3]:
            next_steps.append(f"深入研究{keyword}相关内容")
            next_steps.append(f"寻找{keyword}实践机会")
        return next_steps[:6]
    
    def _identify_advanced_topics(self, keywords: List[str], domain: str) -> List[str]:
        """识别高级主题"""
        advanced_topics = []
        for keyword in keywords[:4]:
            advanced_topics.append(f"{keyword}高级应用")
            advanced_topics.append(f"{keyword}创新实践")
        return advanced_topics[:6]
