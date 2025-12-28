"""
版本选择对话框

启动时显示，让用户选择使用的版本。
"""

import customtkinter as ctk
from typing import Optional, Callable

from app.ui.styles import ThemeColors, UIStyles
from app.ui.components import AnimatedButton
from app.editions.registry import EDITIONS


class EditionSelectorDialog(ctk.CTkToplevel):
    """
    版本选择对话框
    
    启动时显示，让用户选择通用版本或定制版本。
    """
    
    def __init__(
        self, 
        master,
        on_select: Optional[Callable[[str], None]] = None
    ):
        """
        初始化对话框
        
        Args:
            master: 父窗口
            on_select: 选择回调 (edition_id)
        """
        super().__init__(master)
        
        self.on_select = on_select
        self.selected_edition: Optional[str] = None
        
        # 窗口设置
        self.title("Weaver (维沃) - 选择版本")
        self.geometry("500x400")
        self.configure(fg_color=ThemeColors.BG_DARK)
        self.resizable(False, False)
        
        # 模态
        self.transient(master)
        self.grab_set()
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 400) // 2
        self.geometry(f"500x400+{x}+{y}")
        
        # 阻止关闭（必须选择）
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._build_ui()
    
    def _build_ui(self):
        """构建 UI"""
        # 标题区
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="⚡ Weaver (维沃)",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=24, weight="bold"),
            text_color=ThemeColors.ACCENT_PRIMARY
        ).pack(anchor="center")
        
        ctk.CTkLabel(
            title_frame,
            text="请选择您要使用的版本",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="center", pady=(10, 0))
        
        # 版本列表区
        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        for edition_id, info in EDITIONS.items():
            self._create_edition_card(list_frame, edition_id, info)
    
    def _create_edition_card(self, parent, edition_id: str, info: dict):
        """创建版本卡片"""
        card = ctk.CTkFrame(
            parent,
            fg_color=ThemeColors.BG_SECONDARY,
            corner_radius=10,
            border_width=2,
            border_color=ThemeColors.BORDER
        )
        card.pack(fill="x", pady=8)
        
        # 内容区
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)
        content.grid_columnconfigure(1, weight=1)
        
        # 图标
        icon_label = ctk.CTkLabel(
            content,
            text=info["icon"],
            font=ctk.CTkFont(size=32)
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 15))
        
        # 名称
        name_label = ctk.CTkLabel(
            content,
            text=info["name"],
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=16, weight="bold"),
            text_color=ThemeColors.TEXT_PRIMARY,
            anchor="w"
        )
        name_label.grid(row=0, column=1, sticky="w")
        
        # 描述
        desc_label = ctk.CTkLabel(
            content,
            text=info["description"],
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12),
            text_color=ThemeColors.TEXT_SECONDARY,
            anchor="w"
        )
        desc_label.grid(row=1, column=1, sticky="w")
        
        # 选择按钮
        btn = ctk.CTkButton(
            content,
            text="选择",
            width=70,
            height=32,
            fg_color=ThemeColors.ACCENT_PRIMARY,
            hover_color=ThemeColors.ACCENT_SECONDARY,
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12),
            command=lambda eid=edition_id: self._on_select(eid)
        )
        btn.grid(row=0, column=2, rowspan=2, padx=(15, 0))
        
        # 悬停效果
        def on_enter(e):
            card.configure(border_color=ThemeColors.ACCENT_PRIMARY)
        
        def on_leave(e):
            card.configure(border_color=ThemeColors.BORDER)
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
    
    def _on_select(self, edition_id: str):
        """选择版本"""
        self.selected_edition = edition_id
        print(f"[EditionSelector] 选择版本: {edition_id}")
        
        if self.on_select:
            self.on_select(edition_id)
        
        self.destroy()
    
    def _on_close(self):
        """关闭窗口时默认选择通用版本"""
        self._on_select("generic")


def show_edition_selector(master) -> str:
    """
    显示版本选择对话框并返回选择结果
    
    Args:
        master: 父窗口
        
    Returns:
        选择的版本 ID
    """
    selected = [None]
    
    def on_select(edition_id):
        selected[0] = edition_id
    
    dialog = EditionSelectorDialog(master, on_select=on_select)
    dialog.wait_window()
    
    return selected[0] or "generic"
