"""
日志模块单元测试
"""

import logging
import pytest
from app.utils.logger import (
    WeaverLogger, get_logger, setup_logging, log
)


class TestWeaverLogger:
    """WeaverLogger 测试"""
    
    def test_logger_creation(self):
        """创建日志器"""
        logger = WeaverLogger('test_module')
        
        assert logger is not None
        assert logger.logger is not None
    
    def test_info_log(self, capsys):
        """info 级别日志"""
        setup_logging(level=logging.INFO)
        logger = WeaverLogger('test')
        
        logger.info('Test info message')
        
        captured = capsys.readouterr()
        assert 'Test info message' in captured.out
    
    def test_success_log(self, capsys):
        """success 级别日志（带 ✅ 前缀）"""
        setup_logging(level=logging.DEBUG)
        logger = WeaverLogger('test')
        
        logger.success('Operation completed')
        
        captured = capsys.readouterr()
        assert '✅' in captured.out
        assert 'Operation completed' in captured.out
    
    def test_warning_log(self, capsys):
        """warning 级别日志"""
        setup_logging(level=logging.WARNING)
        logger = WeaverLogger('test')
        
        logger.warning('Warning message')
        
        captured = capsys.readouterr()
        assert 'Warning message' in captured.out
    
    def test_error_log(self, capsys):
        """error 级别日志"""
        setup_logging(level=logging.ERROR)
        logger = WeaverLogger('test')
        
        logger.error('Error message')
        
        captured = capsys.readouterr()
        assert 'Error message' in captured.out


class TestUICallback:
    """UI 回调测试"""
    
    def test_callback_is_called(self):
        """日志时应调用 UI 回调"""
        callback_messages = []
        
        def mock_callback(message, level):
            callback_messages.append((message, level))
        
        logger = WeaverLogger('test', ui_callback=mock_callback)
        logger.info('Test message')
        
        assert len(callback_messages) == 1
        assert callback_messages[0][0] == 'Test message'
        assert callback_messages[0][1] == 'info'
    
    def test_callback_receives_correct_level(self):
        """UI 回调应接收正确的级别"""
        callback_messages = []
        
        def mock_callback(message, level):
            callback_messages.append(level)
        
        logger = WeaverLogger('test', ui_callback=mock_callback)
        
        logger.info('info')
        logger.warning('warning')
        logger.error('error')
        logger.success('success')
        
        assert 'info' in callback_messages
        assert 'warning' in callback_messages
        assert 'error' in callback_messages
        assert 'success' in callback_messages
    
    def test_callback_failure_does_not_crash(self):
        """回调失败不应崩溃"""
        def bad_callback(message, level):
            raise RuntimeError('Callback error')
        
        logger = WeaverLogger('test', ui_callback=bad_callback)
        
        # 不应抛出异常
        logger.info('This should not crash')
    
    def test_set_ui_callback(self):
        """可以更新 UI 回调"""
        messages = []
        
        logger = WeaverLogger('test')
        logger.set_ui_callback(lambda m, l: messages.append(m))
        
        logger.info('After callback set')
        
        assert 'After callback set' in messages


class TestGetLogger:
    """get_logger 函数测试"""
    
    def test_returns_weaver_logger(self):
        """get_logger 返回 WeaverLogger 实例"""
        logger = get_logger('test_module')
        
        assert isinstance(logger, WeaverLogger)
    
    def test_with_ui_callback(self):
        """get_logger 支持 UI 回调"""
        messages = []
        logger = get_logger('test', ui_callback=lambda m, l: messages.append(m))
        
        logger.info('Test')
        
        assert 'Test' in messages


class TestSetupLogging:
    """setup_logging 函数测试"""
    
    def test_sets_log_level(self, capsys):
        """设置日志级别"""
        setup_logging(level=logging.WARNING)
        
        logger = logging.getLogger('test_level')
        logger.info('Should not appear')
        logger.warning('Should appear')
        
        captured = capsys.readouterr()
        assert 'Should not appear' not in captured.out
        assert 'Should appear' in captured.out


class TestConvenienceLog:
    """便捷 log 函数测试"""
    
    def test_log_info(self, capsys):
        """log 函数 info 级别"""
        setup_logging(level=logging.INFO)
        
        log('Test message', 'info')
        
        captured = capsys.readouterr()
        assert 'Test message' in captured.out
    
    def test_log_default_level(self, capsys):
        """log 函数默认级别"""
        setup_logging(level=logging.INFO)
        
        log('Default level message')
        
        captured = capsys.readouterr()
        assert 'Default level message' in captured.out
