"""
Weaver 配置中心

集中管理所有可配置参数，避免硬编码散落在各模块中。
支持从环境变量读取配置。

用法:
    from app.config import scanner_config, matcher_config, filler_config
    
    # 访问配置
    timeout = scanner_config.max_wait
    threshold = matcher_config.min_score_threshold
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScannerConfig:
    """
    扫描器配置
    
    控制页面扫描的行为参数。
    """
    max_wait: float = 15.0          # 最大等待时间(秒)
    poll_interval: float = 0.8      # 轮询间隔(秒)
    loading_timeout: float = 5.0    # 加载等待超时(秒)
    stable_count_threshold: int = 3 # 稳定性检测阈值（连续N次一致）
    iframe_scan_depth: int = 2      # Iframe 扫描深度
    shadow_dom_depth: int = 2       # Shadow DOM 扫描深度


@dataclass
class MatcherConfig:
    """
    匹配器配置
    
    控制字段智能匹配的评分阈值。
    """
    min_score_threshold: int = 60   # 最低匹配分数
    exact_match_score: int = 100    # 精确匹配分数
    partial_match_score: int = 80   # 部分匹配分数
    high_quality_threshold: int = 90 # 高质量匹配阈值
    fuzzy_match_ratio: float = 0.7  # 模糊匹配相似度阈值


@dataclass
class FillerConfig:
    """
    填充器配置
    
    控制表单填充的行为参数。
    """
    element_timeout: float = 0.3    # 元素查找超时(秒)
    fill_delay: float = 0.1         # 填充操作间隔(秒)
    retry_count: int = 3            # 失败重试次数
    healing_max_attempts: int = 5   # 自愈最大尝试次数
    wait_after_fill: float = 0.05   # 填充后等待时间(秒)


@dataclass
class PaginationConfig:
    """
    翻页配置
    
    控制分页操作的行为参数。
    """
    click_wait_after: float = 1.5   # 点击后等待时间(秒)
    page_ready_timeout: float = 5.0 # 页面就绪超时(秒)
    auto_next_delay: float = 0.5    # 自动翻页间隔(秒)


@dataclass
class UIConfig:
    """
    UI 配置
    
    控制界面相关参数。
    """
    log_max_lines: int = 1000       # 日志最大行数
    animation_duration: int = 200   # 动画时长(毫秒)
    highlight_duration: float = 1.5 # 元素高亮时长(秒)
    tooltip_delay: int = 500        # 提示延迟(毫秒)


def _get_env_float(key: str, default: float) -> float:
    """从环境变量获取浮点数配置"""
    value = os.environ.get(key)
    if value:
        try:
            return float(value)
        except ValueError:
            pass
    return default


def _get_env_int(key: str, default: int) -> int:
    """从环境变量获取整数配置"""
    value = os.environ.get(key)
    if value:
        try:
            return int(value)
        except ValueError:
            pass
    return default


# ============================================================
# 全局配置实例
# ============================================================

# 扫描器配置
scanner_config = ScannerConfig(
    max_wait=_get_env_float('WEAVER_SCAN_MAX_WAIT', 15.0),
    poll_interval=_get_env_float('WEAVER_SCAN_POLL_INTERVAL', 0.8),
)

# 匹配器配置
matcher_config = MatcherConfig(
    min_score_threshold=_get_env_int('WEAVER_MATCH_MIN_SCORE', 60),
)

# 填充器配置
filler_config = FillerConfig(
    element_timeout=_get_env_float('WEAVER_FILL_TIMEOUT', 0.3),
    fill_delay=_get_env_float('WEAVER_FILL_DELAY', 0.1),
)

# 翻页配置
pagination_config = PaginationConfig()

# UI 配置
ui_config = UIConfig()


# ============================================================
# 便捷函数
# ============================================================

def reload_config():
    """
    重新加载配置
    
    从环境变量重新读取配置。
    """
    global scanner_config, matcher_config, filler_config
    
    scanner_config = ScannerConfig(
        max_wait=_get_env_float('WEAVER_SCAN_MAX_WAIT', 15.0),
        poll_interval=_get_env_float('WEAVER_SCAN_POLL_INTERVAL', 0.8),
    )
    
    matcher_config = MatcherConfig(
        min_score_threshold=_get_env_int('WEAVER_MATCH_MIN_SCORE', 60),
    )
    
    filler_config = FillerConfig(
        element_timeout=_get_env_float('WEAVER_FILL_TIMEOUT', 0.3),
        fill_delay=_get_env_float('WEAVER_FILL_DELAY', 0.1),
    )
