#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenAI模型集成模块，用于处理与OpenAI API的交互
注意: 在MCP环境中，此模块仅作为参考，实际LLM调用将在Cursor中进行
"""

import logging
import json
from typing import Dict, Any, Optional, List

from ..core.utils import get_config

# 设置日志
logger = logging.getLogger("video-sum-mcp.models.openai")

class OpenAIProcessor:
    """OpenAI模型处理器"""
    
    def __init__(self):
        """初始化OpenAI处理器"""
        self.config = get_config()
        self.llm_settings = self.config.get("llm_settings", {})
    
    def process(self, system_prompt: str, user_message: str) -> Dict[str, Any]:
        """
        使用OpenAI处理文本
        
        参数:
            system_prompt: 系统提示词
            user_message: 用户消息
            
        返回:
            处理结果
        """
        # 注意: 此函数在MCP环境中不会被直接调用
        # 实际的LLM交互会在Cursor中进行
        # 此处仅作为参考实现
        
        try:
            import openai
            
            api_key = self.config.get("api_key")
            if not api_key:
                error_msg = "未提供OpenAI API密钥"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg
                }
            
            # 设置API密钥
            openai.api_key = api_key
            
            # 获取模型设置
            model = self.llm_settings.get("model", "gpt-3.5-turbo-16k")
            temperature = self.llm_settings.get("temperature", 0.3)
            max_tokens = self.llm_settings.get("max_tokens", 4000)
            
            # 设置代理（如果有）
            proxy = self.config.get("proxy")
            if proxy:
                import os
                os.environ["http_proxy"] = proxy
                os.environ["https_proxy"] = proxy
            
            # 调用API
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 提取响应文本
            response_text = response.choices[0].message.content
            
            return {
                "status": "success",
                "response": response_text
            }
            
        except Exception as e:
            error_msg = f"OpenAI API调用失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def get_format_template(self) -> Dict[str, Any]:
        """
        获取OpenAI模型的输出格式模板
        
        返回:
            格式模板
        """
        return {
            "core_topic": "视频的核心主题",
            "main_points": [
                {
                    "title": "主要知识点1",
                    "description": "详细描述",
                    "sub_points": [
                        {
                            "title": "子知识点1",
                            "description": "详细描述"
                        }
                    ]
                }
            ],
            "relationships": [
                "知识点1与知识点2的关系"
            ]
        }