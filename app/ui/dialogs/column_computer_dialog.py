"""
列计算器对话框组件

从 process_window.py 提取的独立对话框，用于添加 Excel 计算列。
"""

import customtkinter as ctk
from app.ui.styles import UIStyles
from app.ui.components import AnimatedButton


class ColumnComputerDialog(ctk.CTkToplevel):
    """智能列计算器对话框"""
    
    def __init__(self, master, excel_data, on_complete_callback, add_log_callback):
        """
        初始化列计算器对话框
        
        Args:
            master: 父窗口
            excel_data: pandas DataFrame
            on_complete_callback: 计算完成后的回调 (new_col_name)
            add_log_callback: 日志回调 (message, level)
        """
        super().__init__(master)
        
        self.excel_data = excel_data
        self.on_complete_callback = on_complete_callback
        self.add_log = add_log_callback
        
        self._setup_dialog()
        self._setup_ui()
    
    def _setup_dialog(self):
        """设置对话框属性"""
        self.title("➕ 添加智能计算列")
        self.geometry("400x380")
        self.attributes("-topmost", True)
        self.configure(fg_color="#FFFFFF")
    
    def _setup_ui(self):
        """构建 UI"""
        columns = self.excel_data.columns.tolist()
        
        # 1. 分组依据
        ctk.CTkLabel(self, text="1. 分组依据 (按谁归类?):", 
                    font=(UIStyles.FONT_FAMILY, 13), text_color="#000000").pack(pady=(15,5))
        self.group_col_var = ctk.StringVar(value=columns[0])
        self._create_dropdown(columns, self.group_col_var)
        
        # 2. 计算目标
        ctk.CTkLabel(self, text="2. 计算目标 (算哪一列?):", 
                    font=(UIStyles.FONT_FAMILY, 13), text_color="#000000").pack(pady=(15,5))
        self.target_col_var = ctk.StringVar(value=columns[0])
        self._create_dropdown(columns, self.target_col_var)
        
        # 3. 计算方式
        ctk.CTkLabel(self, text="3. 计算方式:", 
                    font=(UIStyles.FONT_FAMILY, 13), text_color="#000000").pack(pady=(15,5))
        self.op_map = {
            "计数 (Count)": "count", 
            "求和 (Sum)": "sum", 
            "平均值 (Mean)": "mean", 
            "最大值 (Max)": "max", 
            "最小值 (Min)": "min"
        }
        self.op_var = ctk.StringVar(value="计数 (Count)")
        self._create_dropdown(list(self.op_map.keys()), self.op_var)
        
        # 确认按钮
        AnimatedButton(self, text="✅立即生成", command=self._on_confirm, height=36).pack(pady=20)
    
    def _create_dropdown(self, values, variable):
        """创建统一样式的下拉框"""
        ctk.CTkOptionMenu(
            self, 
            values=values, 
            variable=variable,
            fg_color="#FFFFFF", 
            text_color="#000000", 
            button_color="#E5E5E5",
            button_hover_color="#D0D0D0", 
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#000000", 
            dropdown_hover_color="#E5E5E5",
            font=(UIStyles.FONT_FAMILY, 12), 
            corner_radius=6
        ).pack(pady=5)
    
    def _on_confirm(self):
        """确认计算"""
        try:
            grp = self.group_col_var.get()
            tgt = self.target_col_var.get()
            op_name = self.op_var.get()
            op = self.op_map[op_name]
            
            new_col_name = f"{grp}_{op}_{tgt}" if op != 'count' else f"{grp}_出现次数"
            
            # 执行计算
            self.add_log(f"🧮 正在计算: 按[{grp}]对[{tgt}]做[{op_name}]...", "info")
            
            if op == 'count':
                self.excel_data[new_col_name] = self.excel_data.groupby(grp)[grp].transform('count')
            else:
                try:
                    import pandas as pd
                    temp_df = self.excel_data.copy()
                    temp_df[tgt] = pd.to_numeric(temp_df[tgt], errors='coerce')
                    self.excel_data[new_col_name] = temp_df.groupby(grp)[tgt].transform(op)
                except Exception as e:
                    self.add_log(f"⚠️ 数据转换失败: {e}", "error")
                    return

            self.add_log(f"✅ 計算完成! 新增列: [{new_col_name}]", "success")
            
            # 触发回调
            if self.on_complete_callback:
                self.on_complete_callback(new_col_name)
                
            self.destroy()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.add_log(f"❌ 计算失败: {e}", "error")
