#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
抖音核心处理器模块

包含DouyinEnhancedProcessor类的核心处理逻辑。
"""

import sys
import os
from pathlib import Path
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import process_video
from core.services.safe_crawler import get_safe_requester

# 设置日志
logger = logging.getLogger(__name__)


class DouyinEnhancedProcessor:
    """抖音增强版处理器"""
    
    def __init__(self):
        self.driver = None
        self.success_count = 0
        self.total_count = 0
        
    def setup_driver(self):
        """配置Chrome浏览器驱动"""
        chrome_options = Options()
        
        # 基础配置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        
        # 抗检测配置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 移动端模拟（抖音友好）
        mobile_emulation = {
            "deviceName": "iPhone 12 Pro"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        # 随机User-Agent
        user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
        ]
        chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        try:
            # 使用WebDriverManager自动下载和管理ChromeDriver
            logger.info("🔄 自动下载ChromeDriver...")
            service = ChromeService(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("✅ Chrome浏览器驱动初始化成功")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Chrome浏览器初始化失败，尝试无头模式: {str(e)}")
            
            # 尝试无头模式
            try:
                chrome_options.add_argument('--headless')
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                logger.info("✅ Chrome无头模式初始化成功")
                return True
                
            except Exception as e2:
                logger.error(f"❌ Chrome浏览器完全初始化失败: {str(e2)}")
                return False
    
    def simulate_human_behavior(self):
        """模拟人类浏览行为"""
        try:
            # 随机滚动
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(3):
                scroll_to = random.randint(100, scroll_height // 2)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # 随机等待
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            logger.warning(f"模拟人类行为时出现异常: {str(e)}")
    
    def extract_douyin_content_with_selenium(self, url: str) -> dict:
        """使用Selenium提取抖音内容"""
        try:
            logger.info(f"🔄 使用Selenium访问: {url}")
            
            # 访问链接
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(random.uniform(3, 6))
            
            # 检查是否遇到验证码页面
            page_content = self.driver.page_source.lower()
            if '验证码中间页' in page_content or 'captcha' in page_content:
                logger.warning("⚠️ 遇到验证码页面，尝试人类行为模拟")
                self.simulate_human_behavior()
                time.sleep(random.uniform(5, 10))
                
                # 重新获取页面内容
                page_content = self.driver.page_source.lower()
                if '验证码中间页' in page_content or 'captcha' in page_content:
                    logger.error("❌ 仍然遇到验证码页面，无法继续")
                    return None
            
            # 提取页面信息
            try:
                # 尝试找到视频标题
                title_element = None
                title_selectors = [
                    "h1[data-e2e='video-desc']",
                    ".video-info-detail h1",
                    "[data-e2e='video-desc']",
                    "h1",
                    ".desc"
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if title_element and title_element.text.strip():
                            break
                    except:
                        continue
                
                title = title_element.text.strip() if title_element else "无法获取标题"
                
                # 尝试找到作者信息
                author_element = None
                author_selectors = [
                    "[data-e2e='video-author-name']",
                    ".account-name",
                    ".author-name",
                    ".username"
                ]
                
                for selector in author_selectors:
                    try:
                        author_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if author_element and author_element.text.strip():
                            break
                    except:
                        continue
                
                author = author_element.text.strip() if author_element else "未知作者"
                
                # 获取页面内容
                content = self.driver.page_source
                
                result = {
                    'title': title,
                    'author': author,
                    'content': content,
                    'url': url,
                    'success': True
                }
                
                logger.info(f"✅ Selenium提取成功: {title}")
                return result
                
            except Exception as e:
                logger.error(f"❌ 内容提取失败: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Selenium访问失败: {str(e)}")
            return None
    
    def process_single_douyin_url(self, url: str, context: str = "", description: str = ""):
        """处理单个抖音URL"""
        self.total_count += 1
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"🎯 处理第 {self.total_count} 个URL:")
            logger.info(f"🔗 URL: {url}")
            if context:
                logger.info(f"📝 上下文: {context}")
            if description:
                logger.info(f"📋 描述: {description}")
            logger.info(f"{'='*60}")
            
            # 首先尝试常规方法
            logger.info("🔄 首次尝试：使用常规方法处理...")
            
            try:
                result = process_video(url)
                if result and result.get('title') and len(result.get('title', '').strip()) > 5:
                    logger.info("✅ 常规方法处理成功!")
                    self.success_count += 1
                    return result
                else:
                    logger.warning("⚠️ 常规方法返回结果不完整，尝试增强方法...")
            except Exception as e:
                logger.warning(f"⚠️ 常规方法失败: {str(e)}，尝试增强方法...")
            
            # 如果常规方法失败，使用Selenium增强处理
            if not self.driver:
                logger.info("🔄 初始化Selenium环境...")
                if not self.setup_driver():
                    logger.error("❌ Selenium环境初始化失败，无法继续")
                    return None
            
            # 使用Selenium提取内容
            selenium_result = self.extract_douyin_content_with_selenium(url)
            
            if selenium_result:
                # 再次尝试用主程序处理
                logger.info("🔄 使用主程序重新处理Selenium提取的内容...")
                
                try:
                    result = process_video(url)
                    if result and result.get('title'):
                        logger.info("✅ 增强方法处理成功!")
                        self.success_count += 1
                        return result
                    else:
                        logger.warning("⚠️ 增强方法仍然无法完全处理")
                        return selenium_result
                        
                except Exception as e:
                    logger.warning(f"⚠️ 增强方法处理异常: {str(e)}")
                    return selenium_result
            else:
                logger.error("❌ Selenium提取也失败了")
                return None
                
        except Exception as e:
            logger.error(f"❌ 处理URL时发生致命错误: {str(e)}")
            return None
        
        finally:
            # 处理间隔（避免过于频繁的请求）
            if self.total_count < 10:  # 还有更多URL需要处理
                sleep_time = random.uniform(3, 8)
                logger.info(f"⏳ 等待 {sleep_time:.1f} 秒后处理下一个...")
                time.sleep(sleep_time)
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Selenium驱动已关闭")
            except Exception as e:
                logger.warning(f"⚠️ 关闭Selenium驱动时出现异常: {str(e)}")
            finally:
                self.driver = None
    
    def get_statistics(self):
        """获取处理统计信息"""
        success_rate = (self.success_count / self.total_count * 100) if self.total_count > 0 else 0
        
        return {
            'total_processed': self.total_count,
            'successful': self.success_count,
            'failed': self.total_count - self.success_count,
            'success_rate': f"{success_rate:.1f}%"
        }


def create_douyin_processor() -> DouyinEnhancedProcessor:
    """创建抖音增强处理器实例"""
    return DouyinEnhancedProcessor()


