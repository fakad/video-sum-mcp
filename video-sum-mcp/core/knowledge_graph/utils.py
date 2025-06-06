#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识图谱工具类模块
包含生成器使用的辅助方法
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("video-sum-mcp.knowledge_graph.utils")

class KnowledgeGraphUtils:
    """
    知识图谱工具类
    提供各种辅助方法
    """
    
    @staticmethod
    def extract_main_points(analyzed_data: Dict[str, Any]) -> List[str]:
        """提取主要观点"""
        themes = analyzed_data.get('themes', [])
        key_phrases = analyzed_data.get('key_phrases', [])
        
        main_points = []
        
        # 从主题中提取
        for theme in themes[:3]:
            main_points.append(f"主要观点：{theme}")
        
        # 从关键短语中提取
        for phrase in key_phrases[:3]:
            main_points.append(f"核心内容：{phrase}")
        
        return main_points[:5]
    
    @staticmethod
    def extract_supporting_details(analyzed_data: Dict[str, Any]) -> List[str]:
        """提取支撑细节"""
        entities = analyzed_data.get('entities', {})
        
        details = []
        
        # 从实体中提取
        for entity_type, entity_list in entities.items():
            for entity in entity_list[:2]:
                details.append(f"{entity_type}细节：{entity}")
        
        return details[:8]
    
    @staticmethod
    def extract_examples(analyzed_data: Dict[str, Any]) -> List[str]:
        """提取示例"""
        key_phrases = analyzed_data.get('key_phrases', [])
        
        examples = []
        for phrase in key_phrases[3:6]:  # 使用中间的关键短语作为示例
            examples.append(f"实例说明：{phrase}")
        
        return examples
    
    @staticmethod
    def build_concept_hierarchy(keywords: List[str], entities: Dict[str, Any]) -> Dict[str, Any]:
        """构建概念层次结构"""
        hierarchy = {
            'root_concepts': keywords[:3] if keywords else [],
            'sub_concepts': {},
            'leaf_concepts': []
        }
        
        # 为每个根概念分配子概念
        for i, root_concept in enumerate(hierarchy['root_concepts']):
            start_idx = 3 + i * 2
            end_idx = start_idx + 2
            hierarchy['sub_concepts'][root_concept] = keywords[start_idx:end_idx]
        
        # 叶子概念
        hierarchy['leaf_concepts'] = keywords[9:12] if len(keywords) > 9 else []
        
        return hierarchy
    
    @staticmethod
    def categorize_knowledge_domains(analyzed_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """分类知识领域"""
        keyword_groups = analyzed_data.get('keyword_groups', {})
        
        domains = {
            'theoretical': keyword_groups.get('core', [])[:3],
            'practical': keyword_groups.get('application', [])[:3],
            'methodological': keyword_groups.get('method', [])[:3],
            'technical': keyword_groups.get('tool', [])[:3]
        }
        
        return domains
    
    @staticmethod
    def generate_learning_objectives(themes: List[str], keywords: List[str]) -> List[str]:
        """生成学习目标"""
        objectives = []
        
        for theme in themes[:3]:
            objectives.append(f"理解并掌握{theme}的核心要点")
        
        for keyword in keywords[:3]:
            objectives.append(f"能够应用{keyword}解决实际问题")
        
        return objectives[:5]
    
    @staticmethod
    def identify_prerequisites(analyzed_data: Dict[str, Any]) -> List[str]:
        """识别前置条件"""
        domain = analyzed_data.get('domain', 'general')
        
        prerequisites_map = {
            'technology': ['基础编程知识', '计算机操作技能'],
            'business': ['商业基础知识', '市场理解'],
            'education': ['学习方法', '基础知识背景'],
            'finance': ['经济学基础', '数学计算能力'],
            'general': ['基础阅读理解能力']
        }
        
        return prerequisites_map.get(domain, prerequisites_map['general'])
    
    @staticmethod
    def suggest_related_topics(keywords: List[str], domain: str) -> List[str]:
        """建议相关主题"""
        related_topics = []
        
        # 基于关键词生成相关主题
        for keyword in keywords[:5]:
            related_topics.append(f"{keyword}相关研究")
            related_topics.append(f"{keyword}实践案例")
        
        return related_topics[:8]
    
    @staticmethod
    def build_concept_relationships(keywords: List[str]) -> List[Dict[str, str]]:
        """构建概念关系"""
        relationships = []
        
        # 生成关键词之间的关系
        for i, keyword1 in enumerate(keywords[:5]):
            for keyword2 in keywords[i+1:6]:
                relationships.append({
                    'source': keyword1,
                    'target': keyword2,
                    'relationship': 'related_to',
                    'strength': 0.7
                })
        
        return relationships[:10]
    
    @staticmethod
    def build_entity_relationships(entities: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """构建实体关系"""
        relationships = []
        
        for entity_type, entity_list in entities.items():
            for i, entity in enumerate(entity_list):
                for other_type, other_list in entities.items():
                    if other_type != entity_type:
                        for other_entity in other_list[:2]:
                            relationships.append({
                                'source': entity,
                                'target': other_entity,
                                'relationship': f"{entity_type}_to_{other_type}",
                                'strength': 0.5
                            })
        
        return relationships[:15]
    
    @staticmethod
    def build_hierarchical_relationships(keywords: List[str], entities: Dict[str, Any]) -> Dict[str, List[str]]:
        """构建层次关系"""
        hierarchy = {}
        
        if keywords:
            # 第一个关键词作为父概念
            parent = keywords[0]
            hierarchy[parent] = keywords[1:4]
        
        return hierarchy
    
    @staticmethod
    def build_functional_relationships(analyzed_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """构建功能关系"""
        keyword_groups = analyzed_data.get('keyword_groups', {})
        relationships = []
        
        # 方法与应用的关系
        methods = keyword_groups.get('method', [])
        applications = keyword_groups.get('application', [])
        
        for method in methods:
            for application in applications:
                relationships.append({
                    'source': method,
                    'target': application,
                    'relationship': 'enables',
                    'strength': 0.8
                })
        
        return relationships[:10]
    
    @staticmethod
    def build_dependency_graph(keywords: List[str], entities: Dict[str, Any]) -> Dict[str, List[str]]:
        """构建依赖图"""
        dependencies = {}
        
        # 简单的依赖关系：基础概念 -> 高级概念
        if len(keywords) >= 3:
            dependencies[keywords[0]] = []  # 基础概念无依赖
            dependencies[keywords[1]] = [keywords[0]]  # 依赖第一个
            dependencies[keywords[2]] = [keywords[0], keywords[1]]  # 依赖前两个
        
        return dependencies 