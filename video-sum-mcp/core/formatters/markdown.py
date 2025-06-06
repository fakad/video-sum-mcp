#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Markdown格式化器，用于生成Markdown格式的知识图谱
"""

import os
import logging
from typing import Dict, Any, List

# 设置日志
logger = logging.getLogger("video-sum-mcp.formatters.markdown")

class MarkdownFormatter:
    """Markdown格式化器类"""
    
    def __init__(self):
        """初始化Markdown格式化器"""
        pass
    
    def format(self, knowledge_data: Dict[str, Any], output_file: str) -> Dict[str, Any]:
        """
        将知识数据格式化为Markdown文件
        
        参数:
            knowledge_data: AI处理后的知识数据
            output_file: 输出文件路径
            
        返回:
            格式化结果
        """
        try:
            # 获取核心主题
            core_topic = knowledge_data.get("core_topic", "未知主题")
            
            with open(output_file, "w", encoding="utf-8") as f:
                # 写入标题
                f.write(f"# {core_topic}\n\n")
                
                # 写入概述（如果有）
                if "overview" in knowledge_data:
                    f.write(f"## 概述\n\n{knowledge_data['overview']}\n\n")
                
                # 写入主要知识点
                main_points = knowledge_data.get("main_points", [])
                if main_points:
                    f.write("## 主要知识点\n\n")
                
                for i, point in enumerate(main_points):
                    f.write(f"### {i+1}. {point.get('title')}\n\n")
                    f.write(f"{point.get('description', '')}\n\n")
                    
                    # 写入子知识点
                    sub_points = point.get("sub_points", [])
                    for j, sub_point in enumerate(sub_points):
                        f.write(f"#### {i+1}.{j+1} {sub_point.get('title')}\n\n")
                        f.write(f"{sub_point.get('description', '')}\n\n")
                
                # 写入关系
                relationships = knowledge_data.get("relationships", [])
                if relationships:
                    f.write("## 知识点关系\n\n")
                    for relation in relationships:
                        f.write(f"- {relation}\n")
                
                # 写入元数据（如果有）
                metadata = knowledge_data.get("metadata", {})
                if metadata:
                    f.write("\n---\n\n")
                    f.write("## 元数据\n\n")
                    for key, value in metadata.items():
                        f.write(f"- **{key}**: {value}\n")
            
            logger.info(f"已生成Markdown知识图谱: {output_file}")
            
            return {
                "status": "success",
                "message": "已生成Markdown知识图谱",
                "output_path": output_file,
                "format": "markdown"
            }
        
        except Exception as e:
            error_msg = f"生成Markdown知识图谱失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def get_template(self) -> str:
        """
        获取Markdown模板
        
        返回:
            Markdown模板字符串
        """
        return """
# {core_topic}

## 概述

{overview}

## 主要知识点

{main_points}

## 知识点关系

{relationships}

---

## 元数据

{metadata}
""" 