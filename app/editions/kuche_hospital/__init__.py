"""
库车市人民医院定制版

针对库车市人民医院的专属定制功能。
"""

from typing import Any, Dict, List, Tuple
from app.editions.base_edition import BaseEdition


class KucheHospitalEdition(BaseEdition):
    """
    库车市人民医院定制版
    
    定制功能:
    - 耗材采购自动化处理（按医保码统计并批量填充）
    """
    
    name = "库车市人民医院"
    icon = "🏥"
    description = "库车市人民医院专属定制功能"
    
    def __init__(self):
        super().__init__()
        self._processor = None
    
    def on_app_start(self, app: Any) -> None:
        """应用启动时显示定制信息"""
        print("[库车医院版] 🏥 启动库车市人民医院定制版...")
    
    def on_app_ready(self, app: Any) -> None:
        """应用就绪后添加专属功能按钮"""
        print("[库车医院版] 定制功能已就绪")
    
    def on_excel_loaded(self, df: Any) -> Any:
        """
        Excel 加载后的定制处理
        """
        print(f"[库车医院版] Excel 数据已加载: {len(df)} 行")
        
        # 检查是否有医保码列
        if '医保码' in df.columns:
            unique_codes = df['医保码'].dropna().nunique()
            print(f"[库车医院版] 检测到医保码列，共 {unique_codes} 个唯一代码")
        
        return df
    
    def get_extra_toolbar_buttons(self) -> List[Dict[str, Any]]:
        """
        返回库车医院专属的工具栏按钮
        """
        return [
            {
                "text": "🏥 耗材采购",
                "icon": "🏥",
                "tooltip": "启动耗材采购自动化",
                "command_name": "start_consumable_procurement",
            },
        ]
    
    def start_consumable_procurement(self, app: Any, excel_data: Any, browser_tab: Any) -> Dict[str, Any]:
        """
        启动耗材采购自动化流程
        
        Args:
            app: 主应用实例
            excel_data: Excel 数据
            browser_tab: 浏览器标签页
            
        Returns:
            处理结果
        """
        from app.customizations.kuche_hospital.consumable_processor import ConsumableProcessor
        
        def progress_callback(msg):
            print(msg)
            # 如果 app 有日志方法，也输出到 UI
            if hasattr(app, 'add_log'):
                app.add_log(msg)
        
        def confirm_callback(message):
            """弹出确认对话框，显示【继续】和【忽略】按钮"""
            import tkinter as tk
            from tkinter import ttk
            
            result = [False]  # 用列表存储结果，以便在嵌套函数中修改
            
            dialog = tk.Toplevel()
            dialog.title("需要手动处理")
            dialog.geometry("400x200")
            dialog.transient()
            dialog.grab_set()
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - 400) // 2
            y = (dialog.winfo_screenheight() - 200) // 2
            dialog.geometry(f"+{x}+{y}")
            
            # 消息标签
            ttk.Label(dialog, text=message, wraplength=360, justify="center").pack(pady=20, padx=20)
            
            # 按钮框架
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=20)
            
            def on_continue():
                result[0] = True
                dialog.destroy()
            
            def on_ignore():
                result[0] = False
                dialog.destroy()
            
            ttk.Button(btn_frame, text="继续（已手动填写）", command=on_continue).pack(side="left", padx=10)
            ttk.Button(btn_frame, text="忽略", command=on_ignore).pack(side="left", padx=10)
            
            dialog.wait_window()
            return result[0]
        
        processor = ConsumableProcessor(
            browser_tab=browser_tab,
            progress_callback=progress_callback,
            confirm_callback=confirm_callback,
            auto_mode=True  # 默认自动模式，但多行情况会强制暂停
        )
        
        # 执行处理
        result = processor.process(excel_data, code_column='医保码')
        
        return result
    
    def get_config_overrides(self) -> Dict[str, Any]:
        """
        返回库车医院的配置覆盖
        """
        return {
            'code_column': '医保码',  # 医保码列名
        }

