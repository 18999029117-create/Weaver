"""
扫描服务

封装页面元素扫描的业务逻辑。
"""

from typing import List, Any, Optional

from app.domain.entities import ElementFingerprint
from app.core.smart_form_analyzer import SmartFormAnalyzer


class ScanningService:
    """
    扫描服务
    
    职责:
    - 扫描页面元素
    - 管理扫描缓存
    - 提供稳定性等待
    """
    
    def __init__(self, tab: Any):
        """
        初始化扫描服务
        
        Args:
            tab: 浏览器标签页对象
        """
        self.tab = tab
        self._cache: List[ElementFingerprint] = []
    
    def scan(self, max_wait: float = 15.0, poll_interval: float = 0.8) -> List[ElementFingerprint]:
        """
        扫描页面元素
        
        Args:
            max_wait: 最大等待时间
            poll_interval: 轮询间隔
            
        Returns:
            ElementFingerprint 列表
        """
        self._cache = SmartFormAnalyzer.deep_scan_page(
            self.tab, 
            max_wait=max_wait,
            poll_interval=poll_interval
        )
        return self._cache
    
    def get_cached(self) -> List[ElementFingerprint]:
        """获取缓存的扫描结果"""
        return self._cache
    
    def clear_cache(self):
        """清除缓存"""
        self._cache = []
    
    def wait_for_stability(self, timeout: float = 10.0) -> bool:
        """
        等待页面稳定
        
        Args:
            timeout: 超时时间
            
        Returns:
            是否稳定
        """
        import time
        
        js_check = """
        (() => {
            const loaders = document.querySelectorAll(
                '.loading, .spinner, .ant-spin-spinning, .el-loading-mask'
            );
            for (let loader of loaders) {
                const style = window.getComputedStyle(loader);
                if (style.display !== 'none' && style.visibility !== 'hidden') {
                    return false;
                }
            }
            return document.readyState === 'complete';
        })();
        """
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.tab.run_js(js_check):
                    return True
            except:
                pass
            time.sleep(0.2)
        
        return False
