"""
工具栏组件

从 process_window.py 提取的工具栏 UI 组件，包含操作按钮、选项下拉框和进度显示。
"""

import customtkinter as ctk
from app.ui.styles import ThemeColors, UIStyles


class AnimatedButton(ctk.CTkButton):
    """Apple 风格动画按钮（本地定义避免循环导入）"""
    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": "#FFFFFF",
            "text_color": "#000000",
            "border_width": 1,
            "border_color": "#000000",
            "hover_color": "#E5E5E5",
            "text_color_disabled": "#BCBCBC",
            "corner_radius": 6,
            "font": (UIStyles.FONT_FAMILY, 13)
        }
        for k, v in defaults.items():
            if k not in kwargs:
                kwargs[k] = v
        super().__init__(master, **kwargs)



class ProcessToolbar(ctk.CTkFrame):
    """智能填表工作台工具栏"""
    
    def __init__(self, master, excel_columns, callbacks, pagination_elements=None):
        """
        初始化工具栏
        
        Args:
            master: 父窗口
            excel_columns: Excel 列名列表
            callbacks: 回调函数字典，包含：
                - on_load, on_save, on_rescan, on_apply_mappings, on_clear
                - on_start, on_stop, on_continue
                - on_pagination_select, on_pagination_mode_change
            pagination_elements: 翻页元素列表
        """
        super().__init__(master, fg_color=ThemeColors.BG_SECONDARY)
        
        self.excel_columns = excel_columns
        self.callbacks = callbacks
        self.pagination_elements = pagination_elements or []
        
        self._create_variables()
        self._build_row1()
        self._build_row2()
        self._build_row3()
    
    def _create_variables(self):
        """创建 UI 变量"""
        self.anchor_var = ctk.StringVar(value="按顺序录入")
        self.mode_var = ctk.StringVar(value="单条录入")
        self.pagination_var = ctk.StringVar(value="未指定")
        self.pagination_mode_var = ctk.StringVar(value="手动翻页")
    
    def _create_dropdown(self, parent, values, variable, command=None, width=130):
        """创建统一样式的下拉框"""
        return ctk.CTkOptionMenu(
            parent,
            values=values,
            variable=variable,
            command=command,
            fg_color="#FFFFFF",
            text_color="#000000",
            button_color="#E5E5E5",
            button_hover_color="#D0D0D0",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#000000",
            dropdown_hover_color="#E5E5E5",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13),
            dropdown_font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13),
            width=width,
            height=30,
            corner_radius=6
        )
    
    def _build_row1(self):
        """构建第一行：操作按钮"""
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(2, 0))
        
        # 存档/读档
        self.load_btn = AnimatedButton(row, text="📂", width=40, height=30,
                                       command=self.callbacks.get('on_load'))
        self.load_btn.pack(side="left", padx=(5, 2), pady=2)
        
        self.save_btn = AnimatedButton(row, text="💾", width=40, height=30,
                                       command=self.callbacks.get('on_save'))
        self.save_btn.pack(side="left", padx=2, pady=2)
        
        # 重新扫描
        self.refresh_btn = AnimatedButton(row, text="🔄重新扫描", height=30,
                                          command=self.callbacks.get('on_rescan'))
        self.refresh_btn.pack(side="left", padx=2, pady=2)
        
        # 应用建议
        self.auto_map_btn = AnimatedButton(row, text="🤖应用建议", height=30,
                                           command=self.callbacks.get('on_apply_mappings'))
        self.auto_map_btn.pack(side="left", padx=2, pady=2)
        
        # 清空连线
        self.clear_mapping_btn = AnimatedButton(row, text="🗑清空", height=30,
                                                command=self.callbacks.get('on_clear'))
        self.clear_mapping_btn.pack(side="left", padx=2, pady=2)
    
    def _build_row2(self):
        """构建第二行：下拉选项"""
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(0, 2))
        
        # 锚定规则
        ctk.CTkLabel(row, text="锚定规则:", font=(UIStyles.FONT_FAMILY, 12),
                    text_color=ThemeColors.TEXT_SECONDARY).pack(side="left", padx=(5, 2))
        
        # 多重锚定配置按钮（紧贴标签）
        self.anchor_config_btn = AnimatedButton(
            row, text="🔗配置", width=60, height=30,
            command=self.callbacks.get('on_anchor_config')
        )
        self.anchor_config_btn.pack(side="left", padx=2)
        
        # 录入模式
        ctk.CTkLabel(row, text="录入模式:", font=(UIStyles.FONT_FAMILY, 12),
                    text_color=ThemeColors.TEXT_SECONDARY).pack(side="left", padx=(15, 2))
        self.mode_selector = self._create_dropdown(row, ["单条录入", "表格批量"], 
                                                   self.mode_var, width=110)
        self.mode_selector.pack(side="left", padx=2)
        
        # 启动按钮
        self.start_btn = ctk.CTkButton(
            row, text="启动", height=32, width=100,
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13, weight="bold"),
            fg_color=ThemeColors.ACCENT_PRIMARY,
            text_color="white",
            hover_color=ThemeColors.ACCENT_SECONDARY,
            corner_radius=6,
            command=self.callbacks.get('on_start')
        )
        self.start_btn.pack(side="right", padx=5, pady=2)
        
        # 停止按钮
        self.stop_btn = ctk.CTkButton(
            row, text="停止", height=32, width=80,
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13),
            fg_color="#FFFFFF", text_color="#000000",
            border_width=1, border_color="#000000",
            hover_color="#E5E5E5", corner_radius=6,
            state="disabled",
            command=self.callbacks.get('on_stop')
        )
        self.stop_btn.pack(side="right", padx=2, pady=2)
    
    def _build_row3(self):
        """构建第三行：翻页控制"""
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(0, 2))
        
        # 翻页按钮选择
        ctk.CTkLabel(row, text="翻页按钮:", font=(UIStyles.FONT_FAMILY, 12),
                    text_color=ThemeColors.TEXT_SECONDARY).pack(side="left", padx=(5, 2))
        
        pagination_options = ["未指定"]
        if self.pagination_elements:
            pagination_options += [p['text'] for p in self.pagination_elements]
        
        self.pagination_selector = self._create_dropdown(
            row, pagination_options, self.pagination_var,
            command=self.callbacks.get('on_pagination_select'), width=150
        )
        self.pagination_selector.pack(side="left", padx=2)
        
        # 翻页状态标签
        self.pagination_status = ctk.CTkLabel(row, text="", 
                                             font=(UIStyles.FONT_FAMILY, 11),
                                             text_color="#666666")
        self.pagination_status.pack(side="left", padx=5)
        
        # 翻页模式选择
        ctk.CTkLabel(row, text="翻页模式:", font=(UIStyles.FONT_FAMILY, 12),
                    text_color=ThemeColors.TEXT_SECONDARY).pack(side="left", padx=(15, 2))
        
        self.pagination_mode_selector = self._create_dropdown(
            row, ["手动翻页", "全自动"], self.pagination_mode_var,
            command=self.callbacks.get('on_pagination_mode_change'), width=110
        )
        self.pagination_mode_selector.pack(side="left", padx=2)
        
        # 继续录入按钮
        self.continue_btn = ctk.CTkButton(
            row, text="继续录入", height=30, width=100,
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12),
            fg_color="#FFFFFF", text_color="#000000",
            border_width=1, border_color="#000000",
            hover_color="#E5E5E5", corner_radius=6,
            state="disabled",
            command=self.callbacks.get('on_continue')
        )
        self.continue_btn.pack(side="left", padx=10)
        
        # 进度显示
        self.progress_label = ctk.CTkLabel(row, text="就绪", 
                                          font=(UIStyles.FONT_FAMILY, 11),
                                          text_color="#000000")
        self.progress_label.pack(side="right", padx=10)
    
    def update_pagination_options(self, pagination_elements):
        """更新翻页按钮选项"""
        self.pagination_elements = pagination_elements
        options = ["未指定"]
        if pagination_elements:
            options += [p['text'] for p in pagination_elements]
        self.pagination_selector.configure(values=options)
