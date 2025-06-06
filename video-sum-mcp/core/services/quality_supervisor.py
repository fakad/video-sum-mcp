"""
智能质量监督模块

用于监督批量处理过程中的文档质量，防止生成相同或通用模板文档，
集成LLM辅助诊断，确保每个视频链接都能生成真实、有价值的内容。
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class DocumentQualityMetrics:
    """文档质量指标"""
    url: str
    title: str
    content_length: int
    unique_keywords: int
    content_hash: str
    platform: str
    author: str
    timestamp: float
    quality_score: float
    issues: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BatchQualityReport:
    """批量处理质量报告"""
    batch_id: str
    total_documents: int
    unique_documents: int
    duplicate_documents: int
    template_documents: int
    quality_issues: List[str]
    platform_stats: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class QualitySupervisor:
    """智能质量监督器"""
    
    def __init__(self, 
                 enable_llm_assistance: bool = True,
                 similarity_threshold: float = 0.85,
                 min_quality_score: float = 0.6):
        """
        初始化质量监督器
        
        参数:
            enable_llm_assistance: 是否启用LLM辅助诊断
            similarity_threshold: 文档相似度阈值
            min_quality_score: 最低质量分数
        """
        self.enable_llm_assistance = enable_llm_assistance
        self.similarity_threshold = similarity_threshold
        self.min_quality_score = min_quality_score
        
        # 监督数据存储
        self.batch_history: List[BatchQualityReport] = []
        self.document_metrics: List[DocumentQualityMetrics] = []
        self.content_hashes: Dict[str, List[str]] = defaultdict(list)  # hash -> urls
        
        # 通用模板检测关键词
        self.template_keywords = {
            "综合知识", "未知标题", "未知作者", "视频", "内容分析",
            "知识图谱", "核心概念", "实用技巧", "深度见解"
        }
        
        # 平台特定质量标准
        self.platform_standards = {
            "douyin": {
                "min_title_length": 5,
                "min_content_length": 200,
                "required_fields": ["title", "author", "description"],
                "forbidden_titles": ["视频", "抖音视频", "未知标题"]
            },
            "xiaohongshu": {
                "min_title_length": 3,
                "min_content_length": 150,
                "required_fields": ["title", "author"],
                "forbidden_titles": ["小红书", "笔记", "未知标题"]
            },
            "zhihu": {
                "min_title_length": 8,
                "min_content_length": 300,
                "required_fields": ["title", "author"],
                "forbidden_titles": ["知乎", "回答", "未知标题"]
            },
            "bilibili": {
                "min_title_length": 5,
                "min_content_length": 200,
                "required_fields": ["title", "author"],
                "forbidden_titles": ["B站", "视频", "未知标题"]
            }
        }
        
        logger.info(f"初始化质量监督器: LLM辅助={'启用' if enable_llm_assistance else '禁用'}")
    
    def analyze_document_quality(self, 
                                url: str, 
                                content_data: Dict[str, Any], 
                                generated_content: str) -> DocumentQualityMetrics:
        """
        分析单个文档的质量
        
        参数:
            url: 视频URL
            content_data: 提取的内容数据
            generated_content: 生成的文档内容
            
        返回:
            文档质量指标
        """
        metadata = content_data.get('metadata', {})
        title = metadata.get('title', '未知标题')
        author = metadata.get('author', '未知作者')
        platform = content_data.get('platform', 'unknown')
        
        # 计算内容哈希
        content_hash = hashlib.md5(generated_content.encode('utf-8')).hexdigest()
        
        # 分析质量指标
        issues = []
        quality_score = 1.0
        
        # 1. 检查是否为通用模板
        template_score = self._check_template_content(title, generated_content)
        if template_score > 0.7:
            issues.append(f"疑似通用模板 (相似度: {template_score:.2f})")
            quality_score -= 0.4
        
        # 2. 检查平台特定标准
        platform_issues = self._check_platform_standards(platform, title, author, generated_content)
        issues.extend(platform_issues)
        quality_score -= len(platform_issues) * 0.1
        
        # 3. 检查内容唯一性
        if content_hash in [h for hashes in self.content_hashes.values() for h in hashes]:
            issues.append("内容与其他文档重复")
            quality_score -= 0.3
        
        # 4. 计算内容丰富度
        unique_keywords = len(set(generated_content.split())) if generated_content else 0
        if unique_keywords < 50:
            issues.append(f"内容过于简单 (唯一词汇: {unique_keywords})")
            quality_score -= 0.2
        
        # 5. 检查标题和作者有效性
        if title in self.platform_standards.get(platform, {}).get('forbidden_titles', []):
            issues.append(f"标题无效: '{title}'")
            quality_score -= 0.3
        
        if author == '未知作者':
            issues.append("作者信息缺失")
            quality_score -= 0.1
        
        quality_score = max(0.0, quality_score)
        
        metrics = DocumentQualityMetrics(
            url=url,
            title=title,
            content_length=len(generated_content),
            unique_keywords=unique_keywords,
            content_hash=content_hash,
            platform=platform,
            author=author,
            timestamp=time.time(),
            quality_score=quality_score,
            issues=issues
        )
        
        # 记录到监督数据
        self.document_metrics.append(metrics)
        self.content_hashes[content_hash].append(url)
        
        return metrics
    
    def _check_template_content(self, title: str, content: str) -> float:
        """检查是否为通用模板内容"""
        template_indicators = 0
        total_indicators = len(self.template_keywords)
        
        content_lower = content.lower()
        title_lower = title.lower()
        
        for keyword in self.template_keywords:
            if keyword in content_lower or keyword in title_lower:
                template_indicators += 1
        
        return template_indicators / total_indicators if total_indicators > 0 else 0.0
    
    def _check_platform_standards(self, platform: str, title: str, author: str, content: str) -> List[str]:
        """检查平台特定质量标准"""
        issues = []
        standards = self.platform_standards.get(platform, {})
        
        # 检查标题长度
        min_title_length = standards.get('min_title_length', 3)
        if len(title) < min_title_length:
            issues.append(f"标题过短 (长度: {len(title)}, 要求: >={min_title_length})")
        
        # 检查内容长度
        min_content_length = standards.get('min_content_length', 100)
        if len(content) < min_content_length:
            issues.append(f"内容过短 (长度: {len(content)}, 要求: >={min_content_length})")
        
        # 检查禁用标题
        forbidden_titles = standards.get('forbidden_titles', [])
        if title in forbidden_titles:
            issues.append(f"使用了禁用标题: '{title}'")
        
        return issues
    
    def analyze_batch_quality(self, batch_results: List[Dict[str, Any]]) -> BatchQualityReport:
        """
        分析批量处理的整体质量
        
        参数:
            batch_results: 批量处理结果列表
            
        返回:
            批量质量报告
        """
        batch_id = f"batch_{int(time.time())}"
        total_documents = len(batch_results)
        
        # 统计重复和模板文档
        content_hashes = {}
        template_count = 0
        platform_stats = defaultdict(lambda: {"total": 0, "success": 0, "quality_issues": 0})
        quality_issues = []
        
        for result in batch_results:
            if result.get('status') == 'success':
                # 这里需要实际的文档内容来分析，暂时用模拟数据
                url = result.get('url', '')
                platform = self._detect_platform(url)
                title = result.get('title', '未知标题')
                
                platform_stats[platform]["total"] += 1
                platform_stats[platform]["success"] += 1
                
                # 检查是否为模板内容
                if self._is_template_title(title):
                    template_count += 1
                    platform_stats[platform]["quality_issues"] += 1
                    quality_issues.append(f"检测到模板文档: {url} (标题: {title})")
        
        # 计算唯一文档数
        unique_documents = total_documents - template_count
        duplicate_documents = total_documents - len(set(content_hashes.keys()))
        
        # 生成建议
        recommendations = self._generate_recommendations(platform_stats, quality_issues)
        
        report = BatchQualityReport(
            batch_id=batch_id,
            total_documents=total_documents,
            unique_documents=unique_documents,
            duplicate_documents=duplicate_documents,
            template_documents=template_count,
            quality_issues=quality_issues,
            platform_stats=dict(platform_stats),
            recommendations=recommendations,
            timestamp=time.time()
        )
        
        self.batch_history.append(report)
        
        # 如果质量问题严重，触发警报
        if template_count > total_documents * 0.5:  # 超过50%是模板
            self._trigger_quality_alert(report)
        
        return report
    
    def _detect_platform(self, url: str) -> str:
        """检测URL对应的平台"""
        url_lower = url.lower()
        if "douyin.com" in url_lower:
            return "douyin"
        elif "xiaohongshu.com" in url_lower:
            return "xiaohongshu"
        elif "zhihu.com" in url_lower:
            return "zhihu"
        elif "bilibili.com" in url_lower:
            return "bilibili"
        else:
            return "unknown"
    
    def _is_template_title(self, title: str) -> bool:
        """检查标题是否为模板标题"""
        template_titles = ["视频", "未知标题", "综合知识", "核心概念与理论"]
        return title in template_titles or any(keyword in title for keyword in self.template_keywords)
    
    def _generate_recommendations(self, platform_stats: Dict, quality_issues: List[str]) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        # 检查各平台质量
        for platform, stats in platform_stats.items():
            if stats["quality_issues"] > stats["success"] * 0.3:  # 质量问题超过30%
                recommendations.append(f"平台 {platform} 质量问题较多，建议检查提取器配置")
        
        # 检查整体质量问题
        if len(quality_issues) > 0:
            recommendations.append("检测到模板文档，建议:")
            recommendations.append("1. 验证视频链接的有效性")
            recommendations.append("2. 检查网络连接和访问权限")
            recommendations.append("3. 为难以提取的链接提供上下文信息")
            recommendations.append("4. 考虑更新提取器算法")
        
        return recommendations
    
    def _trigger_quality_alert(self, report: BatchQualityReport) -> None:
        """触发质量警报"""
        logger.warning("🚨 质量监督警报!")
        logger.warning(f"批次 {report.batch_id} 检测到严重质量问题:")
        logger.warning(f"- 总文档数: {report.total_documents}")
        logger.warning(f"- 模板文档数: {report.template_documents}")
        logger.warning(f"- 质量问题: {len(report.quality_issues)}")
        
        for issue in report.quality_issues[:5]:  # 只显示前5个问题
            logger.warning(f"  • {issue}")
        
        if self.enable_llm_assistance:
            self._request_llm_assistance(report)
    
    def _request_llm_assistance(self, report: BatchQualityReport) -> None:
        """请求LLM辅助诊断"""
        logger.info("🤖 请求LLM辅助诊断...")
        
        # 这里可以集成实际的LLM API调用
        # 暂时记录诊断请求
        diagnosis_request = {
            "timestamp": time.time(),
            "batch_id": report.batch_id,
            "issues": report.quality_issues,
            "platform_stats": report.platform_stats,
            "request_type": "quality_diagnosis"
        }
        
        logger.info("LLM诊断请求已记录，建议人工审查批量处理结果")
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """获取质量监督总结"""
        if not self.document_metrics:
            return {"status": "no_data", "message": "暂无监督数据"}
        
        total_docs = len(self.document_metrics)
        high_quality_docs = sum(1 for m in self.document_metrics if m.quality_score >= self.min_quality_score)
        
        # 统计各平台质量
        platform_quality = defaultdict(list)
        for metric in self.document_metrics:
            platform_quality[metric.platform].append(metric.quality_score)
        
        platform_avg_quality = {
            platform: sum(scores) / len(scores) if scores else 0.0
            for platform, scores in platform_quality.items()
        }
        
        # 统计常见问题
        all_issues = []
        for metric in self.document_metrics:
            all_issues.extend(metric.issues)
        
        issue_counts = defaultdict(int)
        for issue in all_issues:
            issue_counts[issue] += 1
        
        return {
            "total_documents": total_docs,
            "high_quality_documents": high_quality_docs,
            "quality_rate": high_quality_docs / total_docs if total_docs > 0 else 0.0,
            "platform_quality": platform_avg_quality,
            "common_issues": dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            "duplicate_content_groups": len([h for h, urls in self.content_hashes.items() if len(urls) > 1]),
            "recent_batches": len(self.batch_history)
        }
    
    def save_report(self, output_dir: str = "temp/quality_reports") -> str:
        """保存质量监督报告"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        report_file = output_path / f"quality_report_{timestamp}.json"
        
        report_data = {
            "summary": self.get_quality_summary(),
            "document_metrics": [m.to_dict() for m in self.document_metrics],
            "batch_history": [b.to_dict() for b in self.batch_history],
            "generated_at": time.time()
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"质量监督报告已保存: {report_file}")
        return str(report_file)

# 全局质量监督器实例
quality_supervisor = QualitySupervisor() 