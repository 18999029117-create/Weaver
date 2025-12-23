import customtkinter as ctk

class ThemeColors:
    """系统配色系统 (Apple Monochrome - 极简黑白灰)"""
    # 背景色
    BG_DARK = "#FFFFFF"           # 纯白背景
    BG_SECONDARY = "#F5F5F7"      # 苹果浅灰背景
    BG_CARD = "#FFFFFF"           # 卡片背景
    BG_HOVER = "#E5E5E5"          # 悬停浅灰
    
    # 强调色 - 纯粹的黑
    ACCENT_PRIMARY = "#000000"    # 有力度的纯黑
    ACCENT_SECONDARY = "#333333"  # 也是黑（深灰）
    
    # 功能色 - 放弃彩色，用灰度区分
    SUCCESS = "#000000"           # 成功也是黑
    WARNING = "#555555"           # 警告是深灰
    ERROR = "#000000"             # 错误是黑
    INFO = "#888888"              # 信息是中灰
    
    # 文本色
    TEXT_PRIMARY = "#000000"      # 标题纯黑
    TEXT_SECONDARY = "#6E6E73"    # 副标题（Apple 灰）
    TEXT_MUTED = "#86868B"        # 辅助文字
    
    # 边框
    BORDER = "#000000"            # 极致的黑色细线
    BORDER_FOCUS = "#000000"      # 聚焦也是黑

class UIStyles:
    """UI 样式配置"""
    FONT_FAMILY = "Microsoft YaHei UI"

    @staticmethod
    def apply_global_styles():
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
