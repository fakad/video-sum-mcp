#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI处理模块，用于与大语言模型交互，提取知识点
"""

import logging
import json
import re
from typing import Dict, Any

from ..utils_modules.utils import get_config, read_temp_content_file

# 设置日志
logger = logging.getLogger("video-sum-mcp.ai_processor")

def build_llm_input(video_id: str) -> Dict[str, Any]:
    """
    从暂存文件构建LLM输入
    
    参数:
        video_id: 视频唯一标识
    
    返回:
        LLM输入数据
    """
    # 从暂存文件读取内容
    content = read_temp_content_file(video_id)
    
    title = content.get("metadata", {}).get("title", "未知视频")
    author = content.get("metadata", {}).get("author", "未知作者")
    platform = content.get("platform", "未知平台") 
    transcript = content.get("content", "")
    
    system_prompt = """
你是一位专业的知识图谱构建专家。请分析以下视频内容，提取关键知识点，并构建一个层次清晰、结构化的知识图谱。

请严格按照以下JSON格式输出，确保包含所有必需字段：

{
    "core_topic": "视频的核心主题（简洁明确）",
    "summary": "视频内容的简要概述（2-3句话）",
    "tags": ["相关标签1", "相关标签2", "相关标签3"],
    "main_sections": [
        {
            "title": "主要章节标题",
            "description": "章节的核心内容描述",
            "key_points": [
                {
                    "title": "知识点标题",
                    "content": "知识点的详细内容",
                    "examples": ["相关案例或例子"],
                    "insights": ["重要洞察或启示"]
                }
            ],
            "subsections": [
                {
                    "title": "子章节标题",
                    "description": "子章节描述",
                    "details": ["具体要点1", "具体要点2"]
                }
            ]
        }
    ],
    "key_takeaways": [
        "核心收获1",
        "核心收获2",
        "核心收获3"
    ],
    "actionable_insights": [
        "可执行的建议1",
        "可执行的建议2"
    ]
}

要求：
1. 提取的内容要有逻辑层次，从核心概念到具体应用
2. 重点关注实际案例、方法论、和可操作的建议
3. 确保知识点之间有清晰的关联关系
4. 标签应该覆盖内容的主要领域和关键词
5. 案例要具体，洞察要深刻
6. 最终的收获和建议要实用和可操作

请确保输出的是有效的JSON格式，不要包含任何额外的文字说明。
"""
    
    user_message = f"""
视频标题: {title}
作者: {author}
平台: {platform}

视频内容转录:
{transcript}

请按照要求的JSON格式，提取这个视频的核心知识，构建结构化的知识图谱。
"""
    
    return {
        "system_prompt": system_prompt,
        "user_message": user_message
    }

def parse_llm_response(llm_response: str) -> Dict[str, Any]:
    """
    解析LLM响应文本，提取知识数据
    
    参数:
        llm_response: LLM响应文本
    
    返回:
        解析后的知识数据
    """
    try:
        # 尝试直接解析JSON
        knowledge_data = json.loads(llm_response.strip())
        
        # 验证必要字段
        required_fields = ["core_topic", "main_sections", "key_takeaways"]
        for field in required_fields:
            if field not in knowledge_data:
                logger.warning(f"缺少必要字段: {field}")
                
        logger.info("成功解析LLM响应")
        return knowledge_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {str(e)}")
        
        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            try:
                knowledge_data = json.loads(json_match.group())
                logger.info("成功从响应中提取JSON")
                return knowledge_data
            except json.JSONDecodeError:
                pass
        
        # 如果无法解析，返回错误信息
        return {
            "error": f"无法解析LLM响应为有效的JSON格式: {str(e)}",
            "raw_response": llm_response
        }

def process_with_llm(video_id: str) -> Dict[str, Any]:
    """
    使用LLM处理视频内容
    
    参数:
        video_id: 视频唯一标识
    
    返回:
        处理结果
    """
    # 注意: 此函数在MCP环境中不会直接调用LLM API
    # 而是返回提示词，供用户在Cursor中交互处理
    
    try:
        llm_input = build_llm_input(video_id)
        
        return {
            "status": "prepared",
            "message": "已准备LLM提示词，请在Cursor界面中处理",
            "video_id": video_id,
            "system_prompt": llm_input["system_prompt"],
            "user_message": llm_input["user_message"],
            "llm_input": llm_input
        }
    except Exception as e:
        logger.error(f"准备LLM输入时出错: {str(e)}")
        return {
            "status": "error", 
            "message": f"准备LLM输入失败: {str(e)}",
            "video_id": video_id
        }

def save_llm_result(video_id: str, llm_response: str) -> Dict[str, Any]:
    """
    保存LLM处理结果
    
    参数:
        video_id: 视频唯一标识
        llm_response: LLM响应文本
    
    返回:
        解析后的知识数据
    """
    try:
        # 解析LLM响应
        knowledge_data = parse_llm_response(llm_response)
        
        # TODO: 将解析结果保存到临时文件
        # 这里可以添加将结果保存到指定格式的文件的逻辑
        
        return knowledge_data
    except Exception as e:
        logger.error(f"保存LLM结果时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"保存LLM结果失败: {str(e)}",
            "video_id": video_id
        } 