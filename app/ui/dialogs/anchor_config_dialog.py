"""
锚定配置对话框

允许用户查看和调整自动匹配结果，配置多重锚定列。
遵循 CONTRIBUTING.md 中的 UI 层规范。
"""

import customtkinter as ctk
from typing import List, Optional, Callable

from app.domain.entities.anchor_config import AnchorConfig, AnchorPair, WebColumnInfo
from app.core.anchor_matcher import AnchorMatcher


class AnchorConfigDialog(ctk.CTkToplevel):
    """
    锚定配置对话框
    
    功能:
    - 显示自动匹配结果
    - 允许手动添加/删除/修改锚定列配对
    - 下拉选择 Excel 列和网页列
    """
    
    def __init__(
        self,
        parent,
        excel_columns: List[str],
        web_columns: List[WebColumnInfo],
        initial_config: Optional[AnchorConfig] = None,
        on_confirm: Optional[Callable[[AnchorConfig], None]] = None
    ):
        """
        初始化锚定配置对话框
        
        Args:
            parent: 父窗口
            excel_columns: Excel 列名列表
            web_columns: 网页列信息列表
            initial_config: 初始配置（可选，用于手动调整）
            on_confirm: 确认回调函数
        """
        super().__init__(parent)
        
        self.excel_columns = excel_columns
        self.web_columns = web_columns
        self.on_confirm = on_confirm
        
        # 分离只读列和输入列
        self.readonly_columns = [c for c in web_columns if c.is_readonly]
        self.input_columns = [c for c in web_columns if c.is_input]
        
        # 如果没有初始配置，执行自动匹配
        if initial_config:
            self.config = initial_config
        else:
            self.config = AnchorMatcher.auto_match(excel_columns, web_columns)
        
        # 存储 UI 组件引用
        self.anchor_rows = []  # [(checkbox_var, excel_combo, web_combo)]
        
        self._setup_window()
        self._create_ui()
    
    def _setup_window(self):
        """设置窗口属性"""
        self.title("锚定列配置")
        self.geometry("700x500")
        self.resizable(True, True)
        
        # 模态窗口
        self.transient(self.master)
        self.grab_set()
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 700) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """创建 UI 组件"""
        # 标题
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            title_frame,
            text="🔗 多重锚定列配置",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")
        
        if self.config.auto_matched:
            ctk.CTkLabel(
                title_frame,
                text=f"(自动匹配 · 置信度 {self.config.match_confidence:.0f}%)",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(side="left", padx=10)
        
        # 说明文字
        ctk.CTkLabel(
            self,
            text="选择用于精准匹配行的锚定列（如医保编码、物资名称等）",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(fill="x", padx=20, pady=(0, 10))
        
        # 锚定列配置区域
        self._create_anchor_section()
        
        # 待填列预览
        self._create_fill_section()
        
        # 底部按钮
        self._create_buttons()
    
    def _create_anchor_section(self):
        """创建锚定列配置区域"""
        anchor_frame = ctk.CTkFrame(self)
        anchor_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        # 标题行
        header = ctk.CTkFrame(anchor_frame, fg_color="transparent")
        header.pack(fill="x", pady=(10, 5))
        
        ctk.CTkLabel(header, text="锚定列（用于匹配行）", font=ctk.CTkFont(weight="bold")).pack(side="left")
        
        ctk.CTkButton(
            header, text="+ 添加锚定列", width=100, height=28,
            command=self._add_anchor_row
        ).pack(side="right")
        
        # 列表头
        list_header = ctk.CTkFrame(anchor_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=5)
        
        ctk.CTkLabel(list_header, text="启用", width=50).pack(side="left")
        ctk.CTkLabel(list_header, text="Excel 列", width=180).pack(side="left", padx=5)
        ctk.CTkLabel(list_header, text="↔").pack(side="left")
        ctk.CTkLabel(list_header, text="网页列", width=180).pack(side="left", padx=5)
        
        # 滚动列表
        self.anchor_list_frame = ctk.CTkScrollableFrame(anchor_frame, height=150)
        self.anchor_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 添加现有的锚定配对
        for pair in self.config.anchor_pairs:
            self._add_anchor_row(pair)
    
    def _add_anchor_row(self, pair: Optional[AnchorPair] = None):
        """添加一行锚定配置"""
        row_frame = ctk.CTkFrame(self.anchor_list_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        
        # 启用复选框
        enabled_var = ctk.BooleanVar(value=pair.enabled if pair else True)
        checkbox = ctk.CTkCheckBox(row_frame, text="", variable=enabled_var, width=50)
        checkbox.pack(side="left")
        
        # Excel 列下拉
        excel_values = ["请选择..."] + self.excel_columns
        excel_combo = ctk.CTkComboBox(row_frame, values=excel_values, width=180)
        if pair:
            excel_combo.set(pair.excel_column)
        else:
            excel_combo.set("请选择...")
        excel_combo.pack(side="left", padx=5)
        
        # 连接符号
        ctk.CTkLabel(row_frame, text="↔", width=30).pack(side="left")
        
        # 网页列下拉（只读列）
        web_values = ["请选择..."] + [c.label for c in self.readonly_columns]
        web_combo = ctk.CTkComboBox(row_frame, values=web_values, width=180)
        if pair:
            web_combo.set(pair.web_column_label)
        else:
            web_combo.set("请选择...")
        web_combo.pack(side="left", padx=5)
        
        # 删除按钮
        delete_btn = ctk.CTkButton(
            row_frame, text="×", width=30, height=28,
            fg_color="red", hover_color="darkred",
            command=lambda: self._delete_anchor_row(row_frame)
        )
        delete_btn.pack(side="left", padx=5)
        
        # 保存引用
        self.anchor_rows.append((enabled_var, excel_combo, web_combo, row_frame))
    
    def _delete_anchor_row(self, row_frame):
        """删除锚定行"""
        for i, row in enumerate(self.anchor_rows):
            if row[3] == row_frame:
                row_frame.destroy()
                del self.anchor_rows[i]
                break
    
    def _create_fill_section(self):
        """创建待填列预览区域"""
        fill_frame = ctk.CTkFrame(self)
        fill_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            fill_frame,
            text="待填列预览",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # 显示待填列
        fill_text = ", ".join(self.config.fill_mappings.keys()) if self.config.fill_mappings else "（无）"
        ctk.CTkLabel(
            fill_frame,
            text=f"📝 {fill_text}",
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=(0, 10))
    
    def _create_buttons(self):
        """创建底部按钮"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame, text="取消", width=100,
            fg_color="gray", hover_color="darkgray",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="确认配置", width=120,
            command=self._on_confirm
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            btn_frame, text="重新自动匹配", width=120,
            fg_color="green", hover_color="darkgreen",
            command=self._auto_match
        ).pack(side="left", padx=5)
    
    def _auto_match(self):
        """重新执行自动匹配"""
        self.config = AnchorMatcher.auto_match(self.excel_columns, self.web_columns)
        
        # 清空现有行
        for row in self.anchor_rows:
            row[3].destroy()
        self.anchor_rows.clear()
        
        # 重新添加
        for pair in self.config.anchor_pairs:
            self._add_anchor_row(pair)
    
    def _on_confirm(self):
        """确认配置"""
        # 收集当前 UI 配置
        new_config = AnchorConfig(auto_matched=False)
        
        for enabled_var, excel_combo, web_combo, _ in self.anchor_rows:
            excel_col = excel_combo.get()
            web_label = web_combo.get()
            
            if excel_col == "请选择..." or web_label == "请选择...":
                continue
            
            # 查找网页列的 xpath
            web_xpath = ""
            for col in self.readonly_columns:
                if col.label == web_label:
                    web_xpath = col.xpath
                    break
            
            new_config.anchor_pairs.append(AnchorPair(
                excel_column=excel_col,
                web_column_xpath=web_xpath,
                web_column_label=web_label,
                enabled=enabled_var.get()
            ))
        
        # 保留待填列映射
        new_config.fill_mappings = self.config.fill_mappings
        
        # 验证
        errors = AnchorMatcher.validate_anchor_config(
            new_config, self.excel_columns, self.web_columns
        )
        
        if errors:
            from tkinter import messagebox
            messagebox.showerror("配置错误", "\n".join(errors), parent=self)
            return
        
        # 回调
        if self.on_confirm:
            self.on_confirm(new_config)
        
        self.destroy()
