import sys
import os

# 确保 app 目录在 Python 路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ui.styles import UIStyles
from app.ui.main_window import AutoFillerUI

def main():
    """程序入口"""
    UIStyles.apply_global_styles()
    app = AutoFillerUI()
    app.mainloop()

if __name__ == "__main__":
    main()
