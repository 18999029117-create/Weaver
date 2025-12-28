"""
库车市人民医院 - 简化启动对话框

深度定制版：直接执行自动化，支持断点调试。
v2.1: 添加暂停/终止按钮、断点确认功能
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Any, Callable, Optional, Dict
import threading
import time
from datetime import datetime

from app.ui.styles import ThemeColors, UIStyles
from app.ui.components import AnimatedButton


class KucheStartDialog(ctk.CTkToplevel):
    """
    库车医院专属启动对话框
    
    深度定制版：显示数据统计，一键启动自动化，支持断点调试
    """
    
    def __init__(
        self, 
        master,
        excel_data: Any,
        browser_tab: Any,
        edition: Any,
        on_complete: Optional[Callable] = None
    ):
        super().__init__(master)
        
        self.excel_data = excel_data
        self.browser_tab = browser_tab
        self.edition = edition
        self.on_complete = on_complete
        self.master_app = master
        
        # 处理器引用（用于暂停/终止）
        self._processor = None
        self._is_running = False
        self._debug_mode = True  # 默认开启断点调试
        
        # 断点确认状态
        self._confirm_event = threading.Event()
        self._confirm_result = False
        
        # 窗口设置
        self.title("🏥 库车市人民医院 - 耗材采购自动化")
        self.geometry("550x650")
        self.configure(fg_color=ThemeColors.BG_DARK)
        self.resizable(False, False)
        
        # 居中显示
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 550) // 2
        y = (self.winfo_screenheight() - 650) // 2
        self.geometry(f"550x650+{x}+{y}")
        
        self._build_ui()
        self._analyze_data()
        
        # 确保窗口关闭时停止处理
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _build_ui(self):
        """构建 UI"""
        # 标题区
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="🏥 耗材采购自动化",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=22, weight="bold"),
            text_color=ThemeColors.ACCENT_PRIMARY
        ).pack(anchor="center")
        
        ctk.CTkLabel(
            title_frame,
            text="库车市人民医院专属功能（调试模式）",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="center", pady=(5, 0))
        
        # 数据统计区
        stats_frame = ctk.CTkFrame(self, fg_color=ThemeColors.BG_SECONDARY, corner_radius=10)
        stats_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            stats_frame,
            text="📊 数据统计",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=14, weight="bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="正在分析...",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=11),
            text_color=ThemeColors.TEXT_SECONDARY,
            justify="left"
        )
        self.stats_label.pack(anchor="w", padx=20, pady=(0, 10))
        
        # 调试开关
        debug_frame = ctk.CTkFrame(self, fg_color="transparent")
        debug_frame.pack(fill="x", padx=30, pady=5)
        
        self.debug_switch = ctk.CTkSwitch(
            debug_frame,
            text="🔍 断点调试模式（每步确认）",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=12),
            command=self._toggle_debug,
            onvalue=True,
            offvalue=False
        )
        self.debug_switch.pack(anchor="w")
        self.debug_switch.select()  # 默认开启
        
        # 日志区
        log_frame = ctk.CTkFrame(self, fg_color=ThemeColors.BG_SECONDARY, corner_radius=10)
        log_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        ctk.CTkLabel(
            log_frame,
            text="📝 运行日志",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13, weight="bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=11),
            fg_color=ThemeColors.BG_DARK,
            height=150
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # 断点确认区（初始隐藏）
        self.confirm_frame = ctk.CTkFrame(self, fg_color=ThemeColors.BG_SECONDARY, corner_radius=10)
        # 不 pack，需要时再显示
        
        self.confirm_label = ctk.CTkLabel(
            self.confirm_frame,
            text="",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=13),
            text_color=ThemeColors.TEXT_PRIMARY
        )
        self.confirm_label.pack(pady=(15, 10))
        
        confirm_btn_frame = ctk.CTkFrame(self.confirm_frame, fg_color="transparent")
        confirm_btn_frame.pack(pady=(0, 15))
        
        self.confirm_yes_btn = ctk.CTkButton(
            confirm_btn_frame,
            text="✅ 正确，继续",
            width=120,
            fg_color="#28a745",
            hover_color="#218838",
            command=lambda: self._on_confirm(True)
        )
        self.confirm_yes_btn.pack(side="left", padx=5)
        
        self.confirm_no_btn = ctk.CTkButton(
            confirm_btn_frame,
            text="❌ 错误，终止",
            width=120,
            fg_color="#dc3545",
            hover_color="#c82333",
            command=lambda: self._on_confirm(False)
        )
        self.confirm_no_btn.pack(side="left", padx=5)
        
        # 控制按钮区
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(5, 10))
        
        # 启动按钮
        self.start_btn = AnimatedButton(
            btn_frame,
            text="🚀 开始录入",
            height=45,
            font=(UIStyles.FONT_FAMILY, 14, "bold"),
            command=self._start_process
        )
        self.start_btn.pack(fill="x", pady=(0, 8))
        
        # 暂停/终止按钮行
        control_row = ctk.CTkFrame(btn_frame, fg_color="transparent")
        control_row.pack(fill="x")
        
        self.pause_btn = ctk.CTkButton(
            control_row,
            text="⏸️ 暂停",
            width=90,  # 减小宽度
            height=35,
            fg_color=ThemeColors.BG_SECONDARY,
            hover_color="#4a4a4a",
            state="disabled",
            command=self._toggle_pause
        )
        self.pause_btn.pack(side="left", expand=True, padx=2)
        
        self.stop_btn = ctk.CTkButton(
            control_row,
            text="⏹️ 终止",
            width=90,  # 减小宽度
            height=35,
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled",
            command=self._stop_process
        )
        self.stop_btn.pack(side="left", expand=True, padx=2)
        
        self.export_btn = ctk.CTkButton(
            control_row,
            text="📊 导出",  # 缩短文字
            width=90,  # 减小宽度
            height=35,
            fg_color="#17a2b8",
            hover_color="#138496",
            state="disabled",
            command=self._export_report
        )
        self.export_btn.pack(side="left", expand=True, padx=2)
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            btn_frame,
            text="",
            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY, size=11),
            text_color=ThemeColors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=(8, 0))
    
    def _toggle_debug(self):
        """切换调试模式"""
        self._debug_mode = self.debug_switch.get()
        if self._debug_mode:
            self._log("🔍 断点调试已开启")
        else:
            self._log("⚡ 断点调试已关闭，将自动执行")
    
    def _analyze_data(self):
        """分析数据并显示统计"""
        try:
            code_column = '医保码'
            
            if code_column not in self.excel_data.columns:
                possible_names = ['医保码', 'C码', '耗材代码', '产品代码']
                found = None
                for name in possible_names:
                    if name in self.excel_data.columns:
                        found = name
                        break
                
                if not found:
                    self.stats_label.configure(
                        text=f"⚠️ 找不到医保码列\n可用列：{', '.join(list(self.excel_data.columns)[:5])}..."
                    )
                    self._log("⚠️ 未找到医保码列，请检查Excel表格")
                    self.start_btn.configure(state="disabled")
                    return
                
                code_column = found
            
            total_rows = len(self.excel_data)
            codes = self.excel_data[code_column].dropna().astype(str)
            unique_codes = codes.nunique()
            code_counts = codes.value_counts()
            
            preview = ""
            for code, count in list(code_counts.items())[:5]:
                preview += f"  • {code}: {count} 个\n"
            if len(code_counts) > 5:
                preview += f"  ... 共 {len(code_counts)} 种耗材"
            
            stats_text = f"总行数：{total_rows} 行  |  唯一耗材：{unique_codes} 种\n\n{preview}"
            
            self.stats_label.configure(text=stats_text)
            self._log(f"✅ 数据分析完成，共 {unique_codes} 种耗材待采购")
            
        except Exception as e:
            self.stats_label.configure(text=f"❌ 分析失败: {e}")
            self._log(f"❌ 数据分析失败: {e}")
    
    def _start_process(self):
        """开始处理"""
        self._is_running = True
        self.start_btn.configure(state="disabled", text="⏳ 处理中...")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.debug_switch.configure(state="disabled")
        self.status_label.configure(text="正在执行自动化流程...")
        
        def run():
            try:
                from app.customizations.kuche_hospital.consumable_processor import ConsumableProcessor
                
                self._processor = ConsumableProcessor(
                    browser_tab=self.browser_tab,
                    progress_callback=self._safe_log,
                    confirm_callback=self._wait_for_confirm if self._debug_mode else None,
                    debug_mode=self._debug_mode
                )
                
                result = self._processor.process(self.excel_data, code_column='医保码')
                
                self.after(0, lambda: self._on_complete(result))
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.after(0, lambda err=str(e): self._on_error(err))
        
        threading.Thread(target=run, daemon=True).start()
    
    def _wait_for_confirm(self, step_name: str) -> bool:
        """
        显示断点确认对话框，等待用户响应
        
        Args:
            step_name: 当前步骤名称
            
        Returns:
            True = 继续, False = 终止
        """
        self._confirm_event.clear()
        
        # 在主线程显示确认框
        def show_confirm():
            self.confirm_label.configure(text=f"🔵 {step_name}")
            self.confirm_frame.pack(fill="x", padx=30, pady=5, before=self.start_btn.master)
        
        self.after(0, show_confirm)
        
        # 等待用户响应
        self._confirm_event.wait()
        
        # 隐藏确认框
        def hide_confirm():
            self.confirm_frame.pack_forget()
        
        self.after(0, hide_confirm)
        
        return self._confirm_result
    
    def _on_confirm(self, result: bool):
        """用户确认响应"""
        self._confirm_result = result
        self._confirm_event.set()
    
    def _toggle_pause(self):
        """切换暂停状态"""
        if not self._processor:
            return
        
        if self._processor._pause_requested:
            self._processor.resume()
            self.pause_btn.configure(text="⏸️ 暂停")
            self._log("▶️ 已恢复执行")
        else:
            self._processor.pause()
            self.pause_btn.configure(text="▶️ 继续")
            self._log("⏸️ 已暂停")
    
    def _stop_process(self):
        """终止处理"""
        if self._processor:
            self._processor.stop()
            self._log("⏹️ 正在终止...")
        
        # 如果在等待确认，直接设为终止
        self._confirm_result = False
        self._confirm_event.set()
    
    def _export_report(self):
        """导出报告到用户选择的位置"""
        if not self._processor or not self._processor.has_report_data():
            messagebox.showwarning("提示", "无数据可导出，请先运行处理流程")
            return
        
        # 默认文件名
        default_name = f"采购处理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 弹出文件保存对话框
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=default_name,
            title="保存采购处理报告"
        )
        
        if filepath:
            success = self._processor.export_report(filepath)
            if success:
                messagebox.showinfo("成功", f"报告已保存到:\n{filepath}")
            else:
                messagebox.showerror("失败", "导出报告失败，请查看日志")
    
    def _on_complete(self, result):
        """处理完成"""
        self._is_running = False
        
        def ui_update():
            # 安全检查：确保所有涉及的组件都还存在
            if not self.winfo_exists(): return
            
            if hasattr(self, 'confirm_frame') and self.confirm_frame.winfo_exists():
                self.confirm_frame.pack_forget()
                
            if result.get('stopped'):
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    self.status_label.configure(
                        text=f"⏹️ 已终止：处理了 {result.get('processed', 0)}/{result.get('total_codes', 0)} 个耗材",
                        text_color=ThemeColors.WARNING
                    )
            elif result.get('success'):
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    self.status_label.configure(
                        text=f"✅ 完成！处理 {result.get('processed', 0)}/{result.get('total_codes', 0)} 个耗材",
                        text_color=ThemeColors.SUCCESS
                    )
                self._log(f"🎉 处理完成：成功 {result.get('processed', 0)} 个")
            else:
                if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                    self.status_label.configure(
                        text=f"⚠️ {result.get('error', '未知错误')}",
                        text_color=ThemeColors.WARNING
                    )
            self._reset_buttons()
            
        self._ui_safe(ui_update)
    
    def _on_error(self, error):
        """处理错误"""
        self._is_running = False
        
        def ui_update():
            if not self.winfo_exists(): return
            if hasattr(self, 'confirm_frame') and self.confirm_frame.winfo_exists():
                self.confirm_frame.pack_forget()
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.configure(text=f"❌ 错误: {error}", text_color=ThemeColors.ERROR)
            self._log(f"❌ 错误: {error}")
            self._reset_buttons()
            
        self._ui_safe(ui_update)
    
    def _reset_buttons(self):
        """重置按钮状态"""
        def ui_update():
            if not self.winfo_exists(): return
            widgets = ['start_btn', 'pause_btn', 'stop_btn', 'debug_switch', 'export_btn']
            for w in widgets:
                if hasattr(self, w):
                    widget = getattr(self, w)
                    if widget.winfo_exists():
                        if w == 'start_btn': widget.configure(state="normal", text="🔄 重新开始")
                        elif w == 'pause_btn': widget.configure(state="disabled", text="⏸️ 暂停")
                        elif w == 'stop_btn': widget.configure(state="disabled")
                        elif w == 'debug_switch': widget.configure(state="normal")
                        elif w == 'export_btn':
                            # 如果有报告数据，启用导出按钮
                            if self._processor and self._processor.has_report_data():
                                widget.configure(state="normal")
        self._ui_safe(ui_update)
    
    def _safe_log(self, message: str):
        """安全的日志更新"""
        self._ui_safe(lambda m=message: self._log(m))
    
    def _ui_safe(self, func, *args):
        """通用的 UI 安全调用封装，防止窗口关闭后的 TclError"""
        try:
            if self.winfo_exists():
                self.after(0, lambda: self._run_if_exists(func, *args))
        except:
            pass

    def _run_if_exists(self, func, *args):
        """实际执行 UI 更新前的最后检查"""
        try:
            if self.winfo_exists():
                func(*args)
        except:
            pass

    def _log(self, message: str):
        """添加日志"""
        try:
            if not self.winfo_exists() or not hasattr(self, 'log_text'):
                return
            if not self.log_text.winfo_exists():
                return
                
            t = time.strftime("%H:%M:%S")
            self.log_text.configure(state="normal")
            self.log_text.insert("end", f"[{t}] {message}\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except:
            pass
    
    def _on_closing(self):
        """窗口关闭处理"""
        if self._is_running and self._processor:
            self._processor.stop()
            self._confirm_result = False
            self._confirm_event.set()
        self.destroy()
