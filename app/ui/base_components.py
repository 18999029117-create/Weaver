import customtkinter as ctk
from app.ui.styles import ThemeColors, UIStyles

class GradientFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, 
                        fg_color=ThemeColors.BG_CARD,
                        border_width=1,
                        border_color=ThemeColors.BORDER,
                        corner_radius=12,
                        **kwargs)

class StatusBadge(ctk.CTkFrame):
    def __init__(self, master, text="就绪", color=ThemeColors.SUCCESS, **kwargs):
        super().__init__(master, fg_color=color, corner_radius=8, **kwargs)
        self.label = ctk.CTkLabel(self, text=text, 
                                  font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=11, weight="bold"),
                                  text_color="white")
        self.label.pack(padx=10, pady=3)
    
    def set_status(self, text, color):
        self.configure(fg_color=color)
        self.label.configure(text=text)

class AnimatedButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        # 极简 Apple 风格：白底黑字黑框，悬停浅灰
        defaults = {
            "fg_color": "#FFFFFF",
            "text_color": "#000000",
            "border_width": 1,
            "border_color": "#000000",
            "hover_color": "#E5E5E5", # 悬停变浅灰
            "text_color_disabled": "#BCBCBC",
            "corner_radius": 6,
            "font": (UIStyles.FONT_FAMILY, 13)
        }
        for k, v in defaults.items():
            if k not in kwargs:
                kwargs[k] = v
                
        super().__init__(master, **kwargs)
