#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
video-sum-mcp主入口文件
实现MCP工具接口定义和主要功能执行
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# 确保当前目录在Python路径中，以便正确导入core模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 使用相对导入替换绝对导入
from core.media_extractor import MediaExtractor
from core.processors.content_analyzer import generate_content_analysis_document
from core.utils_modules.utils import get_config, update_config, generate_video_id
import time

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("video-sum-mcp")

def ensure_output_directory(project_dir: str = None) -> Path:
    """
    确保output目录存在
    
    参数:
        project_dir: 项目目录，如果为None则使用当前工作目录
    
    返回:
        output目录的Path对象
    """
    base_dir = Path(project_dir) if project_dir else Path.cwd()
    output_dir = base_dir / "output"
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建output目录: {output_dir}")
    
    return output_dir

def sanitize_filename(filename: str) -> str:
    """净化文件名，移除非法字符"""
    import re
    # 移除文件名中的非法字符
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # 将连续的空格和其他空白字符替换为单个下划线
    sanitized = re.sub(r'\s+', "_", sanitized)
    # 限制文件名长度
    if len(sanitized) > 50:
        sanitized = sanitized[:47] + "..."
    return sanitized or "未知内容"

def process_video(url: str, output_format: str = "markdown", use_proxy: bool = False, project_dir: str = None, context_text: str = "") -> Dict[str, Any]:
    """
    处理视频URL，提取内容并生成深度分析文档
    
    参数:
        url: 视频URL，支持抖音、小红书、知乎等平台
        output_format: 输出格式，支持markdown等，默认为markdown
        use_proxy: 是否使用代理，默认为false
        project_dir: 调用者项目目录，如果为None则使用当前目录
        context_text: 可选的上下文文本，帮助提取更准确的信息
    
    返回:
        包含处理结果的字典，包括保存路径、状态等
    """
    logger.info(f"处理视频: {url}, 格式: {output_format}, 代理: {use_proxy}, 项目目录: {project_dir}")
    
    try:
        # 1. 确保output目录存在
        output_dir = ensure_output_directory(project_dir)
        
        # 2. 提取内容
        extractor = MediaExtractor(use_proxy=use_proxy)
        content_data = extractor.extract(url, context_text)
        
        if content_data.get("status") == "error":
            return {
                "status": "error",
                "message": f"内容提取失败: {content_data.get('message')}",
                "url": url
            }
        
        # 3. 生成知识图谱
        try:
            from core.knowledge_graph import KnowledgeGraphProcessor
            from core.services.quality_control import QualityController
            
            # 添加内容质量预检查
            quality_controller = QualityController()
            is_valid, validation_issues = quality_controller.validate_content_before_generation(content_data)
            
            if not is_valid:
                # 内容质量不合格，拒绝生成
                error_message = "内容提取质量不佳，无法生成有意义的知识图谱。"
                detailed_issues = "\n".join([f"• {issue}" for issue in validation_issues])
                
                logger.warning(f"内容质量验证失败: {error_message}")
                logger.warning(f"详细问题:\n{detailed_issues}")
                
                return {
                    "status": "error",
                    "message": f"{error_message}\n\n问题详情:\n{detailed_issues}\n\n建议:\n" +
                              "1. 确认视频链接有效且可访问\n" +
                              "2. 尝试提供视频的标题和描述作为上下文信息\n" +
                              "3. 检查视频是否为私密内容或需要登录\n" +
                              "4. 对于抖音链接，建议提供完整的分享文本作为context_text参数\n" +
                              "5. 确保视频内容包含有意义的信息而非纯娱乐内容",
                    "url": url,
                    "validation_issues": validation_issues,
                    "extraction_details": {
                        "platform": content_data.get('platform', '未知'),
                        "title": content_data.get('metadata', {}).get('title', '未提取'),
                        "author": content_data.get('metadata', {}).get('author', '未提取'),
                        "content_length": len(content_data.get('content', ''))
                    }
                }
            
            # 内容质量合格，继续生成知识图谱
            logger.info("内容质量验证通过，开始生成知识图谱")
            processor = KnowledgeGraphProcessor()
            knowledge_graph = processor.generate_knowledge_graph_document(content_data)
            
        except ValueError as e:
            # 知识图谱生成器内部的质量检查失败（双重保险）
            error_message = str(e)
            logger.warning(f"知识图谱生成器质量检查失败: {error_message}")
            
            return {
                "status": "error",
                "message": f"内容提取质量不佳，无法生成知识图谱。\n\n问题详情:\n{error_message}\n\n建议:\n" +
                          "1. 确认视频链接有效且可访问\n" +
                          "2. 尝试提供视频的标题和描述作为上下文信息\n" +
                          "3. 检查视频是否为私密内容或需要登录\n" +
                          "4. 对于抖音链接，建议提供完整的分享文本作为context_text参数",
                "url": url,
                "extraction_details": {
                    "platform": content_data.get('platform', '未知'),
                    "title": content_data.get('metadata', {}).get('title', '未提取'),
                    "author": content_data.get('metadata', {}).get('author', '未提取'),
                    "content_length": len(content_data.get('content', ''))
                }
            }
        
        # 4. 保存到output目录
        metadata = content_data.get('metadata', {})
        platform_names = {
            'douyin': '抖音',
            'xiaohongshu': '小红书', 
            'zhihu': '知乎',
            'bilibili': '哔哩哔哩'
        }
        platform_cn = platform_names.get(content_data.get('platform', ''), content_data.get('platform', '未知平台'))
        title = sanitize_filename(metadata.get('title', '未知内容'))
        
        # 简化文件名：直接使用标题，不添加时间戳
        filename = f"{title}.md"
        
        # 如果文件已存在，添加数字后缀避免覆盖
        output_path = Path.cwd() / "output"
        output_path.mkdir(exist_ok=True)
        
        final_path = output_path / filename
        counter = 1
        while final_path.exists():
            name_part = title
            filename = f"{name_part}_{counter}.md"
            final_path = output_path / filename
            counter += 1
        
        file_path = final_path
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(knowledge_graph)
        
        logger.info(f"深度分析文档已保存: {file_path}")
        
        return {
            "status": "success",
            "message": "内容分析完成",
            "output_file": str(file_path),
            "filename": filename,
            "platform": platform_cn,
            "title": metadata.get('title', '未知内容'),
            "author": metadata.get('author', '未知作者'),
            "content_type": content_data.get('content_type', metadata.get('content_type', '数字内容')),
            "output_format": output_format,
            "url": url
        }
        
    except Exception as e:
        logger.error(f"处理内容时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"处理失败: {str(e)}",
            "url": url
        }

def continue_processing(video_id: str, llm_response: str, output_format: str = "markdown", project_dir: str = None) -> Dict[str, Any]:
    """
    继续处理功能（为了保持MCP接口兼容性，但实际上现在是一步到位）
    
    参数:
        video_id: 视频唯一标识（实际为URL）
        llm_response: LLM响应文本（现在不需要，因为是自动生成）
        output_format: 输出格式，默认为markdown
        project_dir: 调用者项目目录，如果为None则使用当前目录
        
    返回:
        处理结果
    """
    logger.info(f"继续处理功能调用，重定向到process_video")
    
    # 将video_id作为URL处理（向后兼容）
    return process_video(video_id, output_format, False, project_dir)

def list_supported_platforms() -> List[str]:
    """
    列出支持的视频平台
    
    返回:
        平台名称列表
    """
    try:
        extractor = MediaExtractor()
        return extractor.get_supported_platforms()
    except Exception as e:
        logger.error(f"获取平台列表时出错: {str(e)}")
        # 返回默认支持的平台列表
        return ["douyin", "xiaohongshu", "zhihu", "bilibili"]

def list_supported_formats() -> List[str]:
    """
    列出支持的输出格式
    
    返回:
        格式名称列表
    """
    return ["markdown"]

def configure(api_key: Optional[str] = None, proxy: Optional[str] = None, 
              output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    配置工具参数
    
    参数:
        api_key: LLM API密钥（可选，当前版本不需要）
        proxy: 代理服务器地址（可选）
        output_dir: 输出目录（可选）
    
    返回:
        配置结果状态
    """
    config_updates = {}
    
    if api_key is not None:
        config_updates["api_key"] = api_key
    if proxy is not None:
        config_updates["proxy"] = proxy
    if output_dir is not None:
        config_updates["output_dir"] = output_dir
    
    try:
        if config_updates:
            updated_config = update_config(config_updates)
            logger.info(f"更新配置: {config_updates}")
        else:
            updated_config = get_config()
        
        return {
            "status": "success",
            "message": "配置信息" + ("已更新" if config_updates else ""),
            "config": updated_config
        }
    except Exception as e:
        error_msg = f"配置操作失败: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

def test():
    """
    测试函数，用于开发测试
    """
    print("=== Video-Sum MCP 工具测试 ===")
    print("支持的平台:", list_supported_platforms())
    print("支持的格式:", list_supported_formats())
    
    try:
        config = get_config()
        print("配置信息:", config)
    except Exception as e:
        print("配置信息: 使用默认配置")
    
    print("✅ 基础功能测试完成!")

def main():
    """
    主入口函数，处理MCP工具调用
    """
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <function_name> [args...]")
        print("Available functions:")
        print("  test - 运行基础功能测试")
        print("  process_video <url> [format] [use_proxy] [project_dir] [context_text] - 处理内容")
        print("  continue_processing <video_id> <llm_response> [format] [project_dir] - 继续处理")
        print("  list_platforms - 列出支持的平台")
        print("  list_formats - 列出支持的格式")
        print("  configure [api_key] [proxy] [output_dir] - 配置工具")
        return
    
    function_name = sys.argv[1]
    
    try:
        if function_name == "test":
            test()
        elif function_name == "process_video":
            if len(sys.argv) < 3:
                print("Error: process_video requires url parameter")
                return
            url = sys.argv[2]
            output_format = sys.argv[3] if len(sys.argv) > 3 else "markdown"
            use_proxy = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else False
            project_dir = sys.argv[5] if len(sys.argv) > 5 else None
            context_text = sys.argv[6] if len(sys.argv) > 6 else ""
            result = process_video(url, output_format, use_proxy, project_dir, context_text)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif function_name == "continue_processing":
            if len(sys.argv) < 4:
                print("Error: continue_processing requires video_id and llm_response parameters")
                return
            video_id = sys.argv[2]
            llm_response = sys.argv[3]
            output_format = sys.argv[4] if len(sys.argv) > 4 else "markdown"
            project_dir = sys.argv[5] if len(sys.argv) > 5 else None
            result = continue_processing(video_id, llm_response, output_format, project_dir)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif function_name == "list_platforms":
            platforms = list_supported_platforms()
            print(json.dumps(platforms, indent=2, ensure_ascii=False))
        elif function_name == "list_formats":
            formats = list_supported_formats()
            print(json.dumps(formats, indent=2, ensure_ascii=False))
        elif function_name == "configure":
            api_key = sys.argv[2] if len(sys.argv) > 2 else None
            proxy = sys.argv[3] if len(sys.argv) > 3 else None
            output_dir = sys.argv[4] if len(sys.argv) > 4 else None
            result = configure(api_key, proxy, output_dir)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Error: Unknown function '{function_name}'")
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"执行函数 {function_name} 时出错: {str(e)}"
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main() 