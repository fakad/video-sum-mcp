#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
抖音工具模块

包含批处理功能、测试用例管理和统计报告等辅助功能。
"""

import sys
import os
from pathlib import Path
import time
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.douyin_core_processor import DouyinEnhancedProcessor, create_douyin_processor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DouyinBatchProcessor:
    """抖音批处理器"""
    
    def __init__(self):
        self.processor = create_douyin_processor()
    
    def process_douyin_batch(self, test_cases: list):
        """批量处理抖音视频链接"""
        logger.info("🚀 开始批量处理抖音视频链接")
        logger.info(f"📊 待处理链接数量: {len(test_cases)}")
        
        start_time = time.time()
        results = []
        
        try:
            for i, case in enumerate(test_cases, 1):
                url = case.get('url', '')
                context = case.get('context', '')
                description = case.get('description', '')
                
                logger.info(f"\n🔄 处理进度: {i}/{len(test_cases)}")
                
                try:
                    result = self.processor.process_single_douyin_url(url, context, description)
                    
                    # 整理结果
                    processed_result = {
                        'index': i,
                        'url': url,
                        'context': context,
                        'description': description,
                        'success': result is not None,
                        'result': result,
                        'timestamp': time.time()
                    }
                    
                    results.append(processed_result)
                    
                    if result:
                        logger.info(f"✅ 第 {i} 个链接处理成功")
                    else:
                        logger.warning(f"❌ 第 {i} 个链接处理失败")
                        
                except Exception as e:
                    logger.error(f"❌ 第 {i} 个链接处理异常: {str(e)}")
                    error_result = {
                        'index': i,
                        'url': url,
                        'context': context,
                        'description': description,
                        'success': False,
                        'error': str(e),
                        'timestamp': time.time()
                    }
                    results.append(error_result)
            
        except KeyboardInterrupt:
            logger.warning("⚠️ 用户中断了批处理过程")
        except Exception as e:
            logger.error(f"❌ 批处理过程中发生致命错误: {str(e)}")
        finally:
            # 清理资源
            self.processor.cleanup()
        
        # 生成统计报告
        end_time = time.time()
        total_time = end_time - start_time
        
        stats = self.processor.get_statistics()
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 批处理完成统计:")
        logger.info(f"⏱️  总耗时: {total_time:.1f} 秒")
        logger.info(f"📈 处理总数: {stats['total_processed']}")
        logger.info(f"✅ 成功数量: {stats['successful']}")
        logger.info(f"❌ 失败数量: {stats['failed']}")
        logger.info(f"📊 成功率: {stats['success_rate']}")
        logger.info(f"{'='*60}")
        
        return {
            'results': results,
            'statistics': stats,
            'total_time': total_time,
            'summary': {
                'total_cases': len(test_cases),
                'processed_cases': len(results),
                'success_rate': stats['success_rate']
            }
        }


def get_test_cases():
    """获取测试用例列表"""
    return [
        {
            "url": "https://v.douyin.com/iefnMSBa/",
            "context": "生活技巧",
            "description": "日常生活小窍门分享"
        },
        {
            "url": "https://v.douyin.com/iefjhPb4/",
            "context": "科技知识",
            "description": "科技产品评测或知识分享"
        },
        {
            "url": "https://v.douyin.com/iefBqeqR/",
            "context": "教育学习",
            "description": "学习方法或教育内容"
        },
        {
            "url": "https://v.douyin.com/iefSoR8K/",
            "context": "娱乐内容",
            "description": "娱乐性短视频内容"
        },
        {
            "url": "https://v.douyin.com/iefPySLc/",
            "context": "美食制作",
            "description": "美食制作教程或分享"
        }
    ]


def create_batch_processor() -> DouyinBatchProcessor:
    """创建抖音批处理器实例"""
    return DouyinBatchProcessor()


def run_douyin_test():
    """运行抖音测试"""
    logger.info("🎯 开始抖音增强处理器测试")
    
    # 获取测试用例
    test_cases = get_test_cases()
    
    # 创建批处理器
    batch_processor = create_batch_processor()
    
    # 执行批处理
    results = batch_processor.process_douyin_batch(test_cases)
    
    # 输出最终结果
    logger.info("\n🎊 测试完成!")
    logger.info(f"📋 测试报告已生成，共处理 {results['summary']['total_cases']} 个测试用例")
    logger.info(f"✨ 最终成功率: {results['summary']['success_rate']}")
    
    return results


