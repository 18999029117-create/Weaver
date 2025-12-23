"""
翻页服务

封装分页控制的业务逻辑。
"""

from typing import List, Any, Optional, Callable

from app.core.pagination_controller import PaginationController


class PaginationService:
    """
    翻页服务
    
    职责:
    - 检测翻页按钮
    - 执行翻页操作
    - 等待页面加载
    """
    
    def __init__(self, tab: Any):
        """
        初始化翻页服务
        
        Args:
            tab: 浏览器标签页对象
        """
        self.tab = tab
        self.controller: Optional[PaginationController] = None
        self.detected_buttons: List[dict] = []
    
    def detect_buttons(self) -> List[dict]:
        """
        检测翻页按钮
        
        Returns:
            翻页按钮列表
        """
        js_detect = """
        (function() {
            const keywords = ['下一页', '下一条', 'Next', 'next', '下页', '后一页', 
                              '翻页', '下一步', '向后', '››', '»', '>>', '>', '→'];
            const results = [];
            
            const elements = document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"], .btn, .page-btn');
            
            elements.forEach((el, idx) => {
                const text = (el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
                const className = el.className || '';
                const id = el.id || '';
                
                let isMatch = false;
                let matchKeyword = '';
                
                for (let kw of keywords) {
                    if (text.includes(kw) || className.toLowerCase().includes('next') || id.toLowerCase().includes('next')) {
                        isMatch = true;
                        matchKeyword = text || kw;
                        break;
                    }
                }
                
                if (isMatch && text.length < 50) {
                    let xpath = '';
                    if (el.id) {
                        xpath = `//*[@id="${el.id}"]`;
                    } else {
                        let path = [];
                        let current = el;
                        while (current && current !== document.body) {
                            let tag = current.tagName.toLowerCase();
                            let parent = current.parentElement;
                            if (parent) {
                                let siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
                                if (siblings.length > 1) {
                                    let index = siblings.indexOf(current) + 1;
                                    tag += '[' + index + ']';
                                }
                            }
                            path.unshift(tag);
                            current = parent;
                        }
                        xpath = '//' + path.join('/');
                    }
                    
                    results.push({
                        text: matchKeyword.substring(0, 30),
                        tagName: el.tagName.toLowerCase(),
                        id: el.id || '',
                        className: (el.className || '').substring(0, 50),
                        xpath: xpath
                    });
                }
            });
            
            return results;
        })();
        """
        
        try:
            result = self.tab.run_js(js_detect)
            
            self.detected_buttons = []
            if result and isinstance(result, list):
                seen_texts = set()
                for item in result:
                    text = item.get('text', '翻页按钮')
                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        self.detected_buttons.append({
                            'text': text,
                            'xpath': item.get('xpath', ''),
                            'id': item.get('id', ''),
                            'tag': item.get('tagName', 'button')
                        })
            
            self.detected_buttons = self.detected_buttons[:10]
            return self.detected_buttons
            
        except Exception as e:
            print(f"翻页检测异常: {e}")
            return []
    
    def setup(self, xpath: str = None, selector: str = None):
        """
        设置翻页按钮
        
        Args:
            xpath: XPath 选择器
            selector: CSS 选择器
        """
        self.controller = PaginationController(self.tab)
        self.controller.set_next_button(selector=selector, xpath=xpath)
    
    def click_next(self, wait_after: float = 1.0) -> bool:
        """
        点击下一页
        
        Args:
            wait_after: 点击后等待时间
            
        Returns:
            是否成功
        """
        if not self.controller:
            return False
        return self.controller.click_next_page(wait_after=wait_after)
    
    def wait_for_ready(self, timeout: float = 5.0) -> bool:
        """
        等待页面加载完成
        
        Args:
            timeout: 超时时间
            
        Returns:
            是否加载完成
        """
        if not self.controller:
            return True
        return self.controller.wait_for_page_ready(timeout=timeout)
    
    def on_page_change(self, callback: Callable):
        """注册页面变化回调"""
        if self.controller:
            self.controller.on_page_change(callback)
    
    def reset(self):
        """重置翻页状态"""
        if self.controller:
            self.controller.reset()
