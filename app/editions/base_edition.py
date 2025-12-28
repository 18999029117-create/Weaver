"""
版本基类

所有定制版本都继承此类，通过覆盖钩子方法实现定制功能。
"""

from typing import Any, Dict, List, Optional, Tuple
from abc import ABC


class BaseEdition(ABC):
    """
    版本基类
    
    定制版本继承此类并覆盖需要定制的钩子方法。
    未覆盖的方法使用默认实现（即通用版本行为）。
    
    Attributes:
        name: 版本显示名称
        icon: 版本图标 (emoji)
        description: 版本描述
    """
    
    name: str = "通用版本"
    icon: str = "🌐"
    description: str = "适用于所有用户的标准功能"
    
    # ==================== 生命周期钩子 ====================
    
    def on_app_start(self, app: Any) -> None:
        """
        应用启动时调用
        
        可用于：显示定制 logo、初始化特殊配置等
        
        Args:
            app: 主窗口实例
        """
        pass
    
    def on_app_ready(self, app: Any) -> None:
        """
        应用就绪后调用（UI 构建完成）
        
        Args:
            app: 主窗口实例
        """
        pass
    
    # ==================== 数据处理钩子 ====================
    
    def on_excel_loaded(self, df: Any) -> Any:
        """
        Excel 数据加载后调用
        
        可用于：数据预处理、添加计算列、格式转换等
        
        Args:
            df: pandas DataFrame
            
        Returns:
            处理后的 DataFrame
        """
        return df
    
    def on_fill_before(
        self, 
        data: Dict[str, Any], 
        mappings: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        填充前调用
        
        可用于：数据验证、自动补全、添加前缀等
        
        Args:
            data: 当前行数据
            mappings: 字段映射
            
        Returns:
            (处理后的数据, 处理后的映射)
        """
        return data, mappings
    
    def on_fill_after(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        填充后调用
        
        可用于：记录日志、统计数据、触发后续操作等
        
        Args:
            results: 填充结果
            
        Returns:
            处理后的结果
        """
        return results
    
    def on_page_scanned(self, elements: List[Any]) -> List[Any]:
        """
        页面扫描完成后调用
        
        可用于：过滤元素、添加特殊标记等
        
        Args:
            elements: 扫描到的元素列表
            
        Returns:
            处理后的元素列表
        """
        return elements
    
    # ==================== UI 定制钩子 ====================
    
    def get_extra_toolbar_buttons(self) -> List[Dict[str, Any]]:
        """
        返回额外的工具栏按钮
        
        Returns:
            按钮配置列表 [{"text": "按钮", "icon": "🔧", "command": callable}, ...]
        """
        return []
    
    def get_custom_menu_items(self) -> List[Dict[str, Any]]:
        """
        返回自定义菜单项
        
        Returns:
            菜单项配置列表
        """
        return []
    
    # ==================== 配置钩子 ====================
    
    def get_config_overrides(self) -> Dict[str, Any]:
        """
        返回配置覆盖项
        
        可用于：调整超时时间、匹配阈值等
        
        Returns:
            配置覆盖字典
        """
        return {}
