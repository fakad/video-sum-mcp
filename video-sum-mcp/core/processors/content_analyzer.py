#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
内容分析器 - 生成统一格式的深度内容分析文档
支持视频、文字、图片等多种内容类型
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import re

logger = logging.getLogger("video-sum-mcp.content_analyzer")

class ContentAnalyzer:
    """内容分析器，生成统一格式的深度内容分析"""
    
    def __init__(self):
        pass
    
    def analyze_and_generate_document(self, video_data: Dict[str, Any]) -> str:
        """
        分析内容数据并生成统一格式的深度分析文档
        
        参数:
            video_data: 内容提取数据
            
        返回:
            Markdown格式的分析文档
        """
        platform = video_data.get('platform', '未知平台')
        metadata = video_data.get('metadata', {})
        content = video_data.get('content', '')
        
        # 统一生成标题格式
        platform_names = {
            'douyin': '抖音',
            'xiaohongshu': '小红书',
            'zhihu': '知乎',
            'bilibili': '哔哩哔哩'
        }
        platform_cn = platform_names.get(platform, platform)
        title = f"{platform_cn}内容深度分析"
        
        # 检测内容类型
        content_type = self._detect_content_type(video_data)
        
        # 生成统一标签
        tags = self._generate_unified_tags(platform, content_type)
        
        # 分析核心主题（统一方法）
        core_topic = self._extract_unified_core_topic(platform, content_type, content)
        
        # 生成统一格式文档
        doc = self._generate_unified_document(
            title=title,
            platform=platform,
            platform_cn=platform_cn,
            metadata=metadata,
            content=content,
            content_type=content_type,
            tags=tags,
            core_topic=core_topic,
            video_data=video_data
        )
        
        return doc
    
    def _detect_content_type(self, video_data: Dict[str, Any]) -> str:
        """检测内容类型"""
        platform = video_data.get('platform', '')
        
        # 根据平台和URL特征检测内容类型
        if platform == 'douyin':
            return 'short_video'  # 短视频
        elif platform == 'xiaohongshu':
            # 小红书可能是视频、图片或文字笔记
            return 'lifestyle_note'  # 生活笔记（可包含图片、文字、视频）
        elif platform == 'zhihu':
            url = video_data.get('url', '')
            if 'zvideo' in url:
                return 'knowledge_video'  # 知识视频
            elif 'zhuanlan' in url:
                return 'article'  # 专栏文章
            elif 'answer' in url:
                return 'qa_answer'  # 问答回答
            else:
                return 'knowledge_content'  # 知识内容
        elif platform == 'bilibili':
            return 'video_content'  # 视频内容
        else:
            return 'digital_content'  # 数字内容
    
    def _generate_unified_tags(self, platform: str, content_type: str) -> List[str]:
        """生成统一的标签体系"""
        # 基础标签（所有内容都有）
        base_tags = ["内容分析", "数字媒体"]
        
        # 平台标签
        platform_tags = {
            'douyin': ["抖音", "短视频平台"],
            'xiaohongshu': ["小红书", "生活社交"],
            'zhihu': ["知乎", "知识社区"],
            'bilibili': ["哔哩哔哩", "视频平台"]
        }
        
        # 内容类型标签
        content_type_tags = {
            'short_video': ["短视频", "移动视频"],
            'lifestyle_note': ["生活笔记", "社交内容"],
            'knowledge_video': ["知识视频", "教育内容"],
            'article': ["长文章", "深度阅读"],
            'qa_answer': ["问答内容", "知识分享"],
            'video_content': ["视频内容", "娱乐媒体"],
            'knowledge_content': ["知识内容", "专业分享"],
            'digital_content': ["数字内容", "网络媒体"]
        }
        
        # 主题标签
        theme_tags = ["内容创作", "平台分析", "用户研究"]
        
        # 合并所有标签
        all_tags = (base_tags + 
                   platform_tags.get(platform, []) + 
                   content_type_tags.get(content_type, []) + 
                   theme_tags)
        
        return all_tags[:8]  # 限制标签数量
    
    def _extract_unified_core_topic(self, platform: str, content_type: str, content: str) -> str:
        """统一的核心主题提取"""
        # 基于内容类型的主题映射
        topic_mapping = {
            'short_video': "短视频内容创作与传播",
            'lifestyle_note': "生活化内容分享与社交",
            'knowledge_video': "知识视频教育与传播",
            'article': "深度内容创作与阅读",
            'qa_answer': "知识问答与社区互动",
            'video_content': "视频娱乐与用户体验",
            'knowledge_content': "知识分享与专业交流",
            'digital_content': "数字内容分析与洞察"
        }
        
        return topic_mapping.get(content_type, "数字内容分析与洞察")
    
    def _generate_unified_document(self, title: str, platform: str, platform_cn: str,
                                 metadata: Dict[str, Any], content: str, content_type: str,
                                 tags: List[str], core_topic: str, video_data: Dict[str, Any]) -> str:
        """生成完全统一格式的分析文档，优化Obsidian显示"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        author = metadata.get('author', '未知作者')
        url = video_data.get('url', '')
        
        # 优化的Obsidian YAML前置内容
        doc = f"""---
title: "{title}"
author: "{author}"
platform: "{platform}"
content_type: "{content_type}"
created: "{current_time}"
tags: 
{self._format_tags_for_obsidian(tags)}
source_url: "{url}"
core_topic: "{core_topic}"
analysis_version: "2.0"
cssclass: "content-analysis"
---

# 📊 {title}

> [!info] 分析概览
> 本文档采用标准化分析框架，对来自**{platform_cn}**平台的{self._get_content_type_desc(content_type)}进行深度分析，提取关键信息和策略洞察。

## 📝 基础信息

| 🏷️ 项目 | 📋 详情 |
|---------|-------|
| **🌐 分析平台** | {platform_cn} |
| **👤 内容作者** | {author} |
| **📱 内容类型** | {self._get_content_type_desc(content_type)} |
| **📅 分析时间** | {current_time} |
| **🔗 源链接** | {url} |
| **🎯 核心主题** | {core_topic} |

---

## 🔍 内容结构分析

### 🎯 主题定位

> [!abstract] 核心主题
> **{core_topic}**

{self._generate_content_structure_analysis(content_type, platform)}

### 🧩 内容要素

{self._generate_content_elements(content_type)}

### 👥 受众特征

{self._generate_audience_analysis(platform, content_type)}

---

## 🌐 平台生态分析

### 🏛️ 平台特征

{self._generate_platform_characteristics(platform)}

### 📡 分发机制

{self._generate_distribution_mechanism(platform)}

### 👆 用户行为

{self._generate_user_behavior(platform)}

---

## 💎 内容价值评估

### 📊 信息维度

| 📈 评估项 | 🔍 分析要点 |
|----------|------------|
| **💡 信息密度** | 内容信息量与表达效率的平衡 |
| **🎯 实用价值** | 对目标受众的实际帮助程度 |
| **✨ 原创程度** | 内容的独特性和创新性 |
| **⏰ 时效性** | 内容的时间敏感性和持续价值 |

### 🚀 传播潜力

| 📈 评估项 | 🔍 分析要点 |
|----------|------------|
| **🔥 话题性** | 引发讨论和互动的能力 |
| **📤 分享动机** | 用户主动传播的驱动力 |
| **⚙️ 平台适配** | 与平台机制的匹配程度 |
| **🦠 病毒特质** | 快速传播的潜在因素 |

---

## 💡 策略洞察

### 🔑 关键发现

{self._generate_key_insights(platform, content_type)}

### ✅ 成功要素

{self._generate_success_factors(platform, content_type)}

### ⚠️ 风险评估

{self._generate_risk_assessment(platform, content_type)}

---

## 🎯 实施建议

### 📈 内容优化

{self._generate_content_optimization(platform, content_type)}

### 📢 传播策略

{self._generate_distribution_strategy(platform, content_type)}

### 🔄 持续改进

{self._generate_improvement_suggestions(platform, content_type)}

---

## 📋 分析总结

{self._generate_analysis_summary(platform_cn, content_type, core_topic)}

---

> [!tip] 标签索引
> {' | '.join([f'#{tag}' for tag in tags])}

> [!warning] 免责声明
> 本分析基于公开内容，遵循网络爬虫伦理规范，分析结果仅供学习研究使用。

"""
        
        return doc
    
    def _format_tags_for_obsidian(self, tags: List[str]) -> str:
        """格式化标签为Obsidian YAML格式"""
        formatted_tags = []
        for tag in tags:
            formatted_tags.append(f"  - {tag}")
        return '\n'.join(formatted_tags)
    
    def _get_content_type_desc(self, content_type: str) -> str:
        """获取内容类型的中文描述"""
        descriptions = {
            'short_video': '短视频内容',
            'lifestyle_note': '生活笔记',
            'knowledge_video': '知识视频',
            'article': '文章内容',
            'qa_answer': '问答回复',
            'video_content': '视频内容',
            'knowledge_content': '知识内容',
            'digital_content': '数字内容'
        }
        return descriptions.get(content_type, '数字内容')
    
    def _generate_content_structure_analysis(self, content_type: str, platform: str) -> str:
        """生成内容结构分析"""
        analyses = {
            'short_video': """**内容特征**: 短视频以快节奏、强视觉冲击为核心，在有限时间内最大化信息传递效果。

**结构特点**:
- 开场吸引：前3秒的关键信息呈现
- 核心内容：中段的主要信息传递
- 结尾引导：促进互动和分享的设计""",
            
            'lifestyle_note': """**内容特征**: 生活笔记以真实体验分享为核心，注重实用性和可操作性。

**结构特点**:
- 场景设置：生活化的情境描述
- 经验分享：具体的操作方法和心得
- 效果展示：实际结果和使用感受""",
            
            'knowledge_video': """**内容特征**: 知识视频以教育价值为核心，强调逻辑性和专业性。

**结构特点**:
- 问题提出：明确的学习目标设定
- 知识讲解：系统的内容组织呈现
- 总结应用：实际应用和拓展思考""",
            
            'article': """**内容特征**: 长文章以深度分析为核心，提供全面的观点阐述。

**结构特点**:
- 主题引入：背景介绍和问题提出
- 深度分析：多角度的详细论述
- 观点总结：结论提炼和启发思考""",
            
            'qa_answer': """**内容特征**: 问答回复以解决具体问题为核心，强调针对性和准确性。

**结构特点**:
- 问题理解：对提问的准确把握
- 解答过程：逻辑清晰的回应展开
- 补充说明：相关的延伸信息提供"""
        }
        
        return analyses.get(content_type, """**内容特征**: 数字内容以信息传递为核心，适应网络传播特点。

**结构特点**:
- 信息组织：清晰的内容层次结构
- 表达方式：适合平台特征的呈现形式
- 互动设计：促进用户参与的元素安排""")
    
    def _generate_content_elements(self, content_type: str) -> str:
        """生成内容要素分析"""
        elements = {
            'short_video': """- **视觉设计**: 画面构图、色彩搭配、动态效果
- **声音元素**: 背景音乐、音效、解说词
- **剪辑技巧**: 节奏控制、转场效果、特效运用
- **互动机制**: 话题标签、挑战参与、评论引导""",
            
            'lifestyle_note': """- **图片质量**: 拍摄技巧、美化处理、排版设计
- **文字表达**: 语言风格、描述详细度、情感传递
- **实用信息**: 具体步骤、注意事项、效果展示
- **社交元素**: 话题关联、用户互动、分享价值""",
            
            'knowledge_video': """- **内容深度**: 专业程度、信息密度、逻辑严密性
- **表达清晰**: 语言准确、概念解释、案例运用
- **视觉辅助**: 图表设计、动画效果、重点标识
- **教学设计**: 知识架构、难度递进、实践指导""",
            
            'article': """- **论述逻辑**: 观点组织、论证过程、结构完整性
- **信息来源**: 数据支撑、案例引用、权威参考
- **表达技巧**: 文字功底、修辞运用、可读性
- **深度价值**: 独特见解、思考启发、实用指导""",
            
            'qa_answer': """- **回答质量**: 准确性、完整性、专业程度
- **表达清晰**: 逻辑顺序、重点突出、易于理解
- **实用价值**: 可操作性、针对性、解决效果
- **延伸价值**: 相关补充、经验分享、思维拓展"""
        }
        
        return elements.get(content_type, """- **信息架构**: 内容组织、层次结构、逻辑关系
- **表达形式**: 媒体类型、呈现方式、互动元素
- **价值主张**: 核心观点、独特价值、用户收益
- **技术实现**: 制作质量、平台适配、用户体验""")
    
    def _generate_audience_analysis(self, platform: str, content_type: str) -> str:
        """生成受众特征分析"""
        audience_maps = {
            ('douyin', 'short_video'): """**主要受众**: 移动端重度用户，偏好快速娱乐内容消费
**年龄分布**: 以18-35岁年轻群体为主
**使用场景**: 碎片化时间，休闲娱乐，社交分享
**参与方式**: 被动浏览为主，轻度互动参与""",
            
            ('xiaohongshu', 'lifestyle_note'): """**主要受众**: 注重生活品质的都市用户群体
**年龄分布**: 以20-40岁女性用户为核心
**使用场景**: 购物决策，生活灵感，经验查找
**参与方式**: 主动搜索，深度收藏，信任分享""",
            
            ('zhihu', 'knowledge_video'): """**主要受众**: 知识型用户，追求深度学习和专业提升
**年龄分布**: 以25-45岁高学历群体为主
**使用场景**: 专业学习，问题解决，观点交流
**参与方式**: 深度阅读，理性讨论，知识积累""",
            
            ('zhihu', 'article'): """**主要受众**: 深度阅读爱好者，专业人士和学习者
**年龄分布**: 以25-45岁知识工作者为主
**使用场景**: 专业提升，观点学习，思维拓展
**参与方式**: 长时间阅读，深度思考，专业讨论""",
            
            ('zhihu', 'qa_answer'): """**主要受众**: 有具体问题需求的学习者和专业人士
**年龄分布**: 跨年龄段，以实际需求为导向
**使用场景**: 问题解决，专业咨询，经验获取
**参与方式**: 目标明确，结果导向，感谢反馈"""
        }
        
        key = (platform, content_type)
        return audience_maps.get(key, """**主要受众**: 数字内容消费者，具有多样化的信息需求
**年龄分布**: 根据平台特征和内容类型而定
**使用场景**: 信息获取，娱乐消费，社交互动
**参与方式**: 基于平台机制的多样化互动形式""")
    
    def _generate_platform_characteristics(self, platform: str) -> str:
        """生成平台特征分析"""
        characteristics = {
            'douyin': """**算法导向**: 基于用户行为的智能推荐系统，强调完播率和互动率
**内容偏好**: 短时长、高娱乐性、视觉冲击力强的内容
**商业模式**: 信息流广告、电商带货、直播打赏为主要变现途径""",
            
            'xiaohongshu': """**社区氛围**: 真实分享导向的种草社区，注重用户体验和信任关系
**内容偏好**: 高质量图片、实用性强、生活化表达的内容
**商业模式**: 品牌合作、电商导流、广告投放为主要盈利方式""",
            
            'zhihu': """**知识定位**: 专业问答和深度内容为核心的知识社区平台
**内容偏好**: 逻辑清晰、有深度价值、专业性强的内容
**商业模式**: 知识付费、会员服务、品牌广告为主要收入来源""",
            
            'bilibili': """**社区文化**: 二次元起家的多元化视频社区，重视创作者生态
**内容偏好**: 高质量视频、有创意性、社区文化强的内容
**商业模式**: 游戏运营、直播打赏、会员增值服务为核心业务"""
        }
        
        return characteristics.get(platform, """**平台定位**: 综合性数字内容平台，适应多样化用户需求
**内容偏好**: 根据平台调性和用户群体特征优化内容策略
**商业模式**: 广告变现、用户付费、电商服务等多元化盈利模式""")
    
    def _generate_distribution_mechanism(self, platform: str) -> str:
        """生成分发机制分析"""
        mechanisms = {
            'douyin': """**推荐算法**: 基于用户兴趣标签、行为数据、内容质量的多维度推荐
**流量分配**: 公域流量为主，通过算法分发到精准用户群体
**影响因素**: 完播率、点赞率、评论率、分享率、关注转化率""",
            
            'xiaohongshu': """**发现机制**: 结合搜索算法和推荐算法的双重分发体系
**流量来源**: 搜索流量、推荐流量、关注流量的多渠道分布
**排序因素**: 内容质量、用户互动、账号权重、时效性""",
            
            'zhihu': """**内容分发**: 基于话题热度、内容质量、用户关注的综合推荐
**权重系统**: 答主权威性、内容专业度、用户反馈的多重考量
**流量入口**: 热榜推荐、话题关注、搜索发现、用户关注""",
            
            'bilibili': """**推荐体系**: 综合考虑播放数据、用户偏好、内容质量的推荐算法
**流量渠道**: 首页推荐、分区热门、搜索发现、订阅推送
**评价指标**: 播放量、弹幕数、收藏数、投币数、分享数"""
        }
        
        return mechanisms.get(platform, """**分发逻辑**: 基于平台算法和用户行为的智能分发机制
**流量获取**: 多元化流量入口和推荐渠道的有机结合
**优化要点**: 内容质量、用户体验、平台适配的综合提升""")
    
    def _generate_user_behavior(self, platform: str) -> str:
        """生成用户行为分析"""
        behaviors = {
            'douyin': """**浏览习惯**: 快速滑动浏览，平均停留时间短，注意力集中在前几秒
**互动偏好**: 轻量级互动为主，点赞门槛低，评论和分享相对较少
**决策模式**: 基于第一印象和情感反应的快速决策""",
            
            'xiaohongshu': """**使用模式**: 主动搜索与被动浏览并重，目的性较强
**互动行为**: 收藏率高，评论质量好，私信咨询频繁
**信任机制**: 基于真实体验的信任建立，口碑传播效应明显""",
            
            'zhihu': """**阅读行为**: 深度阅读为主，停留时间长，完读率相对较高
**参与方式**: 理性讨论，专业交流，知识分享和获取并重
**社交特征**: 基于专业认同的社交关系，权威性认知重要""",
            
            'bilibili': """**观看习惯**: 完整观看比例高，重复观看行为常见
**互动文化**: 弹幕文化浓厚，评论区讨论活跃，创作者粉丝关系紧密
**社区参与**: 高度的社区归属感，亚文化认同强烈"""
        }
        
        return behaviors.get(platform, """**使用特征**: 根据平台性质展现差异化的用户行为模式
**互动方式**: 平台机制决定的多样化用户参与形式
**价值获取**: 基于个人需求和平台特色的价值实现路径""")
    
    def _generate_key_insights(self, platform: str, content_type: str) -> str:
        """生成关键洞察"""
        insights = {
            ('douyin', 'short_video'): """- **3秒法则**: 视频开头3秒决定用户是否继续观看，需要强烈的视觉或情感冲击
- **情感共鸣**: 能够快速建立情感连接的内容更容易获得用户互动
- **趋势把握**: 紧跟平台热点和音乐趋势，提升内容曝光机会
- **完播优化**: 内容节奏紧凑，避免冗长铺垫，确保信息密度合理""",
            
            ('xiaohongshu', 'lifestyle_note'): """- **真实性价值**: 用户更信任真实的使用体验分享，过度包装会降低可信度
- **实用导向**: 提供具体可操作的建议和方法，满足用户实际需求
- **视觉品质**: 高质量的图片和排版设计显著影响内容表现
- **搜索优化**: 合理使用关键词和话题标签，提升被发现的概率""",
            
            ('zhihu', 'knowledge_video'): """- **专业权威**: 展现专业知识背景和逻辑思维能力，建立内容权威性
- **结构清晰**: 良好的内容组织和表达逻辑提升用户理解效果
- **价值密度**: 高信息密度的内容更容易获得用户认可和传播
- **持续价值**: 具有长期参考价值的内容获得更好的平台推荐""",
            
            ('zhihu', 'article'): """- **深度思考**: 独特的观点和深入的分析更容易获得用户关注
- **逻辑严密**: 清晰的论证过程和充分的论据支撑提升内容说服力
- **实用指导**: 结合理论和实践的内容更具有用户价值
- **持续讨论**: 能够引发长期讨论的话题具有更强的传播力""",
            
            ('zhihu', 'qa_answer'): """- **问题针对**: 准确理解问题核心，提供有针对性的解答
- **经验价值**: 结合个人经验的回答更具说服力和参考价值
- **完整全面**: 全面回答问题的各个方面，提供完整的解决方案
- **后续价值**: 具有长期参考价值的回答获得持续关注"""
        }
        
        key = (platform, content_type)
        return insights.get(key, """- **平台适配**: 内容形式和表达方式需要与平台特征高度匹配
- **用户需求**: 深入理解目标用户的核心需求和痛点
- **质量为王**: 高质量的内容是获得平台推荐和用户认可的基础
- **持续优化**: 基于数据反馈不断调整和优化内容策略""")
    
    def _generate_success_factors(self, platform: str, content_type: str) -> str:
        """生成成功要素"""
        factors = {
            ('douyin', 'short_video'): """- **创意表达**: 独特的创意角度和表现形式
- **技术制作**: 优秀的拍摄和剪辑技巧
- **时机把握**: 准确捕捉和利用平台热点
- **用户互动**: 积极的评论回复和粉丝维护""",
            
            ('xiaohongshu', 'lifestyle_note'): """- **内容真实**: 基于真实体验的分享
- **美学品质**: 高品质的视觉呈现
- **实用价值**: 切实解决用户需求的内容
- **社区参与**: 积极的用户互动和关系维护""",
            
            ('zhihu', 'knowledge_video'): """- **专业深度**: 扎实的专业知识基础
- **表达能力**: 清晰的逻辑表达和演示技巧
- **内容价值**: 高质量的知识传递
- **持续输出**: 稳定的内容更新和质量维持""",
            
            ('zhihu', 'article'): """- **思考深度**: 独特而深入的观点分析
- **写作技巧**: 优秀的文字表达和结构组织
- **专业背景**: 相关领域的知识积累
- **读者服务**: 对读者需求的深度理解""",
            
            ('zhihu', 'qa_answer'): """- **专业能力**: 相关领域的专业知识和经验
- **回答质量**: 准确、全面、有用的回答内容
- **表达清晰**: 易于理解的表达方式
- **持续贡献**: 长期稳定的高质量回答输出"""
        }
        
        key = (platform, content_type)
        return factors.get(key, """- **内容质量**: 高标准的内容制作和表达
- **用户导向**: 以用户需求为中心的内容策略
- **平台理解**: 深入理解平台机制和用户特征
- **持续改进**: 基于反馈的持续优化能力""")
    
    def _generate_risk_assessment(self, platform: str, content_type: str) -> str:
        """生成风险评估"""
        risks = {
            ('douyin', 'short_video'): """- **内容同质化**: 跟风内容可能导致缺乏差异化竞争力
- **算法依赖**: 过度依赖平台推荐可能影响账号稳定性
- **注意力竞争**: 激烈的用户注意力争夺战
- **趋势变化**: 快速变化的热点和用户偏好""",
            
            ('xiaohongshu', 'lifestyle_note'): """- **信任危机**: 过度商业化可能损害用户信任
- **内容审核**: 平台对商业内容的严格审核机制
- **竞争加剧**: 优质创作者数量快速增长
- **流量获取**: 自然流量获取难度逐渐增加""",
            
            ('zhihu', 'knowledge_video'): """- **专业要求**: 对内容专业性的高标准要求
- **时间投入**: 制作高质量内容需要大量时间成本
- **受众有限**: 专业内容的受众范围相对较小
- **竞争压力**: 专业领域的权威竞争""",
            
            ('zhihu', 'article'): """- **创作门槛**: 深度内容创作的高技能要求
- **读者期待**: 用户对内容质量的高期待值
- **时效性**: 部分内容可能面临时效性挑战
- **观点争议**: 深度观点可能引发争议性讨论""",
            
            ('zhihu', 'qa_answer'): """- **准确性压力**: 回答错误可能影响个人声誉
- **知识更新**: 需要持续更新专业知识
- **竞争激烈**: 优质答主的竞争压力
- **时间分配**: 高质量回答需要充足时间投入"""
        }
        
        key = (platform, content_type)
        return risks.get(key, """- **平台变化**: 平台政策和算法的不确定性变化
- **竞争加剧**: 内容创作者数量持续增长带来的竞争
- **用户变化**: 用户需求和偏好的动态变化
- **技术发展**: 新技术对现有内容形式的冲击""")
    
    def _generate_content_optimization(self, platform: str, content_type: str) -> str:
        """生成内容优化建议"""
        optimizations = {
            ('douyin', 'short_video'): """- **开头优化**: 前3秒必须包含核心信息或强烈视觉冲击
- **节奏控制**: 保持紧凑的内容节奏，避免拖沓
- **视觉提升**: 改善画面质量、色彩搭配和构图设计
- **音频优化**: 选择合适的背景音乐和音效搭配""",
            
            ('xiaohongshu', 'lifestyle_note'): """- **图片质量**: 提升拍摄技巧和后期处理水平
- **标题优化**: 创作吸引人且包含关键词的标题
- **内容结构**: 合理组织图文内容，提升可读性
- **话题运用**: 恰当使用热门话题和标签""",
            
            ('zhihu', 'knowledge_video'): """- **内容深度**: 增加专业知识的深度和广度
- **表达优化**: 提升口语表达和逻辑组织能力
- **视觉辅助**: 增加图表、动画等视觉辅助元素
- **结构完善**: 优化内容架构和知识传递逻辑""",
            
            ('zhihu', 'article'): """- **逻辑强化**: 加强论证逻辑和观点支撑
- **内容丰富**: 增加案例、数据和实用信息
- **可读性**: 优化文章结构和语言表达
- **价值提升**: 增强内容的实用性和启发性""",
            
            ('zhihu', 'qa_answer'): """- **回答完整**: 全面回答问题的各个方面
- **实用导向**: 提供更多可操作的具体建议
- **案例补充**: 增加实际案例和经验分享
- **持续更新**: 根据新情况及时更新回答内容"""
        }
        
        key = (platform, content_type)
        return optimizations.get(key, """- **质量提升**: 从制作技术到内容深度的全面提升
- **用户体验**: 优化内容的可读性和用户体验
- **差异化**: 打造独特的内容特色和个人风格
- **价值增强**: 提升内容的实用性和参考价值""")
    
    def _generate_distribution_strategy(self, platform: str, content_type: str) -> str:
        """生成传播策略建议"""
        strategies = {
            ('douyin', 'short_video'): """- **发布时机**: 选择用户活跃度高的时间段发布
- **话题运用**: 积极参与平台热点话题和挑战
- **互动策略**: 及时回复评论，鼓励用户互动
- **持续优化**: 基于数据反馈调整内容策略""",
            
            ('xiaohongshu', 'lifestyle_note'): """- **关键词布局**: 在标题和内容中合理布局搜索关键词
- **话题选择**: 选择与内容高度相关的话题标签
- **社群运营**: 积极参与相关兴趣社群讨论
- **合作推广**: 与其他博主进行内容合作""",
            
            ('zhihu', 'knowledge_video'): """- **话题选择**: 选择热度适中且专业对口的话题
- **时效发布**: 把握话题热度的最佳发布时机
- **专业展示**: 通过内容展示专业能力和知识深度
- **长期价值**: 关注内容的长期价值和持续传播""",
            
            ('zhihu', 'article'): """- **话题热度**: 关注相关话题的热度变化
- **观点独特**: 提供独特且有价值的观点角度
- **引发讨论**: 设计能够引发讨论的观点或问题
- **权威建立**: 通过持续输出建立专业权威性""",
            
            ('zhihu', 'qa_answer'): """- **问题选择**: 选择有回答价值且符合专长的问题
- **及时回应**: 在问题热度期内及时提供回答
- **质量保证**: 确保回答的准确性和完整性
- **后续维护**: 根据情况补充和更新回答内容"""
        }
        
        key = (platform, content_type)
        return strategies.get(key, """- **平台机制**: 深入了解并充分利用平台推荐机制
- **时机把握**: 选择最佳的发布时间和热点时机
- **多渠道**: 结合平台内外的多种传播渠道
- **数据驱动**: 基于数据分析持续优化传播策略""")
    
    def _generate_improvement_suggestions(self, platform: str, content_type: str) -> str:
        """生成持续改进建议"""
        suggestions = {
            ('douyin', 'short_video'): """- **数据监控**: 定期分析播放量、互动率等关键指标
- **用户反馈**: 关注评论区用户反馈，及时调整方向
- **趋势跟踪**: 持续关注平台新功能和热点趋势
- **技能提升**: 不断学习视频制作和剪辑技巧""",
            
            ('xiaohongshu', 'lifestyle_note'): """- **数据分析**: 关注笔记的浏览量、收藏量、评论质量
- **用户洞察**: 深入了解目标用户的需求变化
- **内容迭代**: 基于用户反馈持续优化内容质量
- **技能发展**: 提升摄影、写作和审美能力""",
            
            ('zhihu', 'knowledge_video'): """- **专业提升**: 持续学习和更新专业知识
- **制作技巧**: 改进视频制作和演讲技巧
- **用户需求**: 关注用户的知识需求和学习偏好
- **内容规划**: 制定长期的内容输出计划""",
            
            ('zhihu', 'article'): """- **写作技巧**: 持续提升写作能力和表达技巧
- **知识更新**: 保持对相关领域的知识更新
- **读者互动**: 加强与读者的互动和交流
- **内容深化**: 不断深化内容的专业度和价值""",
            
            ('zhihu', 'qa_answer'): """- **专业成长**: 持续提升专业能力和知识广度
- **回答质量**: 不断提高回答的质量和实用性
- **领域深耕**: 在特定领域建立专业影响力
- **社区贡献**: 积极为知识社区贡献价值"""
        }
        
        key = (platform, content_type)
        return suggestions.get(key, """- **持续学习**: 保持对行业发展和平台变化的敏感度
- **技能提升**: 不断提升内容创作和表达能力
- **用户研究**: 深入研究目标用户的需求和行为
- **策略调整**: 基于数据和反馈及时调整策略方向""")
    
    def _generate_analysis_summary(self, platform_cn: str, content_type: str, core_topic: str) -> str:
        """生成分析总结"""
        content_type_desc = self._get_content_type_desc(content_type)
        
        return f"""通过对{platform_cn}平台{content_type_desc}的深度分析，我们发现成功的内容创作需要在理解平台机制、把握用户需求、提升内容质量三个维度上形成合力。

**核心洞察**: {core_topic}的成功关键在于平台适配性与内容价值的有机结合。

**实施要点**: 
1. 深度理解平台算法和用户行为特征
2. 持续提升内容质量和表达能力  
3. 建立有效的用户互动和反馈机制
4. 基于数据分析进行策略持续优化

通过系统性的分析和持续的优化实践，能够在{platform_cn}平台上实现内容价值的最大化传播。"""

def generate_content_analysis_document(video_data: Dict[str, Any]) -> str:
    """
    生成统一格式的内容分析文档
    
    参数:
        video_data: 内容提取数据
        
    返回:
        Markdown格式的分析文档
    """
    analyzer = ContentAnalyzer()
    return analyzer.analyze_and_generate_document(video_data) 