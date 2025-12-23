"""
Analyzer 模块

提供页面元素分析功能，包括：
- PageScanner: 主页面元素扫描
- IframeScanner: Iframe 递归扫描

使用示例:
    from app.core.analyzer import SmartFormAnalyzer
    
    fingerprints = SmartFormAnalyzer.deep_scan_page(tab)
"""

from typing import List, TYPE_CHECKING

from .page_scanner import PageScanner
from .iframe_scanner import IframeScanner

if TYPE_CHECKING:
    from ..fingerprint import ElementFingerprint


class SmartFormAnalyzer:
    """
    智能表单分析器 (Facade 门面类)
    
    提供统一的页面扫描接口，整合主页面扫描和 Iframe 扫描。
    保持与原有代码的兼容性。
    """
    
    @staticmethod
    def get_analysis_js() -> str:
        """获取页面分析 JavaScript 代码"""
        return PageScanner.get_analysis_js()
    
    @classmethod
    def deep_scan_page(cls, tab, timeout: float = 10.0) -> List['ElementFingerprint']:
        """
        深度扫描页面（主文档 + Iframe）
        
        Args:
            tab: DrissionPage 的 tab 对象
            timeout: 超时时间（秒）
            
        Returns:
            所有元素的 ElementFingerprint 列表
        """
        # 1. 扫描主页面
        fingerprints = PageScanner.scan_to_fingerprints(tab, timeout)
        
        # 2. 扫描 Iframe
        iframe_fingerprints = IframeScanner.scan_iframes(tab)
        if iframe_fingerprints:
            fingerprints.extend(iframe_fingerprints)
            print(f"   📦 Iframe 内元素: {len(iframe_fingerprints)} 个")
        
        print(f"\\n🎯 总计: {len(fingerprints)} 个可操作元素")
        
        return fingerprints


__all__ = [
    'SmartFormAnalyzer',
    'PageScanner',
    'IframeScanner',
]
