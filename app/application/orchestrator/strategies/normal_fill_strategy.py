"""
普通填充策略

顺序逐行填充 Excel 数据到网页表单。
适用于网页表格行与 Excel 行一一对应的简单场景。
"""

from typing import Any

from app.application.orchestrator.strategies.base_strategy import BaseFillStrategy
from app.core.smart_form_filler import SmartFormFiller


class NormalFillStrategy(BaseFillStrategy):
    """
    普通模式填充策略
    
    工作流程:
    1. 检测当前页面表格行数
    2. 按行顺序填充 Excel 数据
    3. 支持自动/手动翻页
    
    特点:
    - 简单顺序填充，无需锚点匹配
    - 支持翻页分批处理
    - 自动检测页面行数
    """
    
    def execute(self) -> None:
        """执行普通模式填充"""
        fill_mode = self.config.fill_mode
        has_pagination = self.pagination_controller is not None
        is_auto_mode = self.config.pagination_mode == "auto"
        
        self._execute_normal_fill(fill_mode, has_pagination, is_auto_mode)
    
    def continue_fill(self) -> None:
        """普通模式翻页后继续填充"""
        fill_mode = self.config.fill_mode
        has_pagination = self.pagination_controller is not None
        is_auto_mode = self.config.pagination_mode == "auto"
        
        if self.state.current_page > 1:
            self.controller.rebind_mappings_for_current_page()
            
        self._execute_normal_fill(fill_mode, has_pagination, is_auto_mode)
    
    def _execute_normal_fill(self, fill_mode: str, has_pagination: bool, is_auto_mode: bool):
        """执行普通模式填充"""
        total_rows = len(self.excel_data)
        current_row_idx = self.state.current_row_idx
        page_number = self.state.current_page
        
        while current_row_idx < total_rows:
            if self.abort_event.is_set():
                self._log("🛑 用户手动终止", "warning")
                break
            
            # ===== 批量填充优先逻辑（遵循批量填充原则）=====
            # 优先检查是否有批量选择的输入框
            max_batch_inputs = 0
            for fp in self.field_mapping.values():
                related = getattr(fp, 'related_inputs', None)
                if related and len(related) > 0:
                    batch_count = 1 + len(related)  # 主元素 + 关联元素
                    max_batch_inputs = max(max_batch_inputs, batch_count)
            
            if max_batch_inputs > 0:
                # 批量模式：以用户选择的输入框数量为准
                rows_on_page = max_batch_inputs
                self._log(f"📊 批量填充模式: {rows_on_page} 个输入框")
            else:
                # 非批量模式：检测页面行数
                rows_on_page = self._count_rows_on_current_page()
                if rows_on_page == 0:
                    rows_on_page = total_rows  # 使用全部 Excel 行数
            
            end_row_idx = min(current_row_idx + rows_on_page, total_rows)
            page_data = self.excel_data.iloc[current_row_idx:end_row_idx]
            
            self._log(f"📄 第 {page_number} 页: 填充第 {current_row_idx+1}-{end_row_idx} 行")
            self._progress(current_row_idx, total_rows, page_number)
            
            result = SmartFormFiller.fill_form_with_healing(
                tab=self.tab,
                excel_data=self.excel_data,  # 传完整数据，由函数内部跳过已处理的行
                fingerprint_mappings=self.field_mapping,
                fill_mode=fill_mode,
                key_column=None,
                progress_callback=lambda c, t, m, s: self._log(m, s),
                start_row_idx=current_row_idx  # 从当前行开始
            )
            
            self.state.total_success += result['success']
            self.state.total_error += result['error']
            self.state.total_healed += result['healed']
            self.state.errors.extend(result['errors'])
            
            # 从结果获取下一行索引
            current_row_idx = result.get('next_row_idx', current_row_idx + 1)
            
            if current_row_idx < total_rows:
                if has_pagination and is_auto_mode:
                    # 全自动翻页
                    page_turned = self.pagination_controller.click_next_page(wait_after=1.5)
                    if page_turned:
                        page_number += 1
                        self.pagination_controller.wait_for_page_ready(timeout=5)
                        self._log(f"✅ 已翻至第 {page_number} 页")
                        self.controller.rebind_mappings_for_current_page()
                    else:
                        self._log("⚠️ 翻页失败，可能已是最后一页", "warning")
                        break
                else:
                    # 手动翻页暂停
                    self._log(f"⏸️ 第 {page_number} 页已完成，请手动翻页后继续")
                    self.state.current_row_idx = current_row_idx
                    self.state.current_page = page_number + 1
                    self.state.is_paused = True
                    return
        
        self._complete_fill()
    
    def _count_rows_on_current_page(self) -> int:
        """检测当前页面的表格行数"""
        try:
            js = """
            (() => {
                let rows = document.querySelectorAll('table tbody tr');
                if (rows.length === 0) {
                    rows = document.querySelectorAll('table tr');
                    if (rows.length > 0) rows = Array.from(rows).slice(1);
                }
                if (rows.length === 0) {
                    rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
                }
                return rows.length;
            })();
            """
            count = self.tab.run_js(js)
            return count if isinstance(count, int) else 0
        except Exception as e:
            print(f"检测行数失败: {e}")
            return 0
