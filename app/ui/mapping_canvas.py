"""
可视化映射画布 - 升级版（支持元素指纹+滚动条+高亮）
"""
import customtkinter as ctk
from tkinter import Canvas, Scrollbar, VERTICAL
from app.ui.styles import ThemeColors, UIStyles
from app.ui.components import AnimatedButton

class MappingCanvas(ctk.CTkFrame):
    """可视化映射画布（支持ElementFingerprint）"""
    
    def __init__(self, master, excel_columns, web_fingerprints, on_mapping_complete=None, on_element_click=None, on_add_computed_column=None, width=800, height=600):
        super().__init__(master, width=width, height=height)
        
        self.excel_columns = list(excel_columns) # copy
        self.web_fingerprints = web_fingerprints
        self.on_mapping_complete = on_mapping_complete
        self.on_element_click = on_element_click
        self.on_add_computed_column = on_add_computed_column
        
        self.mappings = {}
        self.selected_excel = None
        self.selected_web = None
        
        self.excel_boxes = {}
        self.web_boxes = {}
        self.connection_lines = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """构建UI"""
        # 1. 顶部区域
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=5)
        
        title = ctk.CTkLabel(top_frame, 
                           text="🎨 智能映射画布",
                           font=ctk.CTkFont(family=UIStyles.FONT_FAMILY,size=14, weight="bold"),
                           text_color=ThemeColors.ACCENT_PRIMARY)
        title.pack()
        
        hint = ctk.CTkLabel(top_frame,
                          text="点击Excel列 → 点击网页字段 → 自动连线（绿色=高稳定，黄色=中等，蓝色=低稳定）",
                          font=ctk.CTkFont(family=UIStyles.FONT_FAMILY,size=10),
                          text_color=ThemeColors.TEXT_SECONDARY)
        hint.pack()

        # 2. 画布容器 (用于放置Canvas和Scrollbar)
        canvas_container = ctk.CTkFrame(self, fg_color="transparent")
        canvas_container.pack(fill="both", expand=True, padx=2, pady=2)
        
        # 3. 滚动条
        self.v_scroll = Scrollbar(canvas_container, orient=VERTICAL)
        self.v_scroll.pack(side="right", fill="y")
        
        # 4. Canvas画布
        # 4. Canvas画布
        self.canvas = Canvas(canvas_container, 
                            bg="#FFFFFF", 
                            highlightthickness=0,
                            yscrollcommand=self.v_scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.v_scroll.config(command=self.canvas.yview)
        
        # 5. 绑定事件
        self._draw_layout()
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mousewheel)    # Linux
        self.canvas.bind("<Button-5>", self._on_mousewheel)    # Linux

    def _on_mousewheel(self, event):
        """处理鼠标滚轮"""
        try:
            if event.delta: # Windows
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif event.num == 4: # Linux Up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5: # Linux Down
                self.canvas.yview_scroll(1, "units")
        except: pass

    def _on_add_btn_click(self):
        """添加计算按钮点击事件"""
        if self.on_add_computed_column:
            self.on_add_computed_column()

    def _draw_layout(self):
        """绘制布局（自适应框宽度）"""
        self.canvas.delete("all")
        
        canvas_width = 1000  # 增加画布宽度
        min_box_width = 150   # 最小宽度
        max_box_width = 400   # 增大最大宽度，避免文字溢出
        box_height = 55
        spacing = 15
        padding = 20  # 文字与框边距
        
        # 计算需要的最大高度
        max_items = max(len(self.excel_columns), len(self.web_fingerprints))
        total_height = 100 + max_items * (box_height + spacing)
        
        # 更新滚动区域
        self.canvas.configure(scrollregion=(0, 0, canvas_width, total_height))
        
        # ===== Excel 列区域（边框右对齐）=====
        excel_right_edge = 310  # Excel框的右边界固定位置
        
        self.canvas.create_text(excel_right_edge - 100, 30, 
                               text="📊 Excel列", 
                               fill="#000000", 
                               font=(UIStyles.FONT_FAMILY, 15, "bold"))
        
        # ===== 网页字段区域（边框左对齐）=====
        web_left_edge = canvas_width - 350  # 网页框的左边界固定位置
        
        # 中间：添加计算按钮
        center_x = (excel_right_edge + web_left_edge) / 2
        self.add_calc_btn = AnimatedButton(
            self.canvas,
            text="➕添加计算",
            height=30,
            command=self._on_add_btn_click
        )
        self.canvas.create_window(center_x, 30, window=self.add_calc_btn, tags="add_col_btn")
        
        self.canvas.create_text(web_left_edge + 100, 30,
                               text="🌐 网页字段",
                               fill="#000000",
                               font=(UIStyles.FONT_FAMILY, 15, "bold"))
        
        y_offset = 60
        
        # 绘制 Excel 列（边框右对齐，文字居中）
        for idx, col_name in enumerate(self.excel_columns):
            y = y_offset + idx * (box_height + spacing)
            
            # 计算文字宽度
            text_width = len(col_name) * 12 + padding * 2
            box_width = max(min_box_width, min(text_width, max_box_width))
            
            # 右对齐：右边界固定，左边界根据宽度调整
            x1 = excel_right_edge - box_width
            x2 = excel_right_edge
            
            box_id = self.canvas.create_rectangle(
                x1, y, x2, y + box_height,
                fill="#FFFFFF",
                outline="#000000",
                width=1,
                tags=("excel_box", f"excel_{col_name}")
            )
            
            # 文字居中
            text_id = self.canvas.create_text(
                (x1 + x2) / 2, y + box_height/2,
                text=col_name,
                fill="#000000",
                font=(UIStyles.FONT_FAMILY, 14),
                tags=(f"excel_{col_name}",)
            )
            
            self.excel_boxes[col_name] = (x1, y, x2, y + box_height, box_id, text_id)
        
        # 绘制网页字段（边框左对齐，文字居中）
        for idx, fingerprint in enumerate(self.web_fingerprints):
            y = y_offset + idx * (box_height + spacing)
            
            # 根据稳定性选择颜色
            if fingerprint.stability_score >= 80:
                outline_color = "#000000"
            elif fingerprint.stability_score >= 50:
                outline_color = "#666666"
            else:
                outline_color = "#AAAAAA"
            
            # 获取显示名称（不带类型符号）
            display_name = fingerprint.get_display_name()
            
            # 计算文字宽度（中文约14px/字符）
            text_width = len(display_name) * 14 + padding * 2
            box_width = max(min_box_width, min(text_width, max_box_width))
            
            # 左对齐：左边界固定，右边界根据宽度调整
            x1 = web_left_edge
            x2 = web_left_edge + box_width
            
            box_id = self.canvas.create_rectangle(
                x1, y, x2, y + box_height,
                fill="#FFFFFF",
                outline="#000000",
                width=1,
                tags=("web_box", f"web_{idx}")
            )
            
            # 文字居中，超长截断
            if len(display_name) > 28:
                display_text = display_name[:26] + "..."
            else:
                display_text = display_name
            
            text_id = self.canvas.create_text(
                (x1 + x2) / 2, y + box_height/2,
                text=display_text,
                fill="#000000",
                font=(UIStyles.FONT_FAMILY, 14),
                tags=(f"web_{idx}",)
            )
            
            # 不再显示稳定性分数
            
            self.web_boxes[idx] = (x1, y, x2, y + box_height, box_id, text_id, fingerprint)
    
    def _on_canvas_click(self, event):
        """Canvas点击事件"""
        # 注意：event.x, event.y 是相对于可见区域的坐标
        # 我们需要加上滚动偏移
        scrolled_y = self.canvas.canvasy(event.y)
        x = event.x
        y = scrolled_y
        
        # 检查是否点击了"添加计算列"按钮
        # 按钮在顶部，不受滚动影响太大，但稍微修正一下
        # 按钮区域 y=15~45, 但scrolled_y可能很大
        # 简单起见，find_closest
        item = self.canvas.find_closest(event.x, scrolled_y)[0]
        tags = self.canvas.gettags(item)
        
        if "add_col_btn" in tags:
            if self.on_add_computed_column:
                self.on_add_computed_column()
            return

        # 检查Excel列
        for col_name, (x1, y1, x2, y2, box_id, text_id) in self.excel_boxes.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                self._select_excel_column(col_name, box_id)
                return
        
        # 检查网页字段
        for idx, (x1, y1, x2, y2, box_id, text_id, fingerprint) in self.web_boxes.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                # 触发高亮回调
                if self.on_element_click:
                    self.on_element_click(fingerprint)
                
                self._select_web_field(idx, box_id, fingerprint)
                return
    
    def _select_excel_column(self, col_name, box_id):
        """选择Excel列"""
        # 恢复之前选中的（如果有）
        if self.selected_excel:
            old_box_id = self.excel_boxes[self.selected_excel][4]
            self.canvas.itemconfig(old_box_id, fill="#FFFFFF")  # 恢复白色
        
        # 选中当前：填充变灰，边框不变
        self.canvas.itemconfig(box_id, fill="#E0E0E0")  # 灰色填充
        self.selected_excel = col_name
    
    def _select_web_field(self, idx, box_id, fingerprint):
        """选择网页字段"""
        if not self.selected_excel:
            return
        
        # 已选中的 Excel 列和网页字段都变灰表示已匹配
        excel_box_id = self.excel_boxes[self.selected_excel][4]
        self.canvas.itemconfig(excel_box_id, fill="#D0D0D0")  # 已匹配的灰色
        self.canvas.itemconfig(box_id, fill="#D0D0D0")  # 已匹配的灰色
        
        self._create_connection(self.selected_excel, idx, fingerprint)
        
        self.selected_excel = None
    
    def _create_connection(self, excel_col, web_idx, fingerprint):
        """创建连接线"""
        if excel_col in self.connection_lines:
            self.canvas.delete(self.connection_lines[excel_col])
        
        ex1, ey1, ex2, ey2, _, _ = self.excel_boxes[excel_col]
        wx1, wy1, wx2, wy2, _, _, _ = self.web_boxes[web_idx]
        
        start_x = ex2
        start_y = (ey1 + ey2) / 2
        end_x = wx1
        end_y = (wy1 + wy2) / 2
        mid_x = (start_x + end_x) / 2
        
        # 根据稳定性选择连线颜色
        if fingerprint.stability_score >= 80:
            line_color = "#000000"
        elif fingerprint.stability_score >= 50:
            line_color = "#666666"
        else:
            line_color = "#AAAAAA"
        
        line_id = self.canvas.create_line(
            start_x, start_y,
            mid_x, start_y,
            mid_x, end_y,
            end_x, end_y,
            fill=line_color,
            width=3,
            smooth=True,
            tags=("connection",)
        )
        
        self.canvas.tag_lower(line_id)
        self.connection_lines[excel_col] = line_id
        
        # 更新映射
        self.mappings[excel_col] = fingerprint
        
        # 更新方块颜色
        excel_box_id = self.excel_boxes[excel_col][4]
        self.canvas.itemconfig(excel_box_id, outline="#000000", fill="#F5F5F7")
        
        web_box_id = self.web_boxes[web_idx][4]
        self.canvas.itemconfig(web_box_id, outline="#000000", fill="#F5F5F7")
        
        if self.on_mapping_complete:
            self.on_mapping_complete(self.mappings)

    def draw_mappings(self, mappings):
        """
        程序化绘制映射连线 (API)
        Args:
            mappings: dict {excel_col_name: ElementFingerprint}
        """
        self.msg_label = ctk.CTkLabel(self, text="正在绘制连线...", text_color=ThemeColors.TEXT_MUTED)
        self.msg_label.pack()
        
        count = 0
        for excel_col, target_fp in mappings.items():
            # 1. 找到 Excel 列的索引/Box
            if excel_col not in self.excel_boxes:
                continue
                
            # 2. 找到 Web Fingerprint 的索引
            # 注意：web_fingerprints 是列表，target_fp 是对象
            # 我们需要找到它在 self.web_fingerprints 中的下标
            web_idx = -1
            for idx, fp in enumerate(self.web_fingerprints):
                # 比较指纹对象是否相同，或者核心特征是否一致
                if fp == target_fp or fp.raw_data == target_fp.raw_data:
                    web_idx = idx
                    break
            
            if web_idx != -1:
                self._create_connection(excel_col, web_idx, target_fp)
                count += 1
        
        self.msg_label.destroy()
        # 触发回调更新上层数据
        if self.on_mapping_complete:
            self.on_mapping_complete(self.mappings)
    
    def clear_all_mappings(self):
        """清空所有映射"""
        for line_id in self.connection_lines.values():
            self.canvas.delete(line_id)
        
        self.connection_lines.clear()
        self.mappings.clear()
        
        for col_name, (_, _, _, _, box_id, _) in self.excel_boxes.items():
            self.canvas.itemconfig(box_id, outline="#000000", fill="#FFFFFF", width=1)
        
        for idx, (_, _, _, _, box_id, _, fingerprint) in self.web_boxes.items():
            if fingerprint.stability_score >= 80:
                outline_color = "#000000"
            elif fingerprint.stability_score >= 50:
                outline_color = "#666666"
            else:
                outline_color = "#AAAAAA"
            self.canvas.itemconfig(box_id, outline=outline_color, fill="#FFFFFF", width=1)
