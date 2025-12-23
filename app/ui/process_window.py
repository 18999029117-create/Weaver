# ProcessWindow - 智能版（集成智能匹配）
import customtkinter as ctk
from tkinter import ttk, VERTICAL, HORIZONTAL
import threading
import time

from app.ui.styles import ThemeColors, UIStyles
from app.ui.components import AnimatedButton
from app.ui.components.toolbar import ProcessToolbar
from app.ui.dialogs import ColumnComputerDialog
from app.core.smart_form_analyzer import SmartFormAnalyzer
from app.core.smart_form_filler import SmartFormFiller
from app.core.smart_matcher import SmartMatcher
from app.ui.mapping_canvas import MappingCanvas
from app.core.pagination_controller import PaginationController
from app.core.fill_progress_manager import FillProgressManager
from app.application.orchestrator.fill_session_controller import FillSessionController

class ProcessWindow(ctk.CTkToplevel):
    def __init__(self, master, excel_data, browser_tab_id, browser_mgr):
        super().__init__(master)
        
        self.title("Weaver (维沃) v1.0 Beta - 智能填表工作台")
        self.configure(fg_color=ThemeColors.BG_DARK)
        self.attributes("-topmost", True)
        
        self.excel_data = excel_data
        self.browser_tab_id = browser_tab_id
        self.browser_mgr = browser_mgr
        self.stop_event = threading.Event()
        self.abort_event = threading.Event()  # 紧急停止事件
        
        # 智能系统（保留向后兼容）
        self.web_fingerprints = []  # 所有网页元素
        self.matched_fingerprints = []  # 智能匹配后的元素（只显示这些）
        self.field_mapping = {}
        self.auto_mappings = {}  # 自动建议的映射
        
        # 翻页控制
        self.pagination_controller = None
        self.progress_manager = FillProgressManager()
        self.pagination_elements = []  # 检测到的翻页按钮
        self.selected_pagination_btn = None  # 用户选择的翻页按钮
        self.pagination_mode = "manual"  # manual/auto
        
        # === 初始化业务控制器 ===
        tab = self._get_target_tab()
        self.session_controller = FillSessionController(
            browser_tab=tab,
            excel_data=excel_data,
            log_callback=lambda msg, level="info": self.master.add_log(msg, level),
            progress_callback=self._update_progress_display
        )
        
        self._set_perfect_split()
        self._scan_and_match()  # 扫描并智能匹配
        self._setup_layout()
        
        threading.Thread(target=self._lock_browser_layout, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _get_target_tab(self):
        """获取目标标签页对象"""
        try:
            if self.browser_tab_id:
                return self.browser_mgr.page.get_tab(self.browser_tab_id)
        except: pass
        return self.browser_mgr.page

    def _scan_and_match(self):
        """扫描网页并执行智能匹配 - 委托给 controller"""
        # 1. 使用 controller 扫描网页
        self.web_fingerprints = self.session_controller.scan_page()
        
        # 1.5 检测翻页按钮
        self.pagination_elements = self.session_controller.detect_pagination()
        
        # 2. 使用 controller 执行智能匹配
        if self.web_fingerprints:
            self.auto_mappings = self.session_controller.match_fields()
            
            # 同步 controller 的匹配结果到 UI 状态
            self.matched_fingerprints = self.session_controller.matched_fingerprints
            
            # === 自动同步高置信度匹配到 field_mapping ===
            if self.auto_mappings:
                self.field_mapping.update(self.auto_mappings)
                self.master.add_log(f"   已自动应用 {len(self.auto_mappings)} 个映射", "success")

    def highlight_element(self, fingerprint):
        """在浏览器中高亮显示元素 - 委托给 controller"""
        self.session_controller.highlight_element(fingerprint)

    def _set_perfect_split(self):
        """精准分屏：软件 25% | 浏览器 75%"""
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            
            app_w = int(sw * 0.25)
            app_h = sh - 50
            self.geometry(f"{app_w}x{app_h}+0+0")
            self.update_idletasks()

            browser_w = sw - app_w
            browser_x = app_w
            
            browser_w = sw - app_w
            browser_x = app_w
            
            tab = self._get_target_tab()
            tab.set.window.normal()
            tab.set.activate()
            self._flash_target_page(tab)
            
            tab.set.window.location(browser_x, 0)
            tab.set.window.size(browser_w, sh)
            
            self.master.add_log(f"🎯 目标页已锁定")
        except Exception as e:
            print(f"Split Error: {e}")
    
    def _update_pagination_ui(self):
        """更新翻页按钮 UI（使用 controller 的检测结果）"""
        if self.pagination_elements:
            self.master.add_log(f"检测到 {len(self.pagination_elements)} 个翻页按钮")
            for p in self.pagination_elements:
                self.master.add_log(f"  - {p['text']}")
            
            # 更新下拉框选项（如果存在）
            if hasattr(self, 'pagination_selector'):
                new_options = ["未指定"] + [p['text'] for p in self.pagination_elements]
                self.pagination_selector.configure(values=new_options)
        else:
            self.master.add_log("未检测到翻页按钮，您可手动指定")

    def _flash_target_page(self, tab):
        """网页闪烁效果 - 简化版"""
        try:
            tab.run_js("document.body.style.backgroundColor='#E5E5E5';setTimeout(()=>document.body.style.backgroundColor='',500);")
        except: pass

    def _lock_browser_layout(self):
        """后台监控浏览器位置（已弃用）"""
        pass

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 主容器
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # === 工具栏组件 ===
        callbacks = {
            'on_load': self._load_configuration,
            'on_save': self._save_configuration,
            'on_rescan': self._rescan_form,
            'on_apply_mappings': self._apply_auto_mappings,
            'on_clear': self._clear_all_mappings,
            'on_start': self._on_start_click,
            'on_stop': self._on_stop_click,
            'on_continue': self._on_continue_fill,
            'on_pagination_select': self._on_pagination_select,
            'on_pagination_mode_change': self._on_pagination_mode_change,
        }
        
        self.toolbar = ProcessToolbar(
            main_container,
            excel_columns=self.excel_data.columns.tolist(),
            callbacks=callbacks,
            pagination_elements=getattr(self, 'pagination_elements', [])
        )
        self.toolbar.pack(fill="x", side="top", padx=5, pady=1)
        
        # 将工具栏的 UI 控件引用映射到主窗口，以保持其他代码兼容
        self.load_btn = self.toolbar.load_btn
        self.save_btn = self.toolbar.save_btn
        self.refresh_btn = self.toolbar.refresh_btn
        self.auto_map_btn = self.toolbar.auto_map_btn
        self.clear_mapping_btn = self.toolbar.clear_mapping_btn
        self.anchor_var = self.toolbar.anchor_var
        self.anchor_selector = self.toolbar.anchor_selector
        self.mode_var = self.toolbar.mode_var
        self.mode_selector = self.toolbar.mode_selector
        self.start_btn = self.toolbar.start_btn
        self.stop_btn = self.toolbar.stop_btn
        self.pagination_var = self.toolbar.pagination_var
        self.pagination_selector = self.toolbar.pagination_selector
        self.pagination_status = self.toolbar.pagination_status
        self.pagination_mode_var = self.toolbar.pagination_mode_var
        self.pagination_mode_selector = self.toolbar.pagination_mode_selector
        self.continue_btn = self.toolbar.continue_btn
        self.progress_label = self.toolbar.progress_label

        # === 智能映射画布 ===
        canvas_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        canvas_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self._build_mapping_panel(canvas_frame)

    def _build_excel_table(self, parent):
        """构建 Excel 表格区域"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(parent, text="📊 Excel 数据源", 
                            font=ctk.CTkFont(family=UIStyles.FONT_FAMILY,size=13, weight="bold"),
                            text_color=ThemeColors.ACCENT_PRIMARY)
        header.grid(row=0, column=0, pady=8, sticky="w", padx=10)

        table_frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", border_width=1, border_color=ThemeColors.BORDER)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                       background="#FFFFFF", 
                       foreground="#000000",
                       fieldbackground="#FFFFFF",
                       borderwidth=0,
                       font=(UIStyles.FONT_FAMILY, 10))
        style.configure("Treeview.Heading", 
                       background=ThemeColors.ACCENT_PRIMARY, 
                       foreground="white",
                       relief="flat")
        style.map("Treeview", background=[('selected', '#F5F5F7')], foreground=[('selected', '#000000')])

        self.tree = ttk.Treeview(table_frame, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        cols = self.excel_data.columns.tolist()
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, minwidth=80)
        
        for _, row in self.excel_data.iterrows():
            self.tree.insert("", "end", values=row.tolist())

    def _build_mapping_panel(self, parent):
        """构建智能映射画布（只显示匹配的元素）"""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # 创建智能映射画布（传入过滤后的元素列表）
        self.mapping_canvas = MappingCanvas(
            parent,
            excel_columns=self.excel_data.columns.tolist(),
            web_fingerprints=self.matched_fingerprints,  # ← 只显示匹配的
            on_mapping_complete=self._on_canvas_mapping_complete,
            on_element_click=self.highlight_element,  # ← 传入点击回调
            on_add_computed_column=self._open_column_computer # ← 传入添加列回调
        )
        self.mapping_canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def _on_canvas_mapping_complete(self, mappings):
        """Canvas映射完成回调"""
        self.field_mapping = mappings
        avg_score = sum(fp.stability_score for fp in mappings.values()) / len(mappings) if mappings else 0
        self.master.add_log(f"✅ 已建立 {len(mappings)} 个映射（平均稳定性:{avg_score:.0f}分）", "success")
        if self.auto_mappings:
            self.master.add_log(f"✅ 自动建议 {len(self.auto_mappings)} 个高质量映射", "success")
            self.master.add_log(f"   您可以在画布中点击确认", "success")

    def _apply_auto_mappings(self):
        """应用自动映射建议"""
        if not self.auto_mappings:
            self.master.add_log("⚠️ 没有自动映射建议", "warning")
            return
        
        # 将自动映射应用到field_mapping
        self.field_mapping.update(self.auto_mappings)
        
        # 通知画布绘制连线
        self.mapping_canvas.draw_mappings(self.auto_mappings)
        
        self.master.add_log(f"✅ 已应用 {len(self.auto_mappings)} 个自动映射", "success")
    
    def _rescan_form(self):
        """重新扫描网页表单"""
        self.master.add_log("🔄 重新深度扫描...")
        self._scan_and_match()
        
        # 重新创建映射画布
        mapping_container_parent = self.mapping_canvas.master
        self.mapping_canvas.destroy()
        
        self.mapping_canvas = MappingCanvas(
            mapping_container_parent,
            excel_columns=self.excel_data.columns.tolist(),
            web_fingerprints=self.matched_fingerprints,
            on_mapping_complete=self._on_canvas_mapping_complete,
            on_element_click=self.highlight_element,
            on_add_computed_column=self._open_column_computer
        )
        self.mapping_canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def _clear_all_mappings(self):
        """清空所有映射"""
        self.field_mapping.clear()
        self.mapping_canvas.clear_all_mappings()
        self.master.add_log("🗑️ 已清空所有映射")

    def _on_pagination_select(self, value):
        """选择翻页按钮"""
        if value == "❌未指定":
            self.selected_pagination_btn = None
            self.pagination_status.configure(text="")
            self.pagination_selector.configure(fg_color="#FFFFFF")
        else:
            # 找到对应的翻页元素
            for p in self.pagination_elements:
                if p['text'] == value:
                    self.selected_pagination_btn = p
                    break
            
            self.pagination_status.configure(text="已指定")
            self.pagination_selector.configure(fg_color="#D0D0D0")
            self.master.add_log(f"已指定翻页按钮: {value}")
    
    def _on_pagination_mode_change(self, value):
        """切换翻页模式"""
        if "全自动" in value:
            self.pagination_mode = "auto"
            self.continue_btn.configure(state="disabled")
            self.master.add_log("翻页模式: 全自动（自动翻页并继续填充）")
        else:
            self.pagination_mode = "manual"
            self.master.add_log("翻页模式: 手动（请手动翻页后点击'继续录入'）")
    
    def _on_continue_fill(self):
        """手动模式下继续录入"""
        if not self.field_mapping:
            self.master.add_log("请先建立字段映射", "warning")
            return
        
        self.master.add_log("继续录入...")
        self.continue_btn.configure(state="disabled")
        
        # 检查是否是锚点模式
        anchor_text = self.anchor_selector.get()
        key_column = None
        if anchor_text and anchor_text != "按顺序录入":
            key_column = anchor_text
        
        if key_column:
            # 锚点模式：需要重新扫描当前页的锚点值
            threading.Thread(target=self._execute_anchor_page_fill, args=(key_column,), daemon=True).start()
        else:
            # 普通模式继续
            self._scan_web_form()
            threading.Thread(target=self._execute_fill_continue, daemon=True).start()
    
    def _execute_anchor_page_fill(self, key_column):
        """锚点模式翻页后重新扫描并填充当前页 - 委托给 controller"""
        try:
            # 同步配置到 controller
            self.session_controller.set_config(
                fill_mode="batch_table" if "批量" in self.mode_selector.get() else "single_form",
                key_column=key_column,
                pagination_mode=self.pagination_mode
            )
            self.session_controller.set_mappings(self.field_mapping)
            self.session_controller.state.processed_excel_indices = getattr(self, '_processed_excel_indices', set())
            
            # 调用 controller 执行当前页填充
            self.session_controller._execute_anchor_page_fill()
            
            # 同步状态回 UI
            self._processed_excel_indices = self.session_controller.state.processed_excel_indices
            
            # 更新 UI
            state = self.session_controller.state
            self.master.add_log(f"本页填充完成: 成功 {state.total_success}, 失败 {state.total_error}")
            self.master.add_log(f"累计已处理: {len(self._processed_excel_indices)} 行")
            self.after(0, lambda: self.continue_btn.configure(state="normal"))
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.master.add_log(f"执行异常: {e}", "error")
        finally:
            self.start_btn.configure(state="normal", text="启动")

    
    def _execute_fill_continue(self):
        """从暂停位置继续执行填充 - 委托给 controller"""
        try:
            if not hasattr(self, '_paused_row_idx'):
                self.master.add_log("⚠️ 没有暂停的任务", "warning")
                return
            
            # 配置 controller
            mode_text = self.mode_selector.get()
            anchor_text = self.anchor_selector.get()
            key_column = anchor_text.replace("⚓ ", "") if anchor_text and "按顺序" not in anchor_text else None
            
            self.session_controller.set_config(
                fill_mode="batch_table" if "表格批量" in mode_text else "single_form",
                key_column=key_column,
                pagination_mode=self.pagination_mode
            )
            self.session_controller.set_mappings(self.field_mapping)
            self.session_controller.state.current_row_idx = self._paused_row_idx
            self.session_controller.state.current_page = getattr(self, '_paused_page_number', 1)
            
            # 最小化并继续
            self.master.iconify()
            self.master.add_log(f"📄 从第 {self._paused_row_idx + 1} 行继续...")
            
            # 调用 controller 继续填充
            self.session_controller.resume_fill()
            
            # 等待完成或暂停
            while self.session_controller.state.is_running and not self.session_controller.state.is_paused:
                if self.abort_event.is_set():
                    self.session_controller.stop_fill()
                    break
                time.sleep(0.2)
            
            # 同步状态回 UI
            if self.session_controller.state.is_paused:
                self._paused_row_idx = self.session_controller.state.current_row_idx
                self._paused_page_number = self.session_controller.state.current_page
                self.after(0, lambda: self.continue_btn.configure(state="normal"))
            else:
                # 填充完成
                state = self.session_controller.state
                self.master.add_log(f"{'='*40}")
                self.master.add_log("✅ 全部填表完成!", "success")
                self.master.add_log(f"   成功: {state.total_success} 行", "success")
                if state.total_error:
                    self.master.add_log(f"   失败: {state.total_error} 行", "error")
                self.master.add_log(f"{'='*40}")
                
                if hasattr(self, '_paused_row_idx'): del self._paused_row_idx
                if hasattr(self, '_paused_page_number'): del self._paused_page_number
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.master.add_log(f"❌ 执行异常: {e}", "error")
        finally:
            self._reset_button_states()

    
    def _update_progress_display(self, current, total, page, fields=None):
        """更新进度显示（详细信息：当前行、总行数、页码、字段数）"""
        try:
            if fields:
                info = f"第{page}页 | 第{current}-{min(current+4, total)}/{total}行 | {fields}字段"
            else:
                info = f"第{page}页 | 第{current}/{total}行"
            self.progress_label.configure(text=info)
        except:
            pass

    def _on_start_click(self):
        """点击启动按钮"""
        if not self.field_mapping:
            self.master.add_log("⚠️ 请先建立字段映射", "warning")
            return
        
        # 清除停止信号
        self.abort_event.clear()
        
        # 禁用所有交互按钮，启用停止按钮
        self.start_btn.configure(state="disabled", text="⏳ 运行中...")
        self.stop_btn.configure(state="normal")  # 启用停止按钮
        self.refresh_btn.configure(state="disabled")
        self.clear_mapping_btn.configure(state="disabled")
        if hasattr(self, 'save_btn'): self.save_btn.configure(state="disabled")
        if hasattr(self, 'load_btn'): self.load_btn.configure(state="disabled")
        if hasattr(self, 'anchor_selector'): self.anchor_selector.configure(state="disabled")
        if hasattr(self, 'mode_selector'): self.mode_selector.configure(state="disabled")
        
        # 启动后台线程
        threading.Thread(target=self._execute_fill, daemon=True).start()
    
    def _on_stop_click(self):
        """紧急停止按钮点击"""
        self.abort_event.set()
        self.master.add_log("🛑 用户手动终止，正在保存进度...", "warning")
        self.stop_btn.configure(state="disabled", text="⏹ 停止中...")
    
    def _open_column_computer(self):
        """打开智能列计算器 - 使用独立对话框组件"""
        def on_column_added(new_col_name):
            # 更新画布
            if hasattr(self.mapping_canvas, 'add_new_excel_column'):
                self.mapping_canvas.add_new_excel_column(new_col_name)
            else:
                self._rescan_form()
        
        ColumnComputerDialog(
            self,
            excel_data=self.excel_data,
            on_complete_callback=on_column_added,
            add_log_callback=self.master.add_log
        )

    def _execute_fill(self):
        """在后台线程执行智能填表 - 委托给 controller"""
        try:
            # === 1. 读取并配置 controller ===
            mode_text = self.mode_selector.get()
            fill_mode = "batch_table" if "表格批量" in mode_text else "single_form"
            
            anchor_text = self.anchor_selector.get()
            key_column = anchor_text if anchor_text and anchor_text != "按顺序录入" else None
            
            pagination_mode = self.pagination_mode if self.selected_pagination_btn else "manual"
            
            # 配置 controller
            self.session_controller.set_config(
                fill_mode=fill_mode,
                key_column=key_column,
                pagination_mode=pagination_mode
            )
            self.session_controller.set_mappings(self.field_mapping)
            
            # 设置翻页
            if self.selected_pagination_btn:
                btn_xpath = self.selected_pagination_btn.get('xpath', '')
                if btn_xpath:
                    self.session_controller.setup_pagination(btn_xpath)
            
            # === 2. 最小化窗口 ===
            self.master.iconify()
            self.master.add_log("📉 窗口已最小化，准备开始填表...")
            self.master.add_log(f"🚀 启动智能填表（自愈模式）")
            if key_column:
                self.master.add_log(f"   ⚓ 使用锚点列: {key_column}")
            self.master.add_log(f"   映射字段: {len(self.field_mapping)} 个")
            
            # === 3. 启动填充 ===
            self.session_controller.start_fill()
            
            # 等待填充完成或暂停
            while self.session_controller.state.is_running and not self.session_controller.state.is_paused:
                if self.abort_event.is_set():
                    self.session_controller.stop_fill()
                    break
                time.sleep(0.2)
            
            # === 4. 处理暂停状态 ===
            if self.session_controller.state.is_paused:
                self.after(0, lambda: self.continue_btn.configure(state="normal"))
                return
            
            # === 5. 填充完成 ===
            state = self.session_controller.state
            self.master.add_log(f"{'='*40}")
            self.master.add_log("✅ 全部填表完成!", "success")
            self.master.add_log(f"   成功: {state.total_success} 行", "success")
            if state.total_error:
                self.master.add_log(f"   失败: {state.total_error} 行", "error")
            if state.total_healed:
                self.master.add_log(f"   🩹 自动修复: {state.total_healed} 个", "success")
            self.master.add_log(f"{'='*40}")
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.master.add_log(f"❌ 执行异常: {e}", "error")
        finally:
            self._reset_button_states()
    
    def _reset_button_states(self):
        """重置按钮状态"""
        self.start_btn.configure(state="normal", text="🚀 启动")
        self.stop_btn.configure(state="disabled", text="⏹停止")
        self.refresh_btn.configure(state="normal")
        self.clear_mapping_btn.configure(state="normal")
        if hasattr(self, 'save_btn'): self.save_btn.configure(state="normal")
        if hasattr(self, 'load_btn'): self.load_btn.configure(state="normal")
        if hasattr(self, 'anchor_selector'): self.anchor_selector.configure(state="normal")
        if hasattr(self, 'mode_selector'): self.mode_selector.configure(state="normal")

    def _count_rows_on_current_page(self, tab):
        """检测当前页面的表格行数 - 委托给 controller"""
        return self.session_controller._count_rows_on_current_page()
    
    def _refresh_mappings_for_new_page(self):
        """翻页后刷新映射关系"""
        # 原有映射的Excel列名不变，但需要更新fingerprint指向新页面的元素
        # 由于 fingerprint 中的选择器（尤其是 XPath）可能是相对固定的，
        # 对于表格模式，每页的结构应该相同，所以选择器仍然有效
        # 这里主要是触发重新扫描，让 web_fingerprints 更新
        pass
    
    def _fill_single_anchor_row(self, tab, row_data, web_row_idx, key_column):
        """填充单行锚点匹配的数据 - 委托给 controller"""
        return self.session_controller._fill_single_anchor_row(row_data, web_row_idx, key_column)
    
    def _execute_anchor_fill_continue(self):
        """从暂停位置继续锚点模式填充 - 委托给 controller"""
        try:
            if not hasattr(self, '_paused_anchor_idx') or not hasattr(self, '_paused_matched_rows'):
                self.master.add_log("没有暂停的锚点任务", "warning")
                return
            
            # 配置 controller
            mode_text = self.mode_selector.get()
            fill_mode = "batch_table" if "批量" in mode_text else "single_form"
            
            self.session_controller.set_config(
                fill_mode=fill_mode,
                key_column=self._paused_key_column,
                pagination_mode=self.pagination_mode
            )
            self.session_controller.set_mappings(self.field_mapping)
            
            self.master.add_log(f"恢复锚点填充，从第 {self._paused_anchor_idx + 1} 条继续")
            
            # 调用 controller 继续锚点填充
            self.session_controller.resume_anchor_fill(
                matched_rows=self._paused_matched_rows,
                key_column=self._paused_key_column,
                start_idx=self._paused_anchor_idx
            )
            
            # 等待完成或暂停
            import time
            while self.session_controller.state.is_running and not self.session_controller.state.is_paused:
                if self.abort_event.is_set():
                    self.session_controller.stop_fill()
                    break
                time.sleep(0.2)
            
            # 同步状态回 UI
            if self.session_controller.state.is_paused:
                self._paused_anchor_idx = self.session_controller.state.current_row_idx
                self.after(0, lambda: self.continue_btn.configure(state="normal"))
            else:
                # 填充完成
                state = self.session_controller.state
                self.master.add_log(f"{'='*30}")
                self.master.add_log("锚点填充完成!", "success")
                self.master.add_log(f"  成功: {state.total_success} 行")
                if state.total_error:
                    self.master.add_log(f"  失败: {state.total_error} 行", "error")
                self.master.add_log(f"{'='*30}")
                
                # 清理暂停状态
                if hasattr(self, '_paused_anchor_idx'): del self._paused_anchor_idx
                if hasattr(self, '_paused_matched_rows'): del self._paused_matched_rows
                if hasattr(self, '_paused_key_column'): del self._paused_key_column
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.master.add_log(f"锚点继续执行异常: {e}", "error")
        finally:
            self.start_btn.configure(state="normal", text="启动")
            self.refresh_btn.configure(state="normal")

    def _save_configuration(self):
        """保存当前配置到文件"""
        filename = ctk.filedialog.asksaveasfilename(
            defaultextension=".json", 
            filetypes=[("JSON Config", "*.json")],
            title="保存填表任务配置"
        )
        if not filename: return
        
        try:
            data = {
                "mode": self.mode_selector.get(),
                "anchor": self.anchor_selector.get(),
                "mappings": {k: v.to_dict() for k, v in self.field_mapping.items()},
                "fingerprints": [fp.to_dict() for fp in self.matched_fingerprints]
            }
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.master.add_log(f"💾 配置已保存: {filename}", "success")
        except Exception as e:
            self.master.add_log(f"❌ 保存失败: {e}", "error")

    def _load_configuration(self):
        """从文件加载配置"""
        filename = ctk.filedialog.askopenfilename(
            filetypes=[("JSON Config", "*.json")],
            title="加载填表任务配置"
        )
        if not filename: return
        
        try:
            import json
            from app.core.element_fingerprint import ElementFingerprint
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 1. 恢复界面选项
            if "mode" in data: self.mode_selector.set(data["mode"])
            if "anchor" in data: self.anchor_selector.set(data["anchor"])
            
            # 2. 恢复指纹库 (避免重新扫描)
            if "fingerprints" in data:
                self.master.add_log("📂 正在恢复网页元素指纹...", "info")
                self.matched_fingerprints = [ElementFingerprint.from_dict(d) for d in data["fingerprints"]]
                
                # 重建画布
                mapping_parent = self.mapping_canvas.master
                self.mapping_canvas.destroy()
                self.mapping_canvas = MappingCanvas(
                    mapping_parent,
                    excel_columns=self.excel_data.columns.tolist(),
                    web_fingerprints=self.matched_fingerprints,
                    on_mapping_complete=self._on_canvas_mapping_complete,
                    on_element_click=self.highlight_element,
                    on_add_computed_column=self._open_column_computer
                )
                self.mapping_canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            
            # 3. 恢复映射关系
            if "mappings" in data:
                restored_map = {}
                missing_cols = []
                
                for col, fp_data in data["mappings"].items():
                    # 检查Excel列是否存在
                    if col not in self.excel_data.columns:
                        missing_cols.append(col)
                    
                    fp_obj = ElementFingerprint.from_dict(fp_data)
                    
                    # 尝试在现有指纹中找到匹配的对象（为了保持对象引用一致性）
                    found_existing = False
                    for existing in self.matched_fingerprints:
                        # 比较 raw_data 判定是否同一元素
                        if existing.raw_data == fp_obj.raw_data:
                             restored_map[col] = existing
                             found_existing = True
                             break
                    
                    if not found_existing:
                        # 如果没找到（极少情况），就用恢复的对象
                        restored_map[col] = fp_obj
                
                self.field_mapping = restored_map
                
                # 通知画布绘制
                # 注意：如果Excel列缺失，画布可能画不出来线，但我们要尽力画
                self.mapping_canvas.draw_mappings(restored_map)
                
                self.master.add_log(f"✅ 配置加载成功! 恢复 {len(restored_map)} 个映射", "success")
                
                if missing_cols:
                    self.master.add_log(f"⚠️ 注意: 配置文件引用了当前Excel不存在的列: {missing_cols}", "warning")
                    self.master.add_log(f"   请使用'添加计算列'功能重建这些列。", "warning")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.master.add_log(f"❌ 加载失败: {e}", "error")

    def on_closing(self):
        self.stop_event.set()
        self.destroy()
