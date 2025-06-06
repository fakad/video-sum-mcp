#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档格式化器模块
负责将知识图谱转换为Markdown文档
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("video-sum-mcp.knowledge_graph.formatter")

class DocumentFormatter:
    """
    文档格式化器
    将知识图谱转换为结构化的Markdown文档
    """
    
    def __init__(self):
        """初始化格式化器"""
        pass
        
    def format_knowledge_graph_document(self, knowledge_graph: Dict[str, Any]) -> str:
        """
        将知识图谱格式化为Markdown文档
        
        参数:
            knowledge_graph: 知识图谱数据
            
        返回:
            Markdown格式的文档字符串
        """
        logger.info(f"开始格式化知识图谱文档: {knowledge_graph.get('metadata', {}).get('title', '未知标题')}")
        
        sections = [
            self._format_header(knowledge_graph),
            self._format_metadata(knowledge_graph.get('metadata', {})),
            self._format_content_analysis(knowledge_graph.get('content_analysis', {})),
            self._format_knowledge_structure(knowledge_graph.get('knowledge_structure', {})),
            self._format_relationships(knowledge_graph.get('relationships', {})),
            self._format_applications(knowledge_graph.get('applications', {})),
            self._format_development_path(knowledge_graph.get('development_path', {}))
        ]
        
        document = '\n\n'.join(filter(None, sections))
        
        logger.info("知识图谱文档格式化完成")
        return document
    
    def _format_header(self, knowledge_graph: Dict[str, Any]) -> str:
        """格式化文档头部"""
        metadata = knowledge_graph.get('metadata', {})
        title = metadata.get('title', '未知标题')
        
        header = f"# {title}\n\n"
        header += f"> 知识图谱文档 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return header
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """格式化元数据"""
        if not metadata:
            return ""
        
        content = "## 📋 基本信息\n\n"
        content += "| 项目 | 内容 |\n"
        content += "|------|------|\n"
        
        metadata_items = [
            ('标题', metadata.get('title', '未知')),
            ('来源平台', metadata.get('source', '未知')),
            ('作者', metadata.get('author', '未知')),
            ('内容类型', metadata.get('content_type', '文本')),
            ('知识领域', metadata.get('domain', '通用')),
            ('难度等级', metadata.get('difficulty_level', '初级')),
            ('预估阅读时间', metadata.get('estimated_reading_time', '未知')),
            ('语言', metadata.get('language', 'zh-CN'))
        ]
        
        for item, value in metadata_items:
            content += f"| {item} | {value} |\n"
        
        # 添加标签
        tags = metadata.get('tags', [])
        if tags:
            content += f"\n**主要标签**: {', '.join([f'`{tag}`' for tag in tags[:10]])}\n"
        
        return content
    
    def _format_content_analysis(self, content_analysis: Dict[str, Any]) -> str:
        """格式化内容分析"""
        if not content_analysis:
            return ""
        
        content = "## 🔍 内容分析\n\n"
        
        # 摘要
        summary = content_analysis.get('summary', '')
        if summary:
            content += f"### 内容摘要\n\n{summary}\n\n"
        
        # 主要主题
        themes = content_analysis.get('main_themes', [])
        if themes:
            content += "### 主要主题\n\n"
            for i, theme in enumerate(themes, 1):
                content += f"{i}. {theme}\n"
            content += "\n"
        
        # 关键概念
        concepts = content_analysis.get('key_concepts', [])
        if concepts:
            content += "### 关键概念\n\n"
            content += ", ".join([f"`{concept}`" for concept in concepts]) + "\n\n"
        
        # 实体分析
        entities = content_analysis.get('entities', {})
        if entities:
            content += "### 实体分析\n\n"
            for entity_type, entity_list in entities.items():
                if entity_list:
                    type_names = {
                        'person': '人物',
                        'organization': '组织机构',
                        'concept': '概念',
                        'tool': '工具',
                        'skill': '技能'
                    }
                    type_name = type_names.get(entity_type, entity_type)
                    content += f"**{type_name}**: {', '.join([f'`{entity}`' for entity in entity_list])}\n\n"
        
        # 关键短语
        key_phrases = content_analysis.get('key_phrases', [])
        if key_phrases:
            content += "### 关键短语\n\n"
            for phrase in key_phrases[:5]:  # 只显示前5个
                content += f"- {phrase}\n"
            content += "\n"
        
        # 内容结构
        content_structure = content_analysis.get('content_structure', {})
        if content_structure:
            content += self._format_content_structure(content_structure)
        
        return content
    
    def _format_content_structure(self, structure: Dict[str, Any]) -> str:
        """格式化内容结构"""
        content = "### 内容结构\n\n"
        
        # 主要观点
        main_points = structure.get('main_points', [])
        if main_points:
            content += "#### 主要观点\n\n"
            for point in main_points:
                content += f"- {point}\n"
            content += "\n"
        
        # 支撑细节
        supporting_details = structure.get('supporting_details', [])
        if supporting_details:
            content += "#### 支撑细节\n\n"
            for detail in supporting_details:
                content += f"- {detail}\n"
            content += "\n"
        
        # 示例说明
        examples = structure.get('examples', [])
        if examples:
            content += "#### 示例说明\n\n"
            for example in examples:
                content += f"- {example}\n"
            content += "\n"
        
        return content
    
    def _format_knowledge_structure(self, knowledge_structure: Dict[str, Any]) -> str:
        """格式化知识结构"""
        if not knowledge_structure:
            return ""
        
        content = "## 🏗️ 知识结构\n\n"
        
        # 核心概念层次
        core_concepts = knowledge_structure.get('core_concepts', {})
        if core_concepts:
            content += "### 概念层次\n\n"
            
            primary = core_concepts.get('primary', [])
            if primary:
                content += f"**核心概念**: {', '.join([f'`{concept}`' for concept in primary])}\n\n"
            
            secondary = core_concepts.get('secondary', [])
            if secondary:
                content += f"**次级概念**: {', '.join([f'`{concept}`' for concept in secondary])}\n\n"
            
            tertiary = core_concepts.get('tertiary', [])
            if tertiary:
                content += f"**扩展概念**: {', '.join([f'`{concept}`' for concept in tertiary])}\n\n"
        
        # 知识领域分类
        knowledge_domains = knowledge_structure.get('knowledge_domains', {})
        if knowledge_domains:
            content += "### 知识领域分类\n\n"
            domain_names = {
                'theoretical': '理论基础',
                'practical': '实践应用',
                'methodological': '方法论',
                'technical': '技术工具'
            }
            
            for domain, concepts in knowledge_domains.items():
                if concepts:
                    domain_name = domain_names.get(domain, domain)
                    content += f"**{domain_name}**: {', '.join([f'`{concept}`' for concept in concepts])}\n\n"
        
        # 学习目标
        learning_objectives = knowledge_structure.get('learning_objectives', [])
        if learning_objectives:
            content += "### 学习目标\n\n"
            for i, objective in enumerate(learning_objectives, 1):
                content += f"{i}. {objective}\n"
            content += "\n"
        
        # 前置条件
        prerequisites = knowledge_structure.get('prerequisites', [])
        if prerequisites:
            content += "### 前置条件\n\n"
            for prereq in prerequisites:
                content += f"- {prereq}\n"
            content += "\n"
        
        # 相关主题
        related_topics = knowledge_structure.get('related_topics', [])
        if related_topics:
            content += "### 相关主题\n\n"
            for topic in related_topics[:8]:  # 限制显示数量
                content += f"- {topic}\n"
            content += "\n"
        
        return content
    
    def _format_relationships(self, relationships: Dict[str, Any]) -> str:
        """格式化关系网络"""
        if not relationships:
            return ""
        
        content = "## 🔗 关系网络\n\n"
        
        # 概念关系
        concept_relationships = relationships.get('concept_relationships', [])
        if concept_relationships:
            content += "### 概念关系\n\n"
            content += "```mermaid\n"
            content += "graph LR\n"
            for rel in concept_relationships[:8]:  # 限制显示数量
                source = rel.get('source', '').replace(' ', '_')
                target = rel.get('target', '').replace(' ', '_')
                content += f"    {source} --> {target}\n"
            content += "```\n\n"
        
        # 层次关系
        hierarchical = relationships.get('hierarchical_relationships', {})
        if hierarchical:
            content += "### 层次关系\n\n"
            for parent, children in hierarchical.items():
                if children:
                    content += f"**{parent}**\n"
                    for child in children:
                        content += f"  - {child}\n"
                    content += "\n"
        
        # 依赖关系
        dependency_graph = relationships.get('dependency_graph', {})
        if dependency_graph:
            content += "### 依赖关系\n\n"
            for concept, dependencies in dependency_graph.items():
                if dependencies:
                    deps_str = ', '.join([f'`{dep}`' for dep in dependencies])
                    content += f"- **{concept}** 依赖于: {deps_str}\n"
                else:
                    content += f"- **{concept}** (基础概念)\n"
            content += "\n"
        
        return content
    
    def _format_applications(self, applications: Dict[str, Any]) -> str:
        """格式化应用场景"""
        if not applications:
            return ""
        
        content = "## 💡 应用场景\n\n"
        
        # 实际用途
        practical_uses = applications.get('practical_uses', [])
        if practical_uses:
            content += "### 实际用途\n\n"
            for use in practical_uses:
                content += f"- {use}\n"
            content += "\n"
        
        # 用例场景
        use_cases = applications.get('use_cases', [])
        if use_cases:
            content += "### 用例场景\n\n"
            for case in use_cases:
                content += f"- {case}\n"
            content += "\n"
        
        # 实施方法
        implementation_methods = applications.get('implementation_methods', [])
        if implementation_methods:
            content += "### 实施方法\n\n"
            for method in implementation_methods:
                content += f"- {method}\n"
            content += "\n"
        
        # 工具和资源
        tools_and_resources = applications.get('tools_and_resources', [])
        if tools_and_resources:
            content += "### 工具和资源\n\n"
            content += ", ".join([f"`{tool}`" for tool in tools_and_resources]) + "\n\n"
        
        # 成功指标
        success_metrics = applications.get('success_metrics', [])
        if success_metrics:
            content += "### 成功指标\n\n"
            for metric in success_metrics:
                content += f"- {metric}\n"
            content += "\n"
        
        # 常见挑战
        common_challenges = applications.get('common_challenges', [])
        if common_challenges:
            content += "### 常见挑战\n\n"
            for challenge in common_challenges:
                content += f"- {challenge}\n"
            content += "\n"
        
        return content
    
    def _format_development_path(self, development_path: Dict[str, Any]) -> str:
        """格式化发展路径"""
        if not development_path:
            return ""
        
        content = "## 🛤️ 发展路径\n\n"
        
        # 学习序列
        learning_sequence = development_path.get('learning_sequence', [])
        if learning_sequence:
            content += "### 学习序列\n\n"
            for i, step in enumerate(learning_sequence, 1):
                content += f"{i}. {step}\n"
            content += "\n"
        
        # 技能进阶
        skill_progression = development_path.get('skill_progression', {})
        if skill_progression:
            content += "### 技能进阶\n\n"
            level_names = {
                'beginner': '初级',
                'intermediate': '中级',
                'advanced': '高级'
            }
            
            for level, skills in skill_progression.items():
                if skills:
                    level_name = level_names.get(level, level)
                    content += f"**{level_name}**: {', '.join([f'`{skill}`' for skill in skills])}\n\n"
        
        # 里程碑
        milestones = development_path.get('milestones', [])
        if milestones:
            content += "### 里程碑\n\n"
            for milestone in milestones:
                content += f"- [ ] {milestone}\n"
            content += "\n"
        
        # 推荐资源
        resources = development_path.get('resources', [])
        if resources:
            content += "### 推荐资源\n\n"
            for resource in resources:
                content += f"- {resource}\n"
            content += "\n"
        
        # 下一步建议
        next_steps = development_path.get('next_steps', [])
        if next_steps:
            content += "### 下一步建议\n\n"
            for step in next_steps:
                content += f"- {step}\n"
            content += "\n"
        
        # 高级主题
        advanced_topics = development_path.get('advanced_topics', [])
        if advanced_topics:
            content += "### 高级主题\n\n"
            for topic in advanced_topics:
                content += f"- {topic}\n"
            content += "\n"
        
        return content 