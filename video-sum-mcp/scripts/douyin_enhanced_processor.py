#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
抖音增强版处理器 - 兼容性桥接文件

此文件保持向后兼容性，所有功能已重构为模块化组件。
新的组件包括：
- douyin_core_processor.py: 抖音核心处理器类和Selenium逻辑
- douyin_utils.py: 批处理功能和测试用例管理
"""

import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.douyin_core_processor import DouyinEnhancedProcessor, create_douyin_processor
from scripts.douyin_utils import DouyinBatchProcessor, create_batch_processor, get_test_cases, run_douyin_test

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 为了向后兼容，导入所有主要组件
__all__ = [
    'DouyinEnhancedProcessor',
    'DouyinBatchProcessor',
    'create_douyin_processor',
    'create_batch_processor',
    'get_test_cases',
    'run_douyin_test'
]


def main():
    """主入口函数"""
    logger.info("🎯 启动抖音增强处理器测试")
    
    try:
        # 运行测试
        results = run_douyin_test()
        
        # 显示最终统计
        if results:
            logger.info("🎊 所有测试已完成!")
            logger.info(f"📈 最终统计: {results['summary']}")
        
    except KeyboardInterrupt:
        logger.info("⚠️ 用户中断程序")
    except Exception as e:
        logger.error(f"❌ 程序运行异常: {str(e)}")


if __name__ == "__main__":
    main() 