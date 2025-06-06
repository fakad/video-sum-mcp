#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识图谱模块
提供内容分析、知识图谱生成和文档格式化功能
"""

from .analyzer import ContentAnalyzer
from .generator import KnowledgeGraphGenerator
from .formatter import DocumentFormatter
from .utils import KnowledgeGraphUtils

class KnowledgeGraphProcessor:
    """
    知识图谱处理器主协调器
    整合内容分析、知识图谱生成和文档格式化功能
    """
    
    def __init__(self):
        """初始化协调器"""
        self.analyzer = ContentAnalyzer()
        self.generator = KnowledgeGraphGenerator()
        self.formatter = DocumentFormatter()
    
    def generate_knowledge_graph_document(self, content_data):
        """
        生成知识图谱文档
        
        参数:
            content_data: 包含内容和元数据的字典
            
        返回:
            str: 格式化的知识图谱文档
        """
        # 第一步：内容分析
        analyzed_data = self.analyzer.analyze_content(content_data)
        
        # 第二步：生成知识图谱结构
        knowledge_graph = self.generator.generate_knowledge_graph(analyzed_data, content_data)
        
        # 第三步：格式化为文档
        document = self.formatter.format_knowledge_graph_document(knowledge_graph)
        
        return document

__all__ = [
    'ContentAnalyzer',
    'KnowledgeGraphGenerator', 
    'DocumentFormatter',
    'KnowledgeGraphUtils',
    'KnowledgeGraphProcessor'
] 