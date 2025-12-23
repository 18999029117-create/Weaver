"""
配置模块单元测试
"""

import os
import pytest
from app.config import (
    ScannerConfig, MatcherConfig, FillerConfig, PaginationConfig, UIConfig,
    scanner_config, matcher_config, filler_config,
    _get_env_float, _get_env_int, reload_config
)


class TestConfigDataclasses:
    """配置数据类测试"""
    
    def test_scanner_config_defaults(self):
        """ScannerConfig 默认值"""
        config = ScannerConfig()
        
        assert config.max_wait == 15.0
        assert config.poll_interval == 0.8
        assert config.loading_timeout == 5.0
    
    def test_matcher_config_defaults(self):
        """MatcherConfig 默认值"""
        config = MatcherConfig()
        
        assert config.min_score_threshold == 60
        assert config.exact_match_score == 100
    
    def test_filler_config_defaults(self):
        """FillerConfig 默认值"""
        config = FillerConfig()
        
        assert config.element_timeout == 0.3
        assert config.retry_count == 3
    
    def test_configs_are_mutable(self):
        """配置应可修改"""
        config = ScannerConfig()
        config.max_wait = 30.0
        
        assert config.max_wait == 30.0


class TestEnvironmentVariables:
    """环境变量测试"""
    
    def test_get_env_float_with_valid_value(self, monkeypatch):
        """有效浮点数环境变量"""
        monkeypatch.setenv('TEST_FLOAT', '25.5')
        
        result = _get_env_float('TEST_FLOAT', 10.0)
        assert result == 25.5
    
    def test_get_env_float_with_invalid_value(self, monkeypatch):
        """无效浮点数环境变量返回默认值"""
        monkeypatch.setenv('TEST_FLOAT', 'not_a_number')
        
        result = _get_env_float('TEST_FLOAT', 10.0)
        assert result == 10.0
    
    def test_get_env_float_with_missing_key(self):
        """缺失环境变量返回默认值"""
        result = _get_env_float('NONEXISTENT_KEY_12345', 42.0)
        assert result == 42.0
    
    def test_get_env_int_with_valid_value(self, monkeypatch):
        """有效整数环境变量"""
        monkeypatch.setenv('TEST_INT', '100')
        
        result = _get_env_int('TEST_INT', 50)
        assert result == 100
    
    def test_get_env_int_with_invalid_value(self, monkeypatch):
        """无效整数环境变量返回默认值"""
        monkeypatch.setenv('TEST_INT', 'abc')
        
        result = _get_env_int('TEST_INT', 50)
        assert result == 50


class TestGlobalConfigs:
    """全局配置实例测试"""
    
    def test_scanner_config_is_accessible(self):
        """scanner_config 应可访问"""
        assert scanner_config is not None
        assert hasattr(scanner_config, 'max_wait')
    
    def test_matcher_config_is_accessible(self):
        """matcher_config 应可访问"""
        assert matcher_config is not None
        assert hasattr(matcher_config, 'min_score_threshold')
    
    def test_filler_config_is_accessible(self):
        """filler_config 应可访问"""
        assert filler_config is not None
        assert hasattr(filler_config, 'element_timeout')


class TestReloadConfig:
    """配置重载测试"""
    
    def test_reload_config_updates_scanner(self, monkeypatch):
        """reload_config 应更新 scanner_config"""
        monkeypatch.setenv('WEAVER_SCAN_MAX_WAIT', '99.0')
        
        reload_config()
        
        from app.config import scanner_config as reloaded
        assert reloaded.max_wait == 99.0
