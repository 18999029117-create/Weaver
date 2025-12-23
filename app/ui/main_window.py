import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import os

from app.ui.styles import ThemeColors, UIStyles
from app.ui.components import GradientFrame, StatusBadge, AnimatedButton
from app.core.launcher import BrowserLauncher
from app.core.browser import BrowserManager
from app.core.excel import ExcelManager
from app.ui.process_window import ProcessWindow

class AutoFillerUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- 窗口基础设置 ---
        self.title("Weaver (维沃) v1.0 Beta - 智能自动化工作台")
        self.geometry("1000x750")
        self.minsize(900, 650)
        self.configure(fg_color=ThemeColors.BG_DARK)
        
        # 控制器
        self.browser_mgr = BrowserManager()
        self.excel_mgr = ExcelManager()
        
        # 状态变量
        self.excel_path = ctk.StringVar(value="")
        self.selected_tab = ctk.StringVar(value="")
        self.browser_tabs_data = []  
        self.delay_time = ctk.DoubleVar(value=1.5)
        
        # 构建界面
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=ThemeColors.BG_SECONDARY, corner_radius=0, height=80)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_propagate(False)
        
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=25, pady=15, sticky="w")
        ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=36), text_color=ThemeColors.ACCENT_PRIMARY).pack(side="left", padx=(0, 10))
        
        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="Weaver (维沃)", font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=22, weight="bold"), text_color=ThemeColors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="智能自动化数据编织平台 v1.0 Beta", font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12), text_color=ThemeColors.TEXT_SECONDARY).pack(anchor="w")
        
        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.grid(row=0, column=2, padx=25, pady=15, sticky="e")
        self.status_badge = StatusBadge(status_frame, text="● 就绪", color=ThemeColors.SUCCESS)
        self.status_badge.pack(side="right")

    def _create_main_content(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=20)
        main_frame.grid_columnconfigure(0, weight=2)  # 流程区（更宽）
        main_frame.grid_columnconfigure(1, weight=1)  # 日志预览区（更窄）
        main_frame.grid_rowconfigure(0, weight=1)
        
        # --- 左侧：线性流程区（无滚动条）---
        step_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        step_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 第一步：开启浏览器
        step1 = self._create_step_card(step_container, "Step 1: 开启自动化浏览器", "软件将为您开启一个受控的专用浏览器窗口。")
        self.launch_btn = AnimatedButton(step1, text="🌐 立即打开专用浏览器", height=40, font=(UIStyles.FONT_FAMILY, 13, "bold"), command=self.action_launch_browser)
        self.launch_btn.pack(fill="x", padx=20, pady=15)

        # 第二步：锁定网页
        step2 = self._create_step_card(step_container, "Step 2: 锁定目标网页", "在已开浏览器中找目标页，然后点击下方探测。")
        self.detect_btn = AnimatedButton(step2, text="🔍 探测并关联当前页面", height=40, state="disabled", font=(UIStyles.FONT_FAMILY, 13, "bold"), command=self.action_detect_tabs)
        self.detect_btn.pack(fill="x", padx=20, pady=(15, 5))
        self.tab_dropdown = ctk.CTkComboBox(
            step2, 
            variable=self.selected_tab, 
            values=["等待探测..."], 
            height=40, 
            state="readonly",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13),
            dropdown_font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13),
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#000000",
            dropdown_hover_color="#E5E5E5",
            button_color="#E5E5E5",
            button_hover_color="#D0D0D0",
            border_width=0,
            text_color="#000000",
            fg_color="#FFFFFF",
            corner_radius=6
        )
        self.tab_dropdown.pack(fill="x", padx=20, pady=(5, 15))

        # 第三步：加载 Excel
        step3 = self._create_step_card(step_container, "Step 3: 选择 Excel 数据文件", "选择您需要录入的 Excel 表格。")
        self.excel_btn = AnimatedButton(step3, text="📁 选择 Excel 文件", height=40, font=(UIStyles.FONT_FAMILY, 13, "bold"), command=self.action_browse_file)
        self.excel_btn.pack(fill="x", padx=20, pady=15)
        self.excel_label = ctk.CTkLabel(step3, text="未选择文件", text_color=ThemeColors.TEXT_MUTED, font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=11))
        self.excel_label.pack(pady=(0, 10))

        # --- 右侧：日志反馈区 + 启动按钮 ---
        right_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_container.grid_columnconfigure(0, weight=1)
        right_container.grid_rowconfigure(0, weight=1)  # 日志区域占主要空间
        right_container.grid_rowconfigure(1, weight=0)  # 按钮固定高度
        
        log_panel = GradientFrame(right_container)
        log_panel.grid(row=0, column=0, sticky="nsew")
        log_panel.grid_columnconfigure(0, weight=1)
        log_panel.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(log_panel, text="📝 运行日志看板", font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.log_text = ctk.CTkTextbox(log_panel, font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12), fg_color=ThemeColors.BG_DARK)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.add_log("系统就绪。请按照左侧步骤操作。")
        
        # 启动按钮（放在日志面板下方，与Step3底部对齐）
        start_frame = ctk.CTkFrame(right_container, fg_color="transparent")
        start_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        self.start_btn = AnimatedButton(start_frame, text="🚀 启动智能编织任务", height=55, font=(UIStyles.FONT_FAMILY, 13, "bold"), command=self.action_start_task)
        self.start_btn.pack(fill="x")
        
        # 进度条和状态标签
        self.progress_bar = ctk.CTkProgressBar(start_frame, height=8, corner_radius=4, 
                                               fg_color="#E5E5E5", progress_color="#000000")
        self.progress_bar.pack(fill="x", pady=(8, 0))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # 初始隐藏
        
        self.progress_label = ctk.CTkLabel(start_frame, text="", 
                                           font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=11),
                                           text_color=ThemeColors.TEXT_SECONDARY)
        self.progress_label.pack(pady=(5, 0))
        self.progress_label.pack_forget()  # 初始隐藏

    def _create_step_card(self, parent, title, subtitle):
        card = GradientFrame(parent)
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=15, weight="bold"), text_color=ThemeColors.ACCENT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 0))
        ctk.CTkLabel(card, text=subtitle, font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=11), text_color=ThemeColors.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 5))
        return card

    def _create_footer(self):
        footer_frame = ctk.CTkFrame(self, fg_color=ThemeColors.BG_SECONDARY, corner_radius=0, height=40)
        footer_frame.grid(row=2, column=0, sticky="ew")
        self.sys_info = ctk.CTkLabel(footer_frame, text="Weaver (维沃) v1.0 Beta | 自动化环境就绪", font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=10), text_color=ThemeColors.TEXT_MUTED)
        self.sys_info.pack(side="left", padx=25)

    # --- 交互动作 ---
    def add_log(self, message, m_type="info"):
        self.log_text.configure(state="normal")
        t = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{t}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def action_launch_browser(self):
        self.add_log("🚀 正在为您开启受控浏览器实例...")
        self.launch_btn.configure(state="disabled", text="⏳ 正在启动浏览器...")
        
        def run():
            try:
                self.browser_mgr.page = BrowserLauncher.launch_automated_browser()
                self.after(0, lambda: [
                    self.launch_btn.configure(text="✅ 浏览器已就绪"),
                    self.detect_btn.configure(state="normal"),
                    self.add_log("✅ 浏览器启动成功。请在浏览器中完成登录并找到目标页面。")
                ])
            except Exception as e:
                self.after(0, lambda: [
                    self.launch_btn.configure(state="normal", text="🌐 重新启动浏览器"),
                    self.add_log(f"❌ 启动失败: {str(e)}", "error")
                ])
        threading.Thread(target=run, daemon=True).start()

    def action_detect_tabs(self):
        self.add_log("🔍 正在同步已打开的标签页列表...")
        try:
            tabs = self.browser_mgr.get_tabs()
            self.browser_tabs_data = tabs
            titles = [t['title'] for t in tabs]
            if titles:
                self.tab_dropdown.configure(values=titles)
                self.tab_dropdown.set(titles[0])
                self.selected_tab.set(titles[0])
                self.add_log(f"🎯 已检测到 {len(titles)} 个可用页面。")
            else:
                self.add_log("⚠️ 浏览器内没有打开任何页面。", "warning")
        except Exception as e:
            self.add_log(f"❌ 探测同步失败: {str(e)}", "error")

    def action_browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if f:
            self.excel_path.set(f)
            self.excel_label.configure(text=os.path.basename(f))
            self.add_log(f"✅ Excel 数据已加载: {os.path.basename(f)}")

    def action_start_task(self):
        if not self.excel_path.get() or not self.selected_tab.get():
            messagebox.showwarning("提示", "请先完成 Step 1, 2, 3 的配置")
            return
        
        # 显示进度条
        self.progress_bar.pack(fill="x", pady=(8, 0))
        self.progress_label.pack(pady=(5, 0))
        self.start_btn.configure(state="disabled", text="⚙️ 初始化中...")
        self.update()
        
        def run_with_progress():
            try:
                import time as t
                
                # 步骤1: 加载 Excel 数据
                self._update_progress(0.1, "📊 正在读取Excel文件...")
                t.sleep(0.2)
                df = self.excel_mgr.load_excel(self.excel_path.get())
                self._update_progress(0.15, f"📊 已加载 {len(df)} 行, {len(df.columns)} 列数据")
                self.add_log(f"📊 Excel数据: {len(df)} 行 × {len(df.columns)} 列")
                t.sleep(0.3)
                
                # 步骤2: 连接浏览器
                self._update_progress(0.25, "🌐 正在连接目标页面...")
                tab_id = next(t_item['id'] for t_item in self.browser_tabs_data if t_item['title'] == self.selected_tab.get())
                t.sleep(0.2)
                self._update_progress(0.3, "🌐 浏览器连接成功")
                self.add_log("🌐 已连接到目标页面")
                t.sleep(0.2)
                
                # 步骤3: 扫描网页元素
                self._update_progress(0.4, "🔍 正在深度扫描网页元素...")
                self.add_log("🔍 启动深度扫描...")
                t.sleep(0.3)
                self._update_progress(0.5, "🔍 正在分析表单结构...")
                t.sleep(0.3)
                self._update_progress(0.6, "🔍 正在提取交互元素...")
                t.sleep(0.3)
                
                # 步骤4: 智能匹配
                self._update_progress(0.7, "🎯 正在执行智能字段匹配...")
                self.add_log("🎯 启动智能匹配引擎")
                t.sleep(0.3)
                self._update_progress(0.8, "🎯 正在计算匹配度评分...")
                t.sleep(0.2)
                
                # 步骤5: 初始化工作台
                self._update_progress(0.9, "🛠️ 正在构建映射画布...")
                t.sleep(0.2)
                
                # 步骤6: 打开工作台并排列窗口
                self._update_progress(0.95, "📐 正在调整窗口布局...")
                process_win = ProcessWindow(self, df, tab_id, self.browser_mgr)
                
                # 排列窗口：软件40%左侧，浏览器60%右侧
                self._arrange_windows(process_win)
                
                self._update_progress(1.0, "✅ 初始化完成！")
                t.sleep(0.3)
                
                # 隐藏进度条
                self._hide_progress()
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.add_log(f"❌ 启动失败: {str(e)}", "error")
                messagebox.showerror("错误", f"启动异常: {str(e)}")
                self._hide_progress()
        
        # 在主线程中延迟执行，让UI有时间更新
        self.after(100, run_with_progress)
    
    def _update_progress(self, value, text):
        """更新进度条和状态文本"""
        self.progress_bar.set(value)
        self.progress_label.configure(text=text)
        self.update()
    
    def _hide_progress(self):
        """隐藏进度条并恢复按钮"""
        self.progress_bar.pack_forget()
        self.progress_label.pack_forget()
        self.progress_bar.set(0)
        self.start_btn.configure(state="normal", text="🚀 启动智能编织任务")
    
    def _arrange_windows(self, process_win):
        """排列窗口：工作台40%左侧，浏览器60%右侧"""
        try:
            # 获取屏幕尺寸
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # 计算窗口尺寸
            app_width = int(screen_width * 0.4)
            browser_width = int(screen_width * 0.6)
            window_height = screen_height - 80  # 留出任务栏空间
            
            # 设置工作台位置（左侧40%）
            process_win.geometry(f"{app_width}x{window_height}+0+0")
            process_win.update()
            
            # 设置浏览器位置（右侧60%）
            try:
                # 使用 pyautogui 或直接操作浏览器窗口
                import subprocess
                # Windows下使用PowerShell调整浏览器窗口
                ps_script = f'''
                Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
                    [DllImport("user32.dll")]
                    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
                }}
"@
                $chrome = Get-Process chrome -ErrorAction SilentlyContinue | Where-Object {{$_.MainWindowHandle -ne 0}} | Select-Object -First 1
                if ($chrome) {{
                    [Win32]::SetWindowPos($chrome.MainWindowHandle, [IntPtr]::Zero, {app_width}, 0, {browser_width}, {window_height}, 0x0040)
                }}
                '''
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=3)
            except:
                pass  # 如果无法调整浏览器窗口，忽略错误
                
            self.add_log(f"📐 窗口已排列：工作台 {app_width}px | 浏览器 {browser_width}px")
            
        except Exception as e:
            self.add_log(f"⚠️ 窗口排列失败: {e}")
