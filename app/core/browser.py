"""
浏览器模块 - 兼容层

此文件保持向后兼容，实际实现已移至 infrastructure.browser

注意: 新代码应直接从 app.infrastructure.browser 导入
"""

# 向后兼容导入
from app.infrastructure.browser.browser_manager import BrowserManager

__all__ = ['BrowserManager']
