"""
Weaver (维沃) - 智能网页自动化填表工具

程序入口，支持多版本选择。
"""

import sys
import os

# 确保程序根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui.styles import UIStyles
from app.ui.main_window import AutoFillerUI
from app.editions.registry import get_edition


# 全局版本实例
_current_edition = None


def get_current_edition():
    """获取当前运行的版本实例"""
    global _current_edition
    return _current_edition


def main():
    """程序入口"""
    global _current_edition
    
    # 应用全局样式
    UIStyles.apply_global_styles()
    
    # 创建隐藏的根窗口用于显示对话框
    import customtkinter as ctk
    root = ctk.CTk()
    root.withdraw()  # 隐藏主窗口
    
    # 显示版本选择对话框
    from app.ui.dialogs.edition_selector import show_edition_selector
    selected_edition_id = show_edition_selector(root)
    
    # 销毁临时根窗口
    root.destroy()
    
    # 加载选择的版本
    print(f"[Main] 加载版本: {selected_edition_id}")
    _current_edition = get_edition(selected_edition_id)
    
    # 创建主应用
    app = AutoFillerUI()
    
    # 调用版本启动钩子
    _current_edition.on_app_start(app)
    
    # 将版本实例注入到 app
    app.edition = _current_edition
    
    # 更新窗口标题
    app.title(f"Weaver (维沃) v1.0 Beta - {_current_edition.name}")
    
    # 调用版本就绪钩子
    _current_edition.on_app_ready(app)
    
    # 运行主循环
    app.mainloop()


if __name__ == "__main__":
    main()

