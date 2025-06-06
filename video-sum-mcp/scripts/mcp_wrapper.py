#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
video-sum-mcp包装器
为MCP工具提供接口
"""

import json
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 切换工作目录到项目根目录
os.chdir(project_root)

from main import process_video, continue_processing, list_supported_platforms, list_supported_formats, configure

def main():
    # 确保有足够的参数
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "error",
            "message": "参数不足，请提供方法名和参数JSON"
        }), flush=True)
        return
    
    # 解析方法名和参数
    method_name = sys.argv[1]
    params_json = sys.argv[2]
    
    try:
        params = json.loads(params_json)
    except json.JSONDecodeError:
        print(json.dumps({
            "status": "error",
            "message": "参数解析失败，无效的JSON"
        }), flush=True)
        return
    
    # 根据方法名调用相应函数
    if method_name == "process_video":
        url = params.get("url", "")
        output_format = params.get("output_format", "markdown")
        use_proxy = params.get("use_proxy", False)
        
        result = process_video(url=url, output_format=output_format, use_proxy=use_proxy)
        print(json.dumps(result), flush=True)
    
    elif method_name == "continue_processing":
        video_id = params.get("video_id", "")
        llm_response = params.get("llm_response", "")
        output_format = params.get("output_format", "markdown")
        
        result = continue_processing(video_id=video_id, llm_response=llm_response, output_format=output_format)
        print(json.dumps(result), flush=True)
    
    elif method_name == "list_supported_platforms":
        result = list_supported_platforms()
        print(json.dumps(result), flush=True)
    
    elif method_name == "list_supported_formats":
        result = list_supported_formats()
        print(json.dumps(result), flush=True)
    
    elif method_name == "configure":
        api_key = params.get("api_key")
        proxy = params.get("proxy")
        output_dir = params.get("output_dir")
        
        result = configure(api_key=api_key, proxy=proxy, output_dir=output_dir)
        print(json.dumps(result), flush=True)
    
    else:
        print(json.dumps({
            "status": "error",
            "message": f"未知方法: {method_name}"
        }), flush=True)

if __name__ == "__main__":
    main()