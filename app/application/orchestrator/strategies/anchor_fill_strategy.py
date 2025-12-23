"""
锚点填充策略

基于关键列（锚点）匹配网页行与 Excel 行，实现精准填充。
适用于需要根据唯一标识定位行的场景（如病历号、患者ID）。
"""

import re
from typing import Any, List, Dict

from app.application.orchestrator.strategies.base_strategy import BaseFillStrategy
from app.core.smart_form_filler import SmartFormFiller


class AnchorFillStrategy(BaseFillStrategy):
    """
    锚点模式填充策略
    
    工作流程:
    1. 扫描网页锚点列，构建 {锚点值: 行索引} 映射
    2. 匹配 Excel 数据与网页行
    3. 逐行填充匹配的数据
    
    特点:
    - 支持翻页后重新扫描锚点
    - 自动跳过已处理的行（防止重复填充）
    - 支持单条/批量模式
    """
    
    def execute(self) -> None:
        """执行锚点模式填充"""
        key_column = self.config.key_column
        if not key_column:
            self._log("❌ 未设置锚点列", "error")
            return
        
        # 构建锚点映射
        matched_rows = self._build_anchor_map(key_column)
        
        if not matched_rows:
            self._log("⚠️ 没有匹配的数据行", "warning")
            return
        
        # 保存匹配结果到状态，供恢复时使用
        self.state.matched_rows = matched_rows
        self.state.anchor_key_column = key_column
        
        # 执行填充
        self._execute_anchor_fill(matched_rows, key_column, self.config.fill_mode)
    
    def continue_fill(self) -> None:
        """锚点模式翻页后继续填充"""
        key_column = self.config.key_column or self.state.anchor_key_column
        if not key_column:
            return
        
        # 重新扫描当前页锚点
        matched_rows = self._build_anchor_map(key_column)
        
        # 过滤已处理的行
        unprocessed = [
            r for r in matched_rows 
            if r['excel_idx'] not in self.state.processed_excel_indices
        ]
        
        if not unprocessed:
            self._log("当前页没有匹配的数据", "warning")
            return
        
        self._log(f"本页匹配 {len(unprocessed)} 条数据")
        
        for match_info in unprocessed:
            if self.abort_event.is_set():
                break
            
            success = self._fill_single_anchor_row(
                match_info['excel_data'],
                match_info['web_row_idx'],
                key_column
            )
            
            if success:
                self.state.total_success += 1
                self.state.processed_excel_indices.add(match_info['excel_idx'])
            else:
                self.state.total_error += 1
            
            # 单条模式暂停
            if self.config.fill_mode == "single_form":
                self._log(f"⏸️ 已完成 1 条，请点击继续")
                self.state.is_paused = True
                return
        
        self._log("本页填充完成")
        self.state.is_paused = True  # 等待用户翻页
    
    def _build_anchor_map(self, key_column: str) -> List[dict]:
        """构建锚点匹配映射"""
        self._log(f"⚓ 锚点模式：正在扫描网页锚点列...")
        
        anchor_fp = self.field_mapping.get(key_column)
        if not anchor_fp:
            self._log(f"锚点列 {key_column} 未映射", "error")
            return []
        
        xpath = anchor_fp.selectors.get('xpath', '')
        
        if not xpath:
            self._log("锚点列没有有效的XPath", "error")
            return []
        
        # 将具体行索引替换为通用匹配
        generic_xpath = re.sub(r'tr\[\d+\]', 'tr', xpath)
        
        try:
            web_row_map = {}
            elements = self.tab.eles(f'xpath:{generic_xpath}')
            for idx, ele in enumerate(elements):
                txt = (ele.text or ele.attr('value') or '').strip()
                if txt:
                    web_row_map[txt] = idx
            
            self._log(f"   ✅ 网页锚点扫描完成，找到 {len(web_row_map)} 个唯一值")
            
            matched_rows = []
            for idx, row in self.excel_data.iterrows():
                excel_key = str(row.get(key_column, '')).strip()
                if excel_key in web_row_map:
                    matched_rows.append({
                        'excel_idx': idx,
                        'excel_data': row,
                        'web_row_idx': web_row_map[excel_key],
                        'anchor_value': excel_key
                    })
            
            matched_rows.sort(key=lambda x: x['web_row_idx'])
            self._log(f"   ⚓ 匹配成功 {len(matched_rows)} 行")
            
            return matched_rows
            
        except Exception as e:
            self._log(f"❌ 锚点扫描失败: {e}", "error")
            return []
    
    def _execute_anchor_fill(self, matched_rows: List[dict], key_column: str, fill_mode: str):
        """执行锚点模式填充"""
        total_matched = len(matched_rows)
        current_idx = self.state.current_row_idx  # 支持从暂停位置恢复
        
        while current_idx < total_matched:
            if self.abort_event.is_set():
                self._log("🛑 用户手动终止", "warning")
                break
            
            match_info = matched_rows[current_idx]
            web_row_idx = match_info['web_row_idx']
            anchor_val = match_info['anchor_value']
            row_data = match_info['excel_data']
            
            self._log(f"⚓ 填充: {anchor_val} → 网页第{web_row_idx+1}行")
            
            success = self._fill_single_anchor_row(row_data, web_row_idx, key_column)
            
            if success:
                self.state.total_success += 1
                self.state.processed_excel_indices.add(match_info['excel_idx'])
            else:
                self.state.total_error += 1
            
            current_idx += 1
            self._progress(current_idx, total_matched, 1)
            
            # 单条模式暂停
            if fill_mode == "single_form" and current_idx < total_matched:
                self._log(f"⏸️ 已完成 {current_idx}/{total_matched}")
                self.state.current_row_idx = current_idx
                self.state.is_paused = True
                return
        
        self._complete_fill()
    
    def _fill_single_anchor_row(self, row_data: Any, web_row_idx: int, key_column: str) -> bool:
        """
        填充单行锚点匹配的数据 - 基于锚点定位行
        
        核心逻辑：
        1. 找到锚点值所在的行元素
        2. 在该行内查找其他输入框
        3. 按列名匹配并填充
        """
        try:
            # 获取锚点值
            anchor_value = str(row_data.get(key_column, '')).strip()
            if not anchor_value:
                return False
            
            # === 策略1: 通过锚点值定位行 ===
            row_element = None
            
            # 方法1: 通过文本内容查找
            try:
                anchor_ele = self.tab.ele(f'xpath://tr[.//text()[contains(., "{anchor_value}")]]', timeout=0.3)
                if anchor_ele:
                    row_element = anchor_ele
            except:
                pass
            
            # 方法2: 通过 input value 或 td text
            if not row_element:
                try:
                    anchor_ele = self.tab.ele(f'xpath://tr[.//input[@value="{anchor_value}"] or ./td[text()="{anchor_value}"]]', timeout=0.3)
                    if anchor_ele:
                        row_element = anchor_ele
                except:
                    pass
            
            # 方法3: 通过索引定位行
            if not row_element:
                try:
                    row_element = self.tab.ele(f'xpath://table//tbody/tr[{web_row_idx + 1}]', timeout=0.3)
                except:
                    pass
            
            # 方法4: 直接用 tr 索引
            if not row_element:
                try:
                    row_element = self.tab.ele(f'xpath://tr[{web_row_idx + 1}]', timeout=0.3)
                except:
                    pass
            
            filled_count = 0
            
            if row_element:
                # === 在找到的行内查找并填充输入框 ===
                for excel_col, fingerprint in self.field_mapping.items():
                    if excel_col == key_column:
                        continue
                    
                    cell_value = row_data.get(excel_col)
                    if cell_value is None or (isinstance(cell_value, float) and str(cell_value) == 'nan'):
                        continue
                    cell_value = str(cell_value).strip()
                    if not cell_value:
                        continue
                    
                    try:
                        placeholder = fingerprint.anchors.get('placeholder', '')
                        col_name = fingerprint.features.get('name', '')
                        
                        input_ele = None
                        
                        # 在行内通过 placeholder 查找
                        if placeholder:
                            input_ele = row_element.ele(f'xpath:.//input[@placeholder="{placeholder}"]', timeout=0.2)
                        
                        # 在行内通过 name 查找
                        if not input_ele and col_name:
                            input_ele = row_element.ele(f'xpath:.//input[@name="{col_name}"]', timeout=0.2)
                        
                        # 通过列索引查找
                        if not input_ele:
                            inputs = row_element.eles('tag:input') + row_element.eles('tag:textarea')
                            col_idx = fingerprint.table_info.get('column_index', -1)
                            if col_idx >= 0 and col_idx < len(inputs):
                                input_ele = inputs[col_idx]
                            elif len(inputs) > 0 and placeholder:
                                for inp in inputs:
                                    inp_placeholder = inp.attr('placeholder') or ''
                                    if placeholder in inp_placeholder:
                                        input_ele = inp
                                        break
                        
                        if input_ele:
                            input_ele.clear()
                            input_ele.input(cell_value)
                            filled_count += 1
                            
                    except Exception as e:
                        print(f"填充 {excel_col} 失败: {e}")
            else:
                # 回退到标准填充
                for excel_col, fingerprint in self.field_mapping.items():
                    if excel_col == key_column:
                        continue
                    
                    cell_value = row_data.get(excel_col)
                    if cell_value is None or (isinstance(cell_value, float) and str(cell_value) == 'nan'):
                        continue
                    cell_value = str(cell_value).strip()
                    if not cell_value:
                        continue
                    
                    try:
                        success = SmartFormFiller._fill_with_fallback(self.tab, fingerprint, cell_value)
                        if success:
                            filled_count += 1
                    except:
                        pass
            
            return filled_count > 0
            
        except Exception as e:
            print(f"_fill_single_anchor_row 异常: {e}")
            return False
