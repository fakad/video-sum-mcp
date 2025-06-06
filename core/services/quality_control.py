#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识图谱质量控制模块
负责评估生成文档的质量，并提供改进建议
支持量化评估 + LLM智能评估的混合模式
"""

import logging
import re
import json
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger("video-sum-mcp.quality_control")

@dataclass
class LLMAssessmentResult:
    """LLM评估结果"""
    content_depth: float = 0.0      # 内容深度 (0-100)
    logical_coherence: float = 0.0  # 逻辑连贯性 (0-100)
    practicality: float = 0.0       # 实用性 (0-100)
    professionalism: float = 0.0    # 专业性 (0-100)
    completeness: float = 0.0       # 完整性 (0-100)
    innovation: float = 0.0         # 创新性 (0-100)
    overall_score: float = 0.0      # LLM综合评分 (0-100)
    improvement_suggestions: List[str] = None
    assessment_confidence: float = 0.0  # 评估置信度 (0-1)
    
    def __post_init__(self):
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []

@dataclass
class QualityMetrics:
    """质量评估指标"""
    knowledge_density_score: float = 0.0  # 知识密度评分 (0-100)
    content_quality_score: float = 0.0    # 内容质量评分 (0-100)
    llm_assessment_score: float = 0.0     # LLM评估评分 (0-100)
    overall_score: float = 0.0             # 综合评分 (0-100)
    
    # 详细指标
    core_concepts_count: int = 0
    methodologies_count: int = 0
    practical_tips_count: int = 0
    insights_count: int = 0
    frameworks_count: int = 0
    actionable_advice_count: int = 0
    case_studies_count: int = 0
    
    # 内容特征
    total_content_length: int = 0
    meaningful_content_ratio: float = 0.0
    structure_completeness: float = 0.0
    
    # LLM评估详情
    llm_result: Optional[LLMAssessmentResult] = None
    
    # 改进建议
    improvement_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.improvement_suggestions is None:
            self.improvement_suggestions = []

class LLMQualityAssessor:
    """LLM质量评估器"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.config = llm_config or {}
        self.enabled = self.config.get('enabled', True)
        self.provider = self.config.get('provider', 'openai')
        self.model = self.config.get('model', 'gpt-3.5-turbo')
        self.api_key = self.config.get('api_key', '')
        self.base_url = self.config.get('base_url', '')
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 2)
        
        # 权重配置
        self.weights = {
            'content_depth': 0.25,
            'logical_coherence': 0.20,
            'practicality': 0.25,
            'professionalism': 0.15,
            'completeness': 0.10,
            'innovation': 0.05
        }
        
        logger.info(f"LLM质量评估器初始化，提供商: {self.provider}, 模型: {self.model}, 启用: {self.enabled}")
    
    def assess_document(self, document: str, content_type: str = "general") -> Optional[LLMAssessmentResult]:
        """
        使用LLM评估文档质量
        
        参数:
            document: 待评估的文档
            content_type: 内容类型
            
        返回:
            LLMAssessmentResult或None（如果评估失败）
        """
        
        if not self.enabled:
            logger.info("LLM评估已禁用，跳过LLM评估")
            return None
        
        if not self.api_key:
            logger.warning("未配置LLM API密钥，跳过LLM评估")
            return None
        
        try:
            logger.info("开始LLM质量评估")
            
            # 生成评估prompt
            prompt = self._generate_assessment_prompt(document, content_type)
            
            # 调用LLM
            response = self._call_llm(prompt)
            
            if response:
                # 解析评估结果
                result = self._parse_assessment_result(response)
                logger.info(f"LLM评估完成，综合评分: {result.overall_score:.1f}")
                return result
            else:
                logger.warning("LLM调用失败，跳过LLM评估")
                return None
                
        except Exception as e:
            logger.error(f"LLM评估过程中出错: {str(e)}")
            return None
    
    def _generate_assessment_prompt(self, document: str, content_type: str) -> str:
        """生成LLM评估prompt"""
        
        content_type_descriptions = {
            'finance': '财经金融类内容',
            'business': '商业管理类内容',
            'technology': '技术科技类内容',
            'education': '教育学习类内容',
            'management': '管理类内容',
            'lifestyle': '生活方式类内容',
            'general': '通用类内容'
        }
        
        type_desc = content_type_descriptions.get(content_type, '通用类内容')
        
        prompt = f"""你是一个专业的知识内容质量评估专家。请对以下{type_desc}的知识图谱文档进行全面质量评估。

【待评估文档】
{document}

【评估维度说明】
1. 内容深度 (0-100分): 知识是否有深度，是否提供了有价值的见解和分析
2. 逻辑连贯性 (0-100分): 各部分内容是否逻辑清晰，结构合理，前后呼应
3. 实用性 (0-100分): 是否提供了可操作的建议、方法和实践指导
4. 专业性 (0-100分): 术语使用是否准确，分析是否专业，是否体现专业水准
5. 完整性 (0-100分): 是否全面覆盖了主题的重要方面，结构是否完整
6. 创新性 (0-100分): 是否有独特的观点、新颖的分析角度或创新的见解

【评估标准】
- 90-100分: 优秀，内容非常有价值，质量很高
- 80-89分: 良好，内容有价值，质量较高
- 70-79分: 合格，内容基本有价值，质量一般
- 60-69分: 需要改进，内容价值有限
- 0-59分: 不合格，内容价值很低或存在严重问题

【输出要求】
请严格按照以下JSON格式输出评估结果，不要包含任何其他文字：

{{
    "content_depth": 85,
    "logical_coherence": 90,
    "practicality": 80,
    "professionalism": 88,
    "completeness": 85,
    "innovation": 75,
    "overall_score": 84,
    "improvement_suggestions": [
        "建议增加更多具体的实践案例",
        "可以进一步深化某些理论分析"
    ],
    "assessment_confidence": 0.9
}}

请开始评估："""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用LLM API"""
        
        for attempt in range(self.max_retries + 1):
            try:
                if self.provider.lower() == 'openai':
                    return self._call_openai(prompt)
                elif self.provider.lower() == 'claude':
                    return self._call_claude(prompt)
                else:
                    logger.error(f"不支持的LLM提供商: {self.provider}")
                    return None
                    
            except Exception as e:
                logger.warning(f"LLM调用尝试 {attempt + 1} 失败: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error("LLM调用达到最大重试次数，放弃")
                    return None
    
    def _call_openai(self, prompt: str) -> Optional[str]:
        """调用OpenAI API"""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else None,
                timeout=self.timeout
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的知识内容质量评估专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.error("未安装openai库，无法使用OpenAI API")
            return None
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            return None
    
    def _call_claude(self, prompt: str) -> Optional[str]:
        """调用Claude API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=self.timeout
            )
            
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except ImportError:
            logger.error("未安装anthropic库，无法使用Claude API")
            return None
        except Exception as e:
            logger.error(f"Claude API调用失败: {str(e)}")
            return None
    
    def _parse_assessment_result(self, response: str) -> LLMAssessmentResult:
        """解析LLM评估结果"""
        
        try:
            # 尝试提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # 计算综合评分
                overall_score = sum(
                    data.get(key.replace('_', ''), 0) * weight 
                    for key, weight in self.weights.items()
                )
                
                return LLMAssessmentResult(
                    content_depth=float(data.get('content_depth', 0)),
                    logical_coherence=float(data.get('logical_coherence', 0)),
                    practicality=float(data.get('practicality', 0)),
                    professionalism=float(data.get('professionalism', 0)),
                    completeness=float(data.get('completeness', 0)),
                    innovation=float(data.get('innovation', 0)),
                    overall_score=float(data.get('overall_score', overall_score)),
                    improvement_suggestions=data.get('improvement_suggestions', []),
                    assessment_confidence=float(data.get('assessment_confidence', 0.8))
                )
            else:
                raise ValueError("未找到有效的JSON格式")
                
        except Exception as e:
            logger.error(f"解析LLM评估结果失败: {str(e)}")
            logger.debug(f"原始响应: {response}")
            
            # 返回默认结果
            return LLMAssessmentResult(
                content_depth=70.0,
                logical_coherence=70.0,
                practicality=70.0,
                professionalism=70.0,
                completeness=70.0,
                innovation=60.0,
                overall_score=68.0,
                improvement_suggestions=["LLM评估解析失败，建议人工审核"],
                assessment_confidence=0.3
            )

class QualityStandards:
    """质量标准定义"""
    
    # 基础通过标准
    PASS_THRESHOLD = 70.0
    EXCELLENT_THRESHOLD = 85.0
    
    # 知识点数量标准
    MIN_CORE_CONCEPTS = 3
    IDEAL_CORE_CONCEPTS = 5
    MIN_METHODOLOGIES = 2
    IDEAL_METHODOLOGIES = 4
    MIN_PRACTICAL_TIPS = 3
    IDEAL_PRACTICAL_TIPS = 6
    MIN_INSIGHTS = 2
    IDEAL_INSIGHTS = 4
    
    # 内容长度标准
    MIN_CONTENT_LENGTH = 1000
    IDEAL_CONTENT_LENGTH = 3000
    MAX_CONTENT_LENGTH = 8000
    
    # 权重配置（支持LLM评估）
    KNOWLEDGE_DENSITY_WEIGHT = 0.3
    CONTENT_QUALITY_WEIGHT = 0.3
    LLM_ASSESSMENT_WEIGHT = 0.4  # LLM评估权重最高
    
    @classmethod
    def get_adjusted_standards(cls, content_type: str, original_content_length: int) -> Dict[str, Any]:
        """根据内容类型和原始内容长度调整标准"""
        
        # 基础调整因子
        adjustment_factor = 1.0
        
        # 根据原始内容长度调整期望值
        if original_content_length < 500:
            adjustment_factor = 0.7  # 降低期望
        elif original_content_length < 200:
            adjustment_factor = 0.5  # 大幅降低期望
        elif original_content_length > 2000:
            adjustment_factor = 1.2  # 提高期望
        
        # 根据内容类型调整
        type_adjustments = {
            'management': 1.1,      # 管理类要求较高的实用性
            'technology': 1.0,      # 技术类标准要求
            'finance': 1.1,         # 财经类要求较高的专业性
            'business': 1.0,        # 商业类标准要求
            'education': 1.2,       # 教育类要求最高
            'lifestyle': 0.8,       # 生活类要求较低
            'general': 0.9          # 通用类稍低要求
        }
        
        type_factor = type_adjustments.get(content_type, 1.0)
        final_factor = adjustment_factor * type_factor
        
        return {
            'pass_threshold': max(cls.PASS_THRESHOLD * final_factor, 50.0),
            'min_core_concepts': max(int(cls.MIN_CORE_CONCEPTS * final_factor), 2),
            'min_methodologies': max(int(cls.MIN_METHODOLOGIES * final_factor), 1),
            'min_practical_tips': max(int(cls.MIN_PRACTICAL_TIPS * final_factor), 2),
            'min_insights': max(int(cls.MIN_INSIGHTS * final_factor), 1),
            'adjustment_factor': final_factor
        }

class QualityAssessment:
    """质量评估器（支持量化评估 + LLM智能评估）"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.standards = QualityStandards()
        self.llm_assessor = LLMQualityAssessor(llm_config)
    
    def assess_document(self, document: str, content_type: str = "general", 
                       original_content_length: int = 1000) -> QualityMetrics:
        """
        评估文档质量（混合模式：量化 + LLM）
        
        参数:
            document: 待评估的markdown文档
            content_type: 内容类型
            original_content_length: 原始内容长度
            
        返回:
            QualityMetrics: 质量评估结果
        """
        
        logger.info(f"开始混合模式质量评估，内容类型: {content_type}，原始长度: {original_content_length}")
        
        # 获取调整后的标准
        adjusted_standards = self.standards.get_adjusted_standards(content_type, original_content_length)
        
        # 1. 量化评估
        sections = self._extract_sections(document)
        knowledge_counts = self._count_knowledge_items(sections)
        
        knowledge_density_score = self._calculate_knowledge_density_score(
            knowledge_counts, adjusted_standards
        )
        
        content_quality_score = self._calculate_content_quality_score(
            document, sections, adjusted_standards
        )
        
        # 2. LLM智能评估
        llm_result = self.llm_assessor.assess_document(document, content_type)
        llm_assessment_score = llm_result.overall_score if llm_result else 0.0
        
        # 3. 计算综合评分
        if llm_result and llm_result.assessment_confidence > 0.5:
            # LLM评估可信时，使用混合评分
            overall_score = (
                knowledge_density_score * self.standards.KNOWLEDGE_DENSITY_WEIGHT +
                content_quality_score * self.standards.CONTENT_QUALITY_WEIGHT +
                llm_assessment_score * self.standards.LLM_ASSESSMENT_WEIGHT
            )
            logger.info(f"使用混合评分模式，LLM置信度: {llm_result.assessment_confidence:.2f}")
        else:
            # LLM评估不可用时，降级到量化评估
            overall_score = (
                knowledge_density_score * 0.6 +
                content_quality_score * 0.4
            )
            logger.info("LLM评估不可用，使用量化评估模式")
        
        # 4. 生成综合改进建议
        improvement_suggestions = self._generate_comprehensive_improvement_suggestions(
            knowledge_counts, content_quality_score, adjusted_standards, llm_result
        )
        
        # 构建评估结果
        metrics = QualityMetrics(
            knowledge_density_score=knowledge_density_score,
            content_quality_score=content_quality_score,
            llm_assessment_score=llm_assessment_score,
            overall_score=overall_score,
            core_concepts_count=knowledge_counts['core_concepts'],
            methodologies_count=knowledge_counts['methodologies'],
            practical_tips_count=knowledge_counts['practical_tips'],
            insights_count=knowledge_counts['insights'],
            frameworks_count=knowledge_counts['frameworks'],
            actionable_advice_count=knowledge_counts['actionable_advice'],
            case_studies_count=knowledge_counts['case_studies'],
            total_content_length=len(document),
            meaningful_content_ratio=self._calculate_meaningful_content_ratio(document),
            structure_completeness=self._calculate_structure_completeness(sections),
            llm_result=llm_result,
            improvement_suggestions=improvement_suggestions
        )
        
        logger.info(f"混合模式质量评估完成，综合评分: {overall_score:.1f}")
        
        return metrics
    
    def _extract_sections(self, document: str) -> Dict[str, str]:
        """提取文档各部分内容"""
        sections = {}
        
        # 定义各部分的标识符
        section_patterns = {
            'core_concepts': r'##.*?核心概念.*?\n(.*?)(?=##|\Z)',
            'methodologies': r'##.*?方法论.*?\n(.*?)(?=##|\Z)',
            'practical_tips': r'##.*?实用技巧.*?\n(.*?)(?=##|\Z)',
            'insights': r'##.*?深度见解.*?\n(.*?)(?=##|\Z)',
            'frameworks': r'##.*?分析工具.*?\n(.*?)(?=##|\Z)',
            'actionable_advice': r'##.*?实践指南.*?\n(.*?)(?=##|\Z)',
            'case_studies': r'##.*?案例分析.*?\n(.*?)(?=##|\Z)'
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, document, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(1).strip()
            else:
                sections[section_name] = ""
        
        return sections
    
    def _count_knowledge_items(self, sections: Dict[str, str]) -> Dict[str, int]:
        """统计各类知识点数量"""
        counts = {}
        
        for section_name, content in sections.items():
            if not content:
                counts[section_name] = 0
                continue
            
            # 统计有意义的条目数量
            # 排除占位符和过于简单的内容
            lines = content.split('\n')
            meaningful_items = 0
            
            for line in lines:
                line = line.strip()
                if (line and 
                    not line.startswith('*暂无') and 
                    not line.startswith('待') and
                    len(line) > 20 and
                    ('：' in line or ':' in line or line.startswith('- ') or line.startswith('**'))):
                    meaningful_items += 1
            
            counts[section_name] = meaningful_items
        
        return counts
    
    def _calculate_knowledge_density_score(self, knowledge_counts: Dict[str, int], 
                                         adjusted_standards: Dict[str, Any]) -> float:
        """计算知识密度评分"""
        
        # 各类知识点的权重
        weights = {
            'core_concepts': 5,
            'methodologies': 4,
            'practical_tips': 3,
            'insights': 6,
            'frameworks': 4,
            'actionable_advice': 3,
            'case_studies': 4
        }
        
        total_score = 0
        max_possible_score = 0
        
        for knowledge_type, count in knowledge_counts.items():
            weight = weights.get(knowledge_type, 3)
            
            # 计算该类知识点的得分
            if knowledge_type == 'core_concepts':
                min_count = adjusted_standards['min_core_concepts']
                ideal_count = min_count + 2
            elif knowledge_type == 'methodologies':
                min_count = adjusted_standards['min_methodologies']
                ideal_count = min_count + 2
            elif knowledge_type == 'practical_tips':
                min_count = adjusted_standards['min_practical_tips']
                ideal_count = min_count + 3
            elif knowledge_type == 'insights':
                min_count = adjusted_standards['min_insights']
                ideal_count = min_count + 2
            else:
                min_count = 1
                ideal_count = 3
            
            # 计算得分：达到最低要求得60%分数，达到理想要求得100%分数
            if count >= ideal_count:
                score = weight * 100
            elif count >= min_count:
                ratio = 0.6 + 0.4 * (count - min_count) / (ideal_count - min_count)
                score = weight * 100 * ratio
            else:
                score = weight * 100 * count / min_count * 0.6
            
            total_score += score
            max_possible_score += weight * 100
        
        return min(total_score / max_possible_score * 100, 100.0) if max_possible_score > 0 else 0.0
    
    def _calculate_content_quality_score(self, document: str, sections: Dict[str, str], 
                                       adjusted_standards: Dict[str, Any]) -> float:
        """计算内容质量评分"""
        
        scores = []
        
        # 1. 内容长度适度性 (25%)
        length_score = self._evaluate_content_length(len(document))
        scores.append(('length', length_score, 0.25))
        
        # 2. 结构完整性 (30%)
        structure_score = self._calculate_structure_completeness(sections)
        scores.append(('structure', structure_score, 0.30))
        
        # 3. 内容实用性 (25%)
        practicality_score = self._evaluate_practicality(sections)
        scores.append(('practicality', practicality_score, 0.25))
        
        # 4. 专业性和深度 (20%)
        professionalism_score = self._evaluate_professionalism(document)
        scores.append(('professionalism', professionalism_score, 0.20))
        
        # 计算加权总分
        total_score = sum(score * weight for _, score, weight in scores)
        
        return min(total_score, 100.0)
    
    def _evaluate_content_length(self, length: int) -> float:
        """评估内容长度的适度性"""
        if length < self.standards.MIN_CONTENT_LENGTH:
            return length / self.standards.MIN_CONTENT_LENGTH * 60  # 太短扣分
        elif length <= self.standards.IDEAL_CONTENT_LENGTH:
            return 60 + (length - self.standards.MIN_CONTENT_LENGTH) / (self.standards.IDEAL_CONTENT_LENGTH - self.standards.MIN_CONTENT_LENGTH) * 40
        elif length <= self.standards.MAX_CONTENT_LENGTH:
            return 100  # 理想长度
        else:
            # 太长稍微扣分
            excess_ratio = (length - self.standards.MAX_CONTENT_LENGTH) / self.standards.MAX_CONTENT_LENGTH
            return max(100 - excess_ratio * 20, 80)
    
    def _calculate_structure_completeness(self, sections: Dict[str, str]) -> float:
        """计算结构完整性"""
        required_sections = ['core_concepts', 'methodologies', 'practical_tips', 'insights']
        optional_sections = ['frameworks', 'actionable_advice', 'case_studies']
        
        # 必需部分得分 (70%)
        required_score = 0
        for section in required_sections:
            if sections.get(section) and len(sections[section]) > 50:
                required_score += 70 / len(required_sections)
        
        # 可选部分得分 (30%)
        optional_score = 0
        for section in optional_sections:
            if sections.get(section) and len(sections[section]) > 50:
                optional_score += 30 / len(optional_sections)
        
        return required_score + optional_score
    
    def _evaluate_practicality(self, sections: Dict[str, str]) -> float:
        """评估实用性"""
        practical_sections = ['practical_tips', 'actionable_advice', 'methodologies']
        
        total_score = 0
        for section in practical_sections:
            content = sections.get(section, "")
            if content:
                # 检查是否包含具体的、可操作的建议
                actionable_keywords = ['具体', '步骤', '方法', '技巧', '建议', '策略', '实施', '执行', '操作']
                keyword_matches = sum(1 for keyword in actionable_keywords if keyword in content)
                section_score = min(keyword_matches * 10, 100)
                total_score += section_score
        
        return total_score / len(practical_sections) if practical_sections else 0
    
    def _evaluate_professionalism(self, document: str) -> float:
        """评估专业性和深度"""
        
        # 专业术语和概念的使用
        professional_indicators = [
            '理论', '框架', '模型', '机制', '原理', '体系', '策略', '方法论',
            '分析', '评估', '优化', '管理', '控制', '实施', '应用', '研究'
        ]
        
        indicator_count = sum(1 for indicator in professional_indicators if indicator in document)
        professionalism_score = min(indicator_count * 8, 80)
        
        # 深度分析的体现
        depth_indicators = ['深入', '系统', '全面', '综合', '详细', '具体', '实际', '案例']
        depth_count = sum(1 for indicator in depth_indicators if indicator in document)
        depth_score = min(depth_count * 5, 20)
        
        return professionalism_score + depth_score
    
    def _calculate_meaningful_content_ratio(self, document: str) -> float:
        """计算有意义内容的比例"""
        total_lines = len(document.split('\n'))
        if total_lines == 0:
            return 0.0
        
        meaningful_lines = 0
        for line in document.split('\n'):
            line = line.strip()
            if (line and 
                not line.startswith('#') and 
                not line.startswith('*暂无') and 
                not line.startswith('---') and
                len(line) > 10):
                meaningful_lines += 1
        
        return meaningful_lines / total_lines
    
    def _generate_comprehensive_improvement_suggestions(self, knowledge_counts: Dict[str, int], 
                                                      content_quality_score: float,
                                                      adjusted_standards: Dict[str, Any],
                                                      llm_result: Optional[LLMAssessmentResult]) -> List[str]:
        """生成综合改进建议"""
        suggestions = []
        
        # 检查知识点数量不足的部分
        if knowledge_counts['core_concepts'] < adjusted_standards['min_core_concepts']:
            suggestions.append(f"需要增加核心概念，当前{knowledge_counts['core_concepts']}个，建议至少{adjusted_standards['min_core_concepts']}个")
        
        if knowledge_counts['methodologies'] < adjusted_standards['min_methodologies']:
            suggestions.append(f"需要增加方法论内容，当前{knowledge_counts['methodologies']}个，建议至少{adjusted_standards['min_methodologies']}个")
        
        if knowledge_counts['practical_tips'] < adjusted_standards['min_practical_tips']:
            suggestions.append(f"需要增加实用技巧，当前{knowledge_counts['practical_tips']}个，建议至少{adjusted_standards['min_practical_tips']}个")
        
        if knowledge_counts['insights'] < adjusted_standards['min_insights']:
            suggestions.append(f"需要增加深度见解，当前{knowledge_counts['insights']}个，建议至少{adjusted_standards['min_insights']}个")
        
        # 检查内容质量问题
        if content_quality_score < 70:
            if knowledge_counts['actionable_advice'] < 2:
                suggestions.append("需要增加具体的实践指南和可执行建议")
            
            if knowledge_counts['case_studies'] < 2:
                suggestions.append("需要增加相关案例分析，提升内容说服力")
            
            if knowledge_counts['frameworks'] < 2:
                suggestions.append("需要增加分析工具和模型，提升内容的系统性")
        
        # 通用改进建议
        if len(suggestions) == 0 and sum(knowledge_counts.values()) < 15:
            suggestions.append("整体知识密度偏低，建议在各个部分都增加更多具体、深入的内容")
        
        # 基于LLM评估结果添加建议
        if llm_result:
            if llm_result.improvement_suggestions:
                suggestions.extend(llm_result.improvement_suggestions)
        
        return suggestions

class QualityController:
    """质量控制器 - 管理整个质量控制流程"""
    
    MAX_RETRIES = 3
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        self.assessment = QualityAssessment(llm_config)
        self.llm_config = llm_config or {}
    
    def validate_content_before_generation(self, content_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        在生成知识图谱之前验证内容质量
        这是第一道防线，防止生成无关内容
        
        参数:
            content_data: 内容提取数据
            
        返回:
            (是否通过验证, 问题列表)
        """
        issues = []
        
        # 检查基本数据结构
        if not isinstance(content_data, dict):
            issues.append("内容数据格式错误：不是有效的字典结构")
            return False, issues
        
        # 检查必要字段
        required_fields = ['platform', 'metadata', 'content']
        for field in required_fields:
            if field not in content_data:
                issues.append(f"内容数据缺少必要字段：{field}")
        
        if issues:
            return False, issues
        
        # 提取关键信息
        platform = content_data.get('platform', '')
        metadata = content_data.get('metadata', {})
        content = content_data.get('content', '')
        
        title = metadata.get('title', '')
        author = metadata.get('author', '')
        description = metadata.get('description', '')
        
        # 检查平台信息
        if not platform or platform == '未知平台':
            issues.append("平台信息缺失或无效")
        
        # 检查标题质量
        title_issues = self._validate_title_quality(title, platform)
        issues.extend(title_issues)
        
        # 检查作者信息
        author_issues = self._validate_author_quality(author, platform)
        issues.extend(author_issues)
        
        # 检查描述质量
        description_issues = self._validate_description_quality(description, platform)
        issues.extend(description_issues)
        
        # 检查内容质量
        content_issues = self._validate_content_quality(content, platform)
        issues.extend(content_issues)
        
        # 检查内容相关性
        relevance_issues = self._validate_content_relevance(title, description, content, platform)
        issues.extend(relevance_issues)
        
        # 综合评估
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"内容验证失败 - 平台: {platform}, 问题数量: {len(issues)}")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info(f"内容验证通过 - 平台: {platform}, 标题: {title[:50]}")
        
        return is_valid, issues
    
    def _validate_title_quality(self, title: str, platform: str) -> List[str]:
        """验证标题质量"""
        issues = []
        
        if not title or not title.strip():
            issues.append("标题为空")
            return issues
        
        title_clean = title.strip()
        
        # 检查默认标题
        default_titles = {
            'douyin': ['抖音视频', '视频'],
            'xiaohongshu': ['小红书笔记', '小红书内容', '笔记'],
            'zhihu': ['知乎内容', '知乎视频'],
            'bilibili': ['bilibili视频', '哔哩哔哩视频', 'B站视频']
        }
        
        platform_defaults = default_titles.get(platform, [])
        platform_defaults.extend(['未知标题', '无标题', '默认标题'])
        
        if title_clean in platform_defaults:
            issues.append(f"标题为默认值：'{title_clean}'")
        
        # 检查标题长度
        if len(title_clean) < 3:
            issues.append(f"标题过短：'{title_clean}' (长度: {len(title_clean)})")
        
        # 检查是否为自动生成的标题
        if (title_clean.startswith('抖音视频_') or 
            title_clean.startswith('小红书笔记_') or
            title_clean.startswith('视频_')):
            issues.append(f"标题为自动生成的默认值：'{title_clean}'")
        
        # 检查标题是否包含有意义的内容
        meaningful_chars = re.sub(r'[0-9\s\-_\.@#]+', '', title_clean)
        if len(meaningful_chars) < 3:
            issues.append(f"标题缺少有意义的文字内容：'{title_clean}'")
        
        return issues
    
    def _validate_author_quality(self, author: str, platform: str) -> List[str]:
        """验证作者信息质量"""
        issues = []
        
        if not author or not author.strip():
            issues.append("作者信息为空")
            return issues
        
        author_clean = author.strip()
        
        # 检查默认作者
        default_authors = ['未知作者', '无作者', '默认作者', '匿名']
        if author_clean in default_authors:
            issues.append(f"作者为默认值：'{author_clean}'")
        
        return issues
    
    def _validate_description_quality(self, description: str, platform: str) -> List[str]:
        """验证描述质量"""
        issues = []
        
        if not description or not description.strip():
            issues.append("描述信息为空")
            return issues
        
        description_clean = description.strip()
        
        # 检查默认描述
        default_descriptions = [
            '无法获取视频描述', '无法获取内容描述', '无法获取笔记描述',
            '未知内容', '默认描述', '无描述', '暂无描述'
        ]
        
        if description_clean in default_descriptions:
            issues.append(f"描述为默认值：'{description_clean}'")
        
        # 检查描述长度
        if len(description_clean) < 10:
            issues.append(f"描述过短：长度仅{len(description_clean)}字符")
        
        return issues
    
    def _validate_content_quality(self, content: str, platform: str) -> List[str]:
        """验证内容质量"""
        issues = []
        
        if not content or not content.strip():
            issues.append("内容为空")
            return issues
        
        content_clean = content.strip()
        
        # 检查内容长度
        if len(content_clean) < 50:
            issues.append(f"内容过短：长度仅{len(content_clean)}字符，无法进行有效分析")
        
        # 检查内容是否主要由默认值组成
        default_indicators = [
            '标题: 抖音视频', '标题: 小红书', '标题: 视频',
            '作者: 未知作者', '描述:\n无法获取', '描述: 无法获取'
        ]
        
        default_count = sum(1 for indicator in default_indicators if indicator in content_clean)
        if default_count >= 2:
            issues.append(f"内容主要由默认值组成（发现{default_count}个默认值指标）")
        
        return issues
    
    def _validate_content_relevance(self, title: str, description: str, content: str, platform: str) -> List[str]:
        """验证内容相关性"""
        issues = []
        
        # 合并所有文本进行分析
        all_text = f"{title} {description} {content}".lower()
        
        # 检查是否包含有意义的关键词
        meaningful_keywords = [
            # 商业/管理
            '管理', '团队', '领导', '策略', '营销', '销售', '客户', '市场', '品牌', '运营',
            # 技术
            '技术', '开发', '编程', '代码', '算法', '软件', '系统', '工具', 'ai', 'python',
            # 金融
            '投资', '理财', '股票', '基金', '金融', '财务', '资本', '收益', '风险',
            # 教育
            '学习', '教育', '知识', '技能', '培训', '课程', '方法', '经验', '思维',
            # 生活
            '健康', '美食', '旅行', '时尚', '生活', '家居', '购物', '娱乐',
            # 个人发展
            '成长', '职业', '规划', '目标', '习惯', '能力', '心理', '情商'
        ]
        
        keyword_found = any(keyword in all_text for keyword in meaningful_keywords)
        
        # 如果内容较短且没有找到有意义的关键词
        if len(content) < 200 and not keyword_found:
            issues.append("内容缺乏有意义的主题关键词，可能为无关或通用内容")
        
        # 检查内容信息密度
        info_content = re.sub(r'(标题:|作者:|描述:|平台:)', '', content)
        info_content = re.sub(r'\s+', ' ', info_content).strip()
        
        if len(info_content) < 30:
            issues.append(f"内容信息密度过低：去除格式后仅有{len(info_content)}字符的有效信息")
        
        return issues
    
    def ensure_quality_document(self, initial_document: str, content_data: Dict[str, Any],
                              content_type: str = "general") -> Tuple[str, QualityMetrics, int]:
        """
        确保文档质量达标，如有必要进行重试改进
        
        参数:
            initial_document: 初始生成的文档
            content_data: 原始内容数据
            content_type: 内容类型
            
        返回:
            Tuple[最终文档, 质量指标, 重试次数]
        """
        
        logger.info("开始质量控制流程")
        
        current_document = initial_document
        original_content_length = len(content_data.get('content', ''))
        
        for retry_count in range(self.MAX_RETRIES + 1):
            # 评估当前文档质量
            metrics = self.assessment.assess_document(
                current_document, content_type, original_content_length
            )
            
            # 获取调整后的通过标准
            adjusted_standards = self.standards.get_adjusted_standards(
                content_type, original_content_length
            )
            pass_threshold = adjusted_standards['pass_threshold']
            
            logger.info(f"第{retry_count + 1}次评估，得分: {metrics.overall_score:.1f}，通过标准: {pass_threshold:.1f}")
            
            # 记录详细评估信息
            if metrics.llm_result:
                logger.info(f"LLM评估详情 - 内容深度: {metrics.llm_result.content_depth:.1f}, "
                          f"实用性: {metrics.llm_result.practicality:.1f}, "
                          f"专业性: {metrics.llm_result.professionalism:.1f}")
            
            # 生成详细反馈报告
            feedback_report = self._create_detailed_feedback_report(metrics, content_type)
            
            # 记录反馈报告（用于调试和分析）
            logger.debug(f"详细反馈报告: {feedback_report}")
            
            # 如果质量达标或已达最大重试次数，返回结果
            if metrics.overall_score >= pass_threshold or retry_count >= self.MAX_RETRIES:
                if metrics.overall_score >= pass_threshold:
                    logger.info("文档质量达标，通过审核")
                    logger.info(f"最终质量等级: {feedback_report['overall_assessment']['level']}")
                else:
                    logger.warning(f"达到最大重试次数，使用当前最佳版本（得分: {metrics.overall_score:.1f}）")
                    logger.warning(f"未达标原因: {feedback_report['improvement_priorities']}")
                
                return current_document, metrics, retry_count
            
            # 需要重试改进
            logger.info(f"文档质量不达标，开始第{retry_count + 1}次重试改进")
            
            # 记录具体的改进优先级
            priorities = feedback_report['improvement_priorities']
            if priorities:
                logger.info(f"改进优先级: {[p['area'] for p in priorities[:3]]}")
            
            # 记录具体的行动建议
            actions = feedback_report['specific_actions']
            if actions:
                logger.info(f"具体行动: {[a['action'] for a in actions[:2]]}")
            
            # 生成改进提示并重新生成
            improvement_prompt = self._generate_improvement_prompt(metrics, content_type, retry_count)
            logger.info(f"改进提示: {improvement_prompt[:200]}...")  # 只记录前200字符
            
            current_document = self._regenerate_with_improvement(
                content_data, improvement_prompt, content_type, feedback_report
            )
        
        # 这里不应该到达，但为了安全起见
        return current_document, metrics, self.MAX_RETRIES
    
    def _regenerate_with_improvement(self, content_data: Dict[str, Any], 
                                   improvement_prompt: str, content_type: str,
                                   feedback_report: Dict[str, Any]) -> str:
        """基于改进提示和详细反馈重新生成文档"""
        
        try:
            from .knowledge_graph_processor import KnowledgeGraphProcessor
            
            generator = KnowledgeGraphProcessor()
            
            # 在content_data中添加详细的改进信息
            enhanced_content_data = content_data.copy()
            enhanced_content_data['improvement_prompt'] = improvement_prompt
            enhanced_content_data['retry_mode'] = True
            
            # 添加详细的反馈信息
            enhanced_content_data['quality_feedback'] = {
                'current_score': feedback_report['overall_assessment']['score'],
                'improvement_priorities': feedback_report['improvement_priorities'],
                'specific_actions': feedback_report['specific_actions'],
                'knowledge_gaps': {
                    'core_concepts_needed': max(0, 5 - feedback_report['knowledge_metrics']['core_concepts']),
                    'practical_tips_needed': max(0, 7 - feedback_report['knowledge_metrics']['practical_tips']),
                    'insights_needed': max(0, 5 - feedback_report['knowledge_metrics']['insights']),
                    'methodologies_needed': max(0, 4 - feedback_report['knowledge_metrics']['methodologies'])
                }
            }
            
            # 如果有LLM反馈，也添加进去
            if feedback_report['llm_feedback']:
                enhanced_content_data['llm_feedback'] = feedback_report['llm_feedback']
            
            logger.info("开始基于详细反馈重新生成文档")
            
            # 重新生成
            improved_document = generator.generate_knowledge_graph(enhanced_content_data)
            
            logger.info(f"重新生成完成，新文档长度: {len(improved_document)} 字符")
            
            return improved_document
            
        except Exception as e:
            logger.error(f"重新生成文档时出错: {str(e)}")
            # 如果重新生成失败，返回原文档
            return content_data.get('original_document', "重新生成失败")
    
    def _generate_improvement_prompt(self, metrics: QualityMetrics, content_type: str, 
                                   retry_count: int) -> str:
        """生成改进提示（结合LLM建议和具体修改意见）"""
        
        prompts = []
        
        # 基于重试次数调整策略
        if retry_count == 0:
            prompts.append("请深化分析，增加知识密度和实用性")
        elif retry_count == 1:
            prompts.append("请尝试不同的分析角度，扩大分析范围，增加专业深度")
        else:
            prompts.append("请使用最丰富的分析框架，确保内容全面而深入")
        
        # 基于量化评估的具体不足添加精确的修改建议
        specific_improvements = self._generate_specific_improvements(metrics, content_type)
        prompts.extend(specific_improvements)
        
        # 基于LLM评估结果添加针对性建议
        if metrics.llm_result:
            llm_improvements = self._generate_llm_based_improvements(metrics.llm_result, content_type)
            prompts.extend(llm_improvements)
        
        # 基于内容类型添加特定建议
        type_specific_prompts = self._get_content_type_improvements(content_type, metrics)
        prompts.extend(type_specific_prompts)
        
        return "; ".join(prompts)
    
    def _generate_specific_improvements(self, metrics: QualityMetrics, content_type: str) -> List[str]:
        """生成具体的修改建议"""
        improvements = []
        
        # 核心概念不足
        if metrics.core_concepts_count < 3:
            improvements.append(
                f"核心概念部分需要扩充：当前只有{metrics.core_concepts_count}个，"
                f"请增加到至少5个深度概念，每个概念都要包含定义、重要性和应用场景"
            )
        
        # 方法论不足
        if metrics.methodologies_count < 2:
            improvements.append(
                f"方法论部分严重不足：当前只有{metrics.methodologies_count}个，"
                f"请增加至少4个系统性方法，包含具体步骤、适用条件和预期效果"
            )
        
        # 实用技巧不足
        if metrics.practical_tips_count < 3:
            improvements.append(
                f"实用技巧部分需要大幅增强：当前只有{metrics.practical_tips_count}个，"
                f"请增加至少7个可立即执行的具体技巧，每个技巧都要有明确的操作步骤"
            )
        
        # 深度见解不足
        if metrics.insights_count < 2:
            improvements.append(
                f"深度见解部分缺乏：当前只有{metrics.insights_count}个，"
                f"请增加至少5个有价值的深度思考，包含趋势分析、本质认知和创新观点"
            )
        
        # 分析框架不足
        if metrics.frameworks_count < 2:
            improvements.append(
                f"分析工具部分不完整：当前只有{metrics.frameworks_count}个，"
                f"请增加至少5个专业分析框架，如SWOT、PEST、波特五力等，并说明使用方法"
            )
        
        # 实践指南不足
        if metrics.actionable_advice_count < 3:
            improvements.append(
                f"实践指南部分需要强化：当前只有{metrics.actionable_advice_count}个，"
                f"请增加至少6个可执行的行动建议，包含具体步骤、时间安排和成功指标"
            )
        
        # 案例分析不足
        if metrics.case_studies_count < 2:
            improvements.append(
                f"案例分析部分缺失：当前只有{metrics.case_studies_count}个，"
                f"请增加至少5个真实案例，包含成功案例、失败教训和对比分析"
            )
        
        # 内容长度不足
        if metrics.total_content_length < 2000:
            improvements.append(
                f"整体内容长度不足：当前{metrics.total_content_length}字符，"
                f"请扩充到至少3000字符，确保每个部分都有充分的详细说明"
            )
        
        # 结构完整性不足
        if metrics.structure_completeness < 0.8:
            improvements.append(
                "文档结构不完整：请确保包含所有必要部分（核心概念、方法论、实用技巧、"
                "深度见解、分析工具、实践指南、案例分析），每个部分都要有实质性内容"
            )
        
        return improvements
    
    def _generate_llm_based_improvements(self, llm_result: LLMAssessmentResult, content_type: str) -> List[str]:
        """基于LLM评估结果生成改进建议"""
        improvements = []
        
        if llm_result.content_depth < 75:
            improvements.append(
                f"内容深度不足（{llm_result.content_depth:.1f}/100）：请增加更深入的分析，"
                f"包含原理解释、机制分析、影响因素等深层次内容"
            )
        
        if llm_result.practicality < 75:
            improvements.append(
                f"实用性不够（{llm_result.practicality:.1f}/100）：请增加更多可操作的具体建议，"
                f"包含详细步骤、工具推荐、注意事项等实践指导"
            )
        
        if llm_result.professionalism < 75:
            improvements.append(
                f"专业性有待提升（{llm_result.professionalism:.1f}/100）：请使用更准确的专业术语，"
                f"增加行业标准、最佳实践、专业框架等专业内容"
            )
        
        if llm_result.logical_coherence < 75:
            improvements.append(
                f"逻辑连贯性需要改善（{llm_result.logical_coherence:.1f}/100）：请优化内容结构，"
                f"确保各部分之间逻辑清晰，前后呼应，层次分明"
            )
        
        if llm_result.completeness < 75:
            improvements.append(
                f"完整性不足（{llm_result.completeness:.1f}/100）：请补充遗漏的重要方面，"
                f"确保全面覆盖主题的各个关键维度"
            )
        
        if llm_result.innovation < 60:
            improvements.append(
                f"创新性较低（{llm_result.innovation:.1f}/100）：请增加独特观点、新颖角度、"
                f"创新思路等具有启发性的内容"
            )
        
        # 整合LLM的具体建议
        if llm_result.improvement_suggestions:
            for suggestion in llm_result.improvement_suggestions:
                if suggestion and len(suggestion.strip()) > 5:
                    improvements.append(f"LLM建议：{suggestion}")
        
        return improvements
    
    def _get_content_type_improvements(self, content_type: str, metrics: QualityMetrics) -> List[str]:
        """根据内容类型生成特定的改进建议"""
        improvements = []
        
        type_specific_requirements = {
            'finance': [
                "增加具体的财务分析方法和投资策略",
                "补充风险评估工具和资产配置建议",
                "添加市场分析框架和经济指标解读",
                "包含实际的投资案例和收益分析"
            ],
            'business': [
                "增加商业模式分析和竞争策略",
                "补充市场营销方法和客户分析",
                "添加运营管理工具和效率提升方法",
                "包含真实的商业案例和成功经验"
            ],
            'technology': [
                "增加技术实现细节和架构设计",
                "补充开发工具和最佳实践",
                "添加性能优化方法和故障排除",
                "包含代码示例和项目案例"
            ],
            'management': [
                "增加管理理论和领导力方法",
                "补充团队建设和沟通技巧",
                "添加绩效管理和决策框架",
                "包含管理案例和实践经验"
            ],
            'education': [
                "增加学习理论和教学方法",
                "补充认知科学和记忆技巧",
                "添加评估工具和进度跟踪",
                "包含教育案例和学习经验"
            ],
            'lifestyle': [
                "增加生活技巧和习惯养成方法",
                "补充健康管理和时间规划",
                "添加人际关系和情绪管理",
                "包含生活案例和实践心得"
            ]
        }
        
        if content_type in type_specific_requirements:
            # 根据当前质量水平选择合适的建议
            suggestions = type_specific_requirements[content_type]
            if metrics.overall_score < 60:
                # 低质量时，添加所有建议
                improvements.extend(suggestions)
            elif metrics.overall_score < 80:
                # 中等质量时，添加前两个建议
                improvements.extend(suggestions[:2])
            else:
                # 高质量时，添加一个精细化建议
                improvements.append(suggestions[0])
        
        return improvements
    
    def _create_detailed_feedback_report(self, metrics: QualityMetrics, content_type: str) -> Dict[str, Any]:
        """创建详细的反馈报告"""
        
        report = {
            'overall_assessment': {
                'score': metrics.overall_score,
                'level': self._get_quality_level(metrics.overall_score),
                'pass_status': metrics.overall_score >= 70
            },
            'dimension_scores': {
                'knowledge_density': metrics.knowledge_density_score,
                'content_quality': metrics.content_quality_score,
                'llm_assessment': metrics.llm_assessment_score
            },
            'knowledge_metrics': {
                'core_concepts': metrics.core_concepts_count,
                'methodologies': metrics.methodologies_count,
                'practical_tips': metrics.practical_tips_count,
                'insights': metrics.insights_count,
                'frameworks': metrics.frameworks_count,
                'actionable_advice': metrics.actionable_advice_count,
                'case_studies': metrics.case_studies_count
            },
            'content_metrics': {
                'total_length': metrics.total_content_length,
                'meaningful_ratio': metrics.meaningful_content_ratio,
                'structure_completeness': metrics.structure_completeness
            },
            'improvement_priorities': self._rank_improvement_priorities(metrics),
            'specific_actions': self._generate_specific_actions(metrics, content_type),
            'llm_feedback': None
        }
        
        # 添加LLM详细反馈
        if metrics.llm_result:
            report['llm_feedback'] = {
                'content_depth': metrics.llm_result.content_depth,
                'logical_coherence': metrics.llm_result.logical_coherence,
                'practicality': metrics.llm_result.practicality,
                'professionalism': metrics.llm_result.professionalism,
                'completeness': metrics.llm_result.completeness,
                'innovation': metrics.llm_result.innovation,
                'confidence': metrics.llm_result.assessment_confidence,
                'suggestions': metrics.llm_result.improvement_suggestions
            }
        
        return report
    
    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "合格"
        elif score >= 60:
            return "需要改进"
        else:
            return "不合格"
    
    def _rank_improvement_priorities(self, metrics: QualityMetrics) -> List[Dict[str, Any]]:
        """排序改进优先级"""
        priorities = []
        
        # 检查各个维度的不足
        if metrics.core_concepts_count < 3:
            priorities.append({
                'area': '核心概念',
                'urgency': 'high',
                'current': metrics.core_concepts_count,
                'target': 5,
                'impact': 'high'
            })
        
        if metrics.practical_tips_count < 3:
            priorities.append({
                'area': '实用技巧',
                'urgency': 'high',
                'current': metrics.practical_tips_count,
                'target': 7,
                'impact': 'high'
            })
        
        if metrics.insights_count < 2:
            priorities.append({
                'area': '深度见解',
                'urgency': 'medium',
                'current': metrics.insights_count,
                'target': 5,
                'impact': 'high'
            })
        
        if metrics.methodologies_count < 2:
            priorities.append({
                'area': '方法论',
                'urgency': 'medium',
                'current': metrics.methodologies_count,
                'target': 4,
                'impact': 'medium'
            })
        
        # 基于LLM评估添加优先级
        if metrics.llm_result:
            if metrics.llm_result.practicality < 75:
                priorities.append({
                    'area': '实用性',
                    'urgency': 'high',
                    'current': metrics.llm_result.practicality,
                    'target': 85,
                    'impact': 'high'
                })
            
            if metrics.llm_result.content_depth < 75:
                priorities.append({
                    'area': '内容深度',
                    'urgency': 'high',
                    'current': metrics.llm_result.content_depth,
                    'target': 85,
                    'impact': 'high'
                })
        
        # 按紧急程度和影响力排序
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        priorities.sort(key=lambda x: (priority_order[x['urgency']], priority_order[x['impact']]), reverse=True)
        
        return priorities[:5]  # 返回前5个优先级
    
    def _generate_specific_actions(self, metrics: QualityMetrics, content_type: str) -> List[Dict[str, str]]:
        """生成具体的行动建议"""
        actions = []
        
        # 基于知识点不足生成行动建议
        if metrics.core_concepts_count < 3:
            actions.append({
                'action': '扩充核心概念部分',
                'description': f'当前只有{metrics.core_concepts_count}个核心概念，需要增加到5个以上',
                'method': '为每个概念提供定义、重要性说明、应用场景和相关理论支撑',
                'example': '例如：将"投资风险"扩展为"投资风险管理：指通过多元化、对冲等方法控制投资损失的系统性方法，是现代投资理论的核心组成部分"'
            })
        
        if metrics.practical_tips_count < 5:
            actions.append({
                'action': '增加实用技巧',
                'description': f'当前只有{metrics.practical_tips_count}个实用技巧，需要增加到7个以上',
                'method': '每个技巧都要包含具体步骤、注意事项、预期效果和适用场景',
                'example': '例如：不要只说"要分散投资"，而要说"建议将资金按3-3-3-1比例分配到股票、债券、基金和现金，每季度重新平衡一次"'
            })
        
        if metrics.insights_count < 3:
            actions.append({
                'action': '深化见解分析',
                'description': f'当前只有{metrics.insights_count}个深度见解，需要增加到5个以上',
                'method': '提供趋势分析、本质认知、创新观点和前瞻性思考',
                'example': '例如：分析"为什么散户投资者往往表现不佳"的深层原因，包含心理学、信息不对称、市场结构等多维度分析'
            })
        
        # 基于LLM评估生成行动建议
        if metrics.llm_result:
            if metrics.llm_result.professionalism < 75:
                actions.append({
                    'action': '提升专业性',
                    'description': f'专业性评分{metrics.llm_result.professionalism:.1f}，需要提升到85以上',
                    'method': '使用准确的专业术语，引用权威理论，提供行业标准和最佳实践',
                    'example': f'在{content_type}领域中，应该使用该领域的标准术语和分析框架'
                })
        
        return actions[:4]  # 返回前4个最重要的行动建议

def load_llm_config() -> Dict[str, Any]:
    """加载LLM配置"""
    import os
    
    # 默认配置
    default_config = {
        'enabled': True,
        'provider': 'openai',
        'model': 'gpt-3.5-turbo',
        'api_key': '',
        'base_url': '',
        'timeout': 30,
        'max_retries': 2
    }
    
    # 从环境变量读取配置
    config = default_config.copy()
    
    # LLM开关
    if os.getenv('QUALITY_LLM_ENABLED'):
        config['enabled'] = os.getenv('QUALITY_LLM_ENABLED').lower() == 'true'
    
    # LLM提供商和模型
    if os.getenv('QUALITY_LLM_PROVIDER'):
        config['provider'] = os.getenv('QUALITY_LLM_PROVIDER')
    
    if os.getenv('QUALITY_LLM_MODEL'):
        config['model'] = os.getenv('QUALITY_LLM_MODEL')
    
    # API配置
    if os.getenv('QUALITY_LLM_API_KEY'):
        config['api_key'] = os.getenv('QUALITY_LLM_API_KEY')
    elif os.getenv('OPENAI_API_KEY'):
        config['api_key'] = os.getenv('OPENAI_API_KEY')
    
    if os.getenv('QUALITY_LLM_BASE_URL'):
        config['base_url'] = os.getenv('QUALITY_LLM_BASE_URL')
    elif os.getenv('OPENAI_BASE_URL'):
        config['base_url'] = os.getenv('OPENAI_BASE_URL')
    
    # 超时和重试配置
    if os.getenv('QUALITY_LLM_TIMEOUT'):
        try:
            config['timeout'] = int(os.getenv('QUALITY_LLM_TIMEOUT'))
        except ValueError:
            pass
    
    if os.getenv('QUALITY_LLM_MAX_RETRIES'):
        try:
            config['max_retries'] = int(os.getenv('QUALITY_LLM_MAX_RETRIES'))
        except ValueError:
            pass
    
    # 尝试从配置文件读取
    try:
        import json
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'quality_config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config.get('llm', {}))
    except Exception as e:
        logger.debug(f"读取配置文件失败: {str(e)}")
    
    logger.info(f"LLM配置加载完成: provider={config['provider']}, model={config['model']}, enabled={config['enabled']}")
    
    return config

def assess_document_quality(document: str, content_type: str = "general", 
                          original_content_length: int = 1000,
                          llm_config: Dict[str, Any] = None) -> QualityMetrics:
    """
    便捷函数：评估文档质量
    """
    if llm_config is None:
        llm_config = load_llm_config()
    
    assessor = QualityAssessment(llm_config)
    return assessor.assess_document(document, content_type, original_content_length)

def ensure_quality_document(document: str, content_data: Dict[str, Any], 
                          content_type: str = "general",
                          llm_config: Dict[str, Any] = None) -> Tuple[str, QualityMetrics, int]:
    """
    便捷函数：确保文档质量达标
    """
    if llm_config is None:
        llm_config = load_llm_config()
    
    controller = QualityController(llm_config)
    return controller.ensure_quality_document(document, content_data, content_type) 