"""
统一配置管理系统

整合config.json、quality_config.json、环境变量等多个配置源，
提供统一的配置访问接口，支持分层配置和验证。
"""

import os
import json
import logging
import os
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from copy import deepcopy

from ..interfaces import IConfigManager

logger = logging.getLogger(__name__)


@dataclass
class ConfigSource:
    """配置源描述"""
    name: str
    path: Optional[str] = None
    env_prefix: Optional[str] = None
    required: bool = False
    priority: int = 100  # 数字越小优先级越高


@dataclass 
class ConfigValidationRule:
    """配置验证规则"""
    path: str
    required: bool = False
    data_type: type = str
    default_value: Any = None
    validator: Optional[callable] = None


class ConfigManager(IConfigManager):
    """
    统一配置管理器
    
    功能特性：
    - 多配置源整合（文件、环境变量）
    - 分层配置合并
    - 配置验证和默认值
    - 类型安全的配置访问
    - 热重载支持
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self._config_cache: Dict[str, Any] = {}
        self._last_modified: Dict[str, float] = {}
        self._config_sources: List[ConfigSource] = []
        self._validation_rules: List[ConfigValidationRule] = []
        
        # 设置默认配置源
        self._setup_default_sources()
        self._setup_validation_rules()
        
        # 初始加载配置
        self._load_all_configs()
    
    def _setup_default_sources(self):
        """设置默认配置源"""
        self._config_sources = [
            # 主配置文件（最高优先级）
            ConfigSource(
                name="main_config",
                path="config.json",
                required=True,
                priority=10
            ),
            # 质量配置文件
            ConfigSource(
                name="quality_config", 
                path="config/quality_config.json",
                required=False,
                priority=20
            ),
            # 环境变量（最高优先级）
            ConfigSource(
                name="env_vars",
                env_prefix="VIDEO_SUM_",
                required=False,
                priority=5
            )
        ]
    
    def _setup_validation_rules(self):
        """设置配置验证规则"""
        self._validation_rules = [
            # 基础配置
            ConfigValidationRule("api_key", data_type=str),
            ConfigValidationRule("proxy", data_type=str),
            ConfigValidationRule("temp_dir", required=True, data_type=str, default_value="temp_contents"),
            
            # 支持的平台和格式
            ConfigValidationRule("supported_platforms", required=True, data_type=list, 
                               default_value=["bilibili", "douyin", "xiaohongshu", "zhihu"]),
            ConfigValidationRule("supported_formats", required=True, data_type=list,
                               default_value=["markdown", "xmind"]),
            
            # 日志配置
            ConfigValidationRule("logging.level", required=True, data_type=str, default_value="INFO"),
            ConfigValidationRule("logging.file", data_type=str, default_value="video-sum-mcp.log"),
            
            # LLM配置
            ConfigValidationRule("llm_settings.provider", required=True, data_type=str, default_value="openai"),
            ConfigValidationRule("llm_settings.model", required=True, data_type=str, default_value="gpt-3.5-turbo"),
            ConfigValidationRule("llm_settings.temperature", data_type=float, default_value=0.3),
            ConfigValidationRule("llm_settings.max_tokens", data_type=int, default_value=4000),
            
            # 批处理配置  
            ConfigValidationRule("batch_processing.max_concurrent_requests", data_type=int, default_value=3),
            ConfigValidationRule("batch_processing.default_cache_dir", data_type=str, default_value="temp/cache"),
            
            # 缓存配置
            ConfigValidationRule("cache_settings.enabled", data_type=bool, default_value=True),
            ConfigValidationRule("cache_settings.cache_dir", data_type=str, default_value="temp/cache"),
            ConfigValidationRule("cache_settings.cache_expiry_hours", data_type=int, default_value=24),
            ConfigValidationRule("cache_settings.max_cache_size_mb", data_type=int, default_value=500),
            
            # 质量评估配置
            ConfigValidationRule("quality_standards.pass_threshold", data_type=float, default_value=70.0),
            ConfigValidationRule("quality_standards.excellent_threshold", data_type=float, default_value=85.0),
        ]
    
    def _load_all_configs(self):
        """加载所有配置源"""
        merged_config = {}
        
        # 按优先级排序配置源（优先级高的最后加载，以便覆盖低优先级的配置）
        sorted_sources = sorted(self._config_sources, key=lambda x: x.priority, reverse=True)
        
        for source in sorted_sources:
            try:
                config_data = self._load_config_source(source)
                if config_data:
                    merged_config = self._merge_configs(merged_config, config_data)
                    logger.debug(f"加载配置源: {source.name}")
            except Exception as e:
                if source.required:
                    logger.error(f"必需的配置源 {source.name} 加载失败: {e}")
                    raise
                else:
                    logger.warning(f"可选配置源 {source.name} 加载失败: {e}")
        
        # 应用验证规则和默认值
        self._config_cache = self._validate_and_apply_defaults(merged_config)
    
    def _load_config_source(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """加载单个配置源"""
        if source.path:
            return self._load_file_config(source)
        elif source.env_prefix:
            return self._load_env_config(source)
        return None
    
    def _load_file_config(self, source: ConfigSource) -> Optional[Dict[str, Any]]:
        """加载文件配置"""
        config_path = self.base_dir / source.path
        
        if not config_path.exists():
            if source.required:
                raise FileNotFoundError(f"必需的配置文件不存在: {config_path}")
            return None
        
        # 检查文件修改时间
        mtime = config_path.stat().st_mtime
        if source.name in self._last_modified and self._last_modified[source.name] >= mtime:
            return None  # 文件未修改，跳过重新加载
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._last_modified[source.name] = mtime
            return config_data
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 {config_path} JSON格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"读取配置文件 {config_path} 失败: {e}")
            raise
    
    def _load_env_config(self, source: ConfigSource) -> Dict[str, Any]:
        """加载环境变量配置"""
        env_config = {}
        prefix = source.env_prefix
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 转换环境变量名为配置路径
                config_key = key[len(prefix):].lower()
                
                # 特殊处理：只有特定的多层级配置才转换下划线为点
                # 例如：LOGGING_LEVEL -> logging.level, CACHE_SETTINGS_ENABLED -> cache_settings.enabled
                nested_patterns = [
                    ('logging_', 'logging.'),
                    ('cache_settings_', 'cache_settings.'),
                    ('llm_settings_', 'llm_settings.'),
                    ('batch_processing_', 'batch_processing.'),
                    ('quality_standards_', 'quality_standards.'),
                    ('assessment_dimensions_', 'assessment_dimensions.')
                ]
                
                for pattern, replacement in nested_patterns:
                    if config_key.startswith(pattern):
                        config_key = config_key.replace(pattern, replacement, 1)
                        break
                
                # 尝试类型转换
                converted_value = self._convert_env_value(value)
                self._set_nested_value(env_config, config_key, converted_value)
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值类型"""
        # 布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON数组或对象
        if value.startswith(('[', '{')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 字符串
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """设置嵌套配置值"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并配置"""
        result = deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    def _validate_and_apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置并应用默认值"""
        validated_config = deepcopy(config)
        
        for rule in self._validation_rules:
            try:
                value = self._get_nested_value(validated_config, rule.path)
                
                # 应用默认值
                if value is None and rule.default_value is not None:
                    self._set_nested_value(validated_config, rule.path, rule.default_value)
                    value = rule.default_value
                
                # 检查必需项
                if rule.required and value is None:
                    raise ValueError(f"必需的配置项缺失: {rule.path}")
                
                # 类型验证
                if value is not None and not isinstance(value, rule.data_type):
                    try:
                        # 尝试类型转换
                        converted_value = rule.data_type(value)
                        self._set_nested_value(validated_config, rule.path, converted_value)
                        value = converted_value
                    except (ValueError, TypeError):
                        logger.warning(f"配置项 {rule.path} 类型错误，期望 {rule.data_type.__name__}，实际 {type(value).__name__}")
                
                # 自定义验证器
                if rule.validator and value is not None:
                    if not rule.validator(value):
                        raise ValueError(f"配置项 {rule.path} 验证失败")
                        
            except Exception as e:
                logger.error(f"验证配置项 {rule.path} 时出错: {e}")
                if rule.required:
                    raise
        
        return validated_config
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """获取嵌套配置值"""
        keys = path.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return None
    
    def get(self, path: str, default: Any = None) -> Any:
        """获取配置值"""
        value = self._get_nested_value(self._config_cache, path)
        return value if value is not None else default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        return self.get(section, {})
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """获取平台特定配置"""
        # 从extractor_settings获取平台配置
        extractor_config = self.get_section("extractor_settings").get(platform, {})
        
        # 从batch_processing.platform_strategies获取批处理配置
        batch_config = self.get_section("batch_processing.platform_strategies").get(platform, {})
        
        # 合并配置
        platform_config = {**extractor_config}
        if batch_config:
            platform_config["batch_processing"] = batch_config
        
        return platform_config
    
    def set(self, path: str, value: Any) -> None:
        """设置配置值（运行时修改，不持久化）"""
        self._set_nested_value(self._config_cache, path, value)
        logger.debug(f"运行时配置更新: {path} = {value}")
    
    def update_section(self, section: str, updates: Dict[str, Any]) -> None:
        """更新配置节"""
        current_section = self.get_section(section)
        updated_section = self._merge_configs(current_section, updates)
        self.set(section, updated_section)
    
    def reload(self) -> None:
        """重新加载所有配置"""
        logger.info("重新加载配置...")
        self._config_cache.clear()
        self._last_modified.clear()
        self._load_all_configs()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return deepcopy(self._config_cache)
    
    def validate(self) -> bool:
        """验证当前配置是否有效"""
        try:
            self._validate_and_apply_defaults(self._config_cache)
            return True
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def add_validation_rule(self, rule: ConfigValidationRule) -> None:
        """添加验证规则"""
        self._validation_rules.append(rule)
    
    def add_config_source(self, source: ConfigSource) -> None:
        """添加配置源"""
        self._config_sources.append(source)
        self.reload()  # 重新加载配置


# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_global_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def set_global_config_manager(manager: ConfigManager) -> None:
    """设置全局配置管理器"""
    global _global_config_manager
    _global_config_manager = manager 