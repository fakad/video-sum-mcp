"""
智能缓存机制实现

提供基于URL哈希的缓存系统，避免重复处理相同的视频链接，
支持缓存有效性验证、自动清理等功能。
"""

import os
import json
import hashlib
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DocumentCache:
    """文档缓存管理器"""
    
    def __init__(self, cache_dir: str = "temp/cache", cache_expiry_hours: int = 24, max_cache_size_mb: int = 500):
        """
        初始化文档缓存管理器
        
        参数:
            cache_dir: 缓存目录路径
            cache_expiry_hours: 缓存过期时间（小时）
            max_cache_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_expiry_hours = cache_expiry_hours
        self.max_cache_size_mb = max_cache_size_mb
        self.cache_expiry_seconds = cache_expiry_hours * 3600
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存索引文件
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()
        
        logger.info(f"初始化缓存管理器: {cache_dir}, 过期时间: {cache_expiry_hours}小时")
    
    def _load_index(self) -> Dict[str, Any]:
        """加载缓存索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存索引失败: {e}")
        
        return {
            "version": "1.0",
            "created_at": time.time(),
            "entries": {}
        }
    
    def _save_index(self) -> None:
        """保存缓存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存索引失败: {e}")
    
    def _get_url_hash(self, url: str) -> str:
        """获取URL的哈希值"""
        # 标准化URL（移除查询参数中的时间戳等）
        normalized_url = self._normalize_url(url)
        return hashlib.md5(normalized_url.encode('utf-8')).hexdigest()
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL，移除可能变化的参数"""
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(url)
        
        # 对于某些平台，移除时间戳等参数
        if "douyin.com" in parsed.netloc or "iesdouyin.com" in parsed.netloc:
            # 抖音链接通常包含时间戳参数，需要移除
            query_params = parse_qs(parsed.query)
            # 保留重要参数，移除时间戳类参数
            important_params = {}
            for key, values in query_params.items():
                if key not in ['timestamp', 'ts', '_t', 'time']:
                    important_params[key] = values
            
            new_query = urlencode(important_params, doseq=True)
            normalized = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, ''  # 移除fragment
            ))
        else:
            # 其他平台保持原样，只移除fragment
            normalized = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, parsed.query, ''
            ))
        
        return normalized
    
    def _get_cache_file_path(self, url_hash: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{url_hash}.json"
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        if not cache_entry:
            return False
        
        # 检查时间有效性
        cached_time = cache_entry.get("cached_at", 0)
        current_time = time.time()
        
        if current_time - cached_time > self.cache_expiry_seconds:
            return False
        
        # 检查文件是否存在
        cache_file = self._get_cache_file_path(cache_entry.get("url_hash", ""))
        if not cache_file.exists():
            return False
        
        return True
    
    def get_cached_result(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的处理结果
        
        参数:
            url: 视频URL
            
        返回:
            缓存的结果字典或None
        """
        url_hash = self._get_url_hash(url)
        cache_entry = self.index["entries"].get(url_hash)
        
        if not self._is_cache_valid(cache_entry):
            # 缓存无效，清理
            if cache_entry:
                self._remove_cache_entry(url_hash)
            return None
        
        try:
            cache_file = self._get_cache_file_path(url_hash)
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            logger.info(f"缓存命中: {url}")
            return cached_data
            
        except Exception as e:
            logger.error(f"读取缓存失败: {url} - {e}")
            self._remove_cache_entry(url_hash)
            return None
    
    def save_result(self, url: str, result: Dict[str, Any]) -> bool:
        """
        保存处理结果到缓存
        
        参数:
            url: 视频URL
            result: 处理结果
            
        返回:
            是否保存成功
        """
        try:
            url_hash = self._get_url_hash(url)
            cache_file = self._get_cache_file_path(url_hash)
            
            # 准备缓存数据
            cache_data = {
                "url": url,
                "url_hash": url_hash,
                "cached_at": time.time(),
                "result": result
            }
            
            # 保存到文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.index["entries"][url_hash] = {
                "url": url,
                "url_hash": url_hash,
                "cached_at": time.time(),
                "file_size": cache_file.stat().st_size
            }
            
            self._save_index()
            
            logger.info(f"缓存保存成功: {url}")
            
            # 检查缓存大小，必要时清理
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败: {url} - {e}")
            return False
    
    def _remove_cache_entry(self, url_hash: str) -> None:
        """移除缓存条目"""
        try:
            # 删除缓存文件
            cache_file = self._get_cache_file_path(url_hash)
            if cache_file.exists():
                cache_file.unlink()
            
            # 从索引中移除
            if url_hash in self.index["entries"]:
                del self.index["entries"][url_hash]
                self._save_index()
                
        except Exception as e:
            logger.error(f"移除缓存条目失败: {url_hash} - {e}")
    
    def _get_cache_size_mb(self) -> float:
        """获取当前缓存大小（MB）"""
        total_size = 0
        try:
            for file_path in self.cache_dir.glob("*.json"):
                if file_path.name != "cache_index.json":
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"计算缓存大小失败: {e}")
        
        return total_size / (1024 * 1024)  # 转换为MB
    
    def _cleanup_if_needed(self) -> None:
        """如果需要，清理缓存"""
        current_size = self._get_cache_size_mb()
        
        if current_size > self.max_cache_size_mb:
            logger.info(f"缓存大小超限 ({current_size:.2f}MB > {self.max_cache_size_mb}MB)，开始清理")
            self._cleanup_old_entries()
    
    def _cleanup_old_entries(self) -> None:
        """清理旧的缓存条目"""
        entries = list(self.index["entries"].items())
        
        # 按时间排序，最旧的在前
        entries.sort(key=lambda x: x[1].get("cached_at", 0))
        
        # 删除最旧的25%条目
        cleanup_count = max(1, len(entries) // 4)
        
        for i in range(cleanup_count):
            url_hash, entry = entries[i]
            self._remove_cache_entry(url_hash)
            logger.debug(f"清理旧缓存: {entry.get('url', url_hash)}")
        
        logger.info(f"清理完成，删除了 {cleanup_count} 个缓存条目")
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存条目
        
        返回:
            清理的条目数量
        """
        expired_hashes = []
        current_time = time.time()
        
        for url_hash, entry in self.index["entries"].items():
            cached_time = entry.get("cached_at", 0)
            if current_time - cached_time > self.cache_expiry_seconds:
                expired_hashes.append(url_hash)
        
        for url_hash in expired_hashes:
            self._remove_cache_entry(url_hash)
        
        if expired_hashes:
            logger.info(f"清理过期缓存: {len(expired_hashes)} 个条目")
        
        return len(expired_hashes)
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        try:
            # 删除所有缓存文件
            for file_path in self.cache_dir.glob("*.json"):
                file_path.unlink()
            
            # 重置索引
            self.index = {
                "version": "1.0",
                "created_at": time.time(),
                "entries": {}
            }
            self._save_index()
            
            logger.info("已清空所有缓存")
            
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        返回:
            缓存统计字典
        """
        total_entries = len(self.index["entries"])
        cache_size_mb = self._get_cache_size_mb()
        
        # 计算有效缓存数量
        valid_entries = 0
        for entry in self.index["entries"].values():
            if self._is_cache_valid(entry):
                valid_entries += 1
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "cache_size_mb": round(cache_size_mb, 2),
            "max_cache_size_mb": self.max_cache_size_mb,
            "cache_dir": str(self.cache_dir),
            "expiry_hours": self.cache_expiry_hours
        }
    
    def is_url_cached(self, url: str) -> bool:
        """
        检查URL是否已缓存且有效
        
        参数:
            url: 视频URL
            
        返回:
            是否已缓存
        """
        return self.get_cached_result(url) is not None


# 全局缓存管理器实例
_global_cache_manager = None

def get_cache_manager(
    cache_dir: str = "temp/cache", 
    cache_expiry_hours: int = 24, 
    max_cache_size_mb: int = 500
) -> DocumentCache:
    """
    获取全局缓存管理器实例
    
    参数:
        cache_dir: 缓存目录
        cache_expiry_hours: 缓存过期时间（小时）
        max_cache_size_mb: 最大缓存大小（MB）
        
    返回:
        DocumentCache实例
    """
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = DocumentCache(
            cache_dir=cache_dir,
            cache_expiry_hours=cache_expiry_hours,
            max_cache_size_mb=max_cache_size_mb
        )
        logger.info(f"创建缓存管理器: {cache_dir}")
    return _global_cache_manager

def reset_cache_manager():
    """重置全局缓存管理器实例"""
    global _global_cache_manager
    _global_cache_manager = None 