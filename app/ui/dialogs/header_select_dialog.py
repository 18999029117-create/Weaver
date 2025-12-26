"""
表头选择对话框

当自动检测置信度较低时，让用户通过点击选择正确的表头行。
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Optional, Callable
import pandas as pd

from app.ui.styles import ThemeColors, UIStyles
from app.ui.components import AnimatedButton


class HeaderSelectDialog(ctk.CTkToplevel):
    """
    表头选择对话框
    
    显示 Excel 文件的前 N 行，让用户点击选择正确的表头行。
    """
    
    def __init__(
        self, 
        master, 
        preview_data: pd.DataFrame,
        detected_row: int = 0,
        confidence: float = 50.0,
        on_confirm: Optional[Callable[[int], None]] = None
    ):
        """
        初始化对话框
        
        Args:
            master: 父窗口
            preview_data: 预览数据 (原始 DataFrame，无表头)
            detected_row: 自动检测的表头行 (0-based)
            confidence: 检测置信度
            on_confirm: 确认回调 (row_index)
        """
        super().__init__(master)
        
        self.preview_data = preview_data
        self.detected_row = detected_row
        self.selected_row = detected_row
        self.confidence = confidence
        self.on_confirm = on_confirm
        
        # 窗口设置
        self.title("📊 选择表头行")
        self.geometry("800x500")
        self.configure(fg_color=ThemeColors.BG_DARK)
        self.transient(master)
        self.grab_set()
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 800) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"800x500+{x}+{y}")
        
        self._build_ui()
    
    def _build_ui(self):
        """构建 UI"""
        # 标题区
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="📊 请选择正确的表头行",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=18, weight="bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w")
        
        # 置信度提示
        if self.confidence < 70:
            hint_text = f"系统检测到表头可能在 第 {self.detected_row + 1} 行（置信度: {self.confidence:.0f}%，较低）"
            hint_color = ThemeColors.WARNING
        else:
            hint_text = f"系统检测到表头在 第 {self.detected_row + 1} 行（置信度: {self.confidence:.0f}%）"
            hint_color = ThemeColors.SUCCESS
        
        ctk.CTkLabel(
            title_frame,
            text=hint_text,
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12),
            text_color=hint_color
        ).pack(anchor="w", pady=(5, 0))
        
        ctk.CTkLabel(
            title_frame,
            text="点击下方表格中的某一行，将其设为表头：",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(5, 0))
        
        # 表格预览区
        table_frame = ctk.CTkFrame(self, fg_color=ThemeColors.BG_SECONDARY, corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 创建 Treeview (使用 ttk 因为 CTk 没有内置表格)
        style = ttk.Style()
        style.configure(
            "Header.Treeview",
            background=ThemeColors.BG_SECONDARY,
            foreground=ThemeColors.TEXT_PRIMARY,
            fieldbackground=ThemeColors.BG_SECONDARY,
            rowheight=30,
            font=(UIStyles.FONT_FAMILY, 11)
        )
        style.configure(
            "Header.Treeview.Heading",
            font=(UIStyles.FONT_FAMILY, 11, "bold"),
            background="#E0E0E0",
            foreground="#333333"
        )
        style.map("Header.Treeview", background=[("selected", ThemeColors.ACCENT_PRIMARY)])
        
        # 创建列
        num_cols = len(self.preview_data.columns) if len(self.preview_data) > 0 else 1
        columns = ["row"] + [f"col{i}" for i in range(num_cols)]
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Header.Treeview",
            selectmode="browse"
        )
        
        # 设置列标题
        self.tree.heading("row", text="行号")
        self.tree.column("row", width=50, anchor="center")
        
        for i in range(num_cols):
            col_id = f"col{i}"
            self.tree.heading(col_id, text=f"列{i + 1}")
            self.tree.column(col_id, width=100, anchor="w")
        
        # 填充数据
        for idx, row in self.preview_data.iterrows():
            values = [f"第{idx + 1}行"] + [str(v)[:30] for v in row.tolist()]  # 截断长文本
            item_id = self.tree.insert("", "end", values=values, tags=(f"row_{idx}",))
            
            # 高亮检测到的行
            if idx == self.detected_row:
                self.tree.selection_set(item_id)
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar_y.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # 绑定点击事件
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)
        
        # 底部按钮区
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.confirm_btn = AnimatedButton(
            btn_frame,
            text=f"✅ 确认使用第 {self.selected_row + 1} 行作为表头",
            height=40,
            font=(UIStyles.FONT_FAMILY, 13, "bold"),
            command=self._on_confirm
        )
        self.confirm_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            height=40,
            fg_color="#666666",
            hover_color="#888888",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13),
            command=self.destroy
        )
        cancel_btn.pack(side="right", width=100)
    
    def _on_row_select(self, event):
        """行选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        # 从 tag 中获取行号
        tags = self.tree.item(item, "tags")
        for tag in tags:
            if tag.startswith("row_"):
                self.selected_row = int(tag.replace("row_", ""))
                self.confirm_btn.configure(
                    text=f"✅ 确认使用第 {self.selected_row + 1} 行作为表头"
                )
                break
    
    def _on_confirm(self):
        """确认按钮点击"""
        if self.on_confirm:
            self.on_confirm(self.selected_row)
        self.destroy()
