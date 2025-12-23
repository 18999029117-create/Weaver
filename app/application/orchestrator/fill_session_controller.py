"""
填充会话控制器

从 process_window.py 抽离的核心业务逻辑。
负责协调扫描、填充、翻页等操作。

原则:
- 不包含任何 UI 代码
- 通过回调与 UI 层通信
- 可独立进行单元测试

重构说明:
- 采用策略模式拆分填充逻辑
- AnchorFillStrategy: 锚点模式填充
- NormalFillStrategy: 普通模式填充
"""

import re
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field

# 领域层
from app.domain.entities import ElementFingerprint, FillProgress, FillRecord, PageState

# 核心模块（后续重构时可改为接口注入）
from app.core.smart_form_analyzer import SmartFormAnalyzer
from app.core.smart_form_filler import SmartFormFiller
from app.core.smart_matcher import SmartMatcher
from app.core.pagination_controller import PaginationController
from app.core.fill_progress_manager import FillProgressManager

# 填充策略
from app.application.orchestrator.strategies import AnchorFillStrategy, NormalFillStrategy


@dataclass
class FillSessionConfig:
    """填充会话配置"""
    fill_mode: str = "single_form"  # single_form / batch_table
    key_column: Optional[str] = None  # 锚点列名
    pagination_mode: str = "manual"  # manual / auto
    pagination_xpath: Optional[str] = None  # 翻页按钮 XPath


@dataclass
class FillSessionState:
    """填充会话状态"""
    is_running: bool = False
    is_paused: bool = False
    current_row_idx: int = 0
    current_page: int = 1
    total_success: int = 0
    total_error: int = 0
    total_healed: int = 0
    errors: List[str] = field(default_factory=list)
    processed_excel_indices: Set[int] = field(default_factory=set)
    # 锚点填充状态
    matched_rows: List[dict] = field(default_factory=list)
    anchor_key_column: Optional[str] = None


class FillSessionController:
    """
    填充会话控制器
    
    职责:
    - 协调扫描、匹配、填充流程
    - 管理会话状态
    - 处理翻页逻辑
    - 提供进度回调
    
    这是从 process_window.py 抽离的核心业务逻辑，
    不包含任何 UI 代码，可独立测试。
    """
    
    def __init__(
        self,
        browser_tab: Any,
        excel_data: Any,  # pandas DataFrame
        log_callback: Optional[Callable[[str, str], None]] = None,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ):
        """
        初始化填充会话控制器
        
        Args:
            browser_tab: 浏览器标签页对象
            excel_data: pandas DataFrame
            log_callback: 日志回调 (message, level)
            progress_callback: 进度回调 (current, total, page)
        """
        self.tab = browser_tab
        self.excel_data = excel_data
        self._log = log_callback or (lambda m, l="info": print(f"[{l}] {m}"))
        self._progress = progress_callback or (lambda c, t, p: None)
        
        # 状态
        self.config = FillSessionConfig()
        self.state = FillSessionState()
        
        # 元素指纹
        self.web_fingerprints: List[ElementFingerprint] = []
        self.matched_fingerprints: List[ElementFingerprint] = []
        self.field_mapping: Dict[str, ElementFingerprint] = {}
        self.auto_mappings: Dict[str, ElementFingerprint] = {}
        
        # 翻页控制
        self.pagination_controller: Optional[PaginationController] = None
        self.progress_manager = FillProgressManager()
        self.pagination_elements: List[dict] = []
        
        # 事件
        self.abort_event = threading.Event()
    
    # ==================== 扫描服务 ====================
    
    def scan_page(self, max_wait: float = 15.0) -> List[ElementFingerprint]:
        """
        扫描网页元素
        
        Returns:
            ElementFingerprint 列表
        """
        self._log("🔍 启动深度扫描（多维指纹采集）...")
        
        try:
            self.web_fingerprints = SmartFormAnalyzer.deep_scan_page(
                self.tab, max_wait=max_wait
            )
            
            if self.web_fingerprints:
                high_stable = sum(1 for f in self.web_fingerprints if f.stability_score >= 80)
                mid_stable = sum(1 for f in self.web_fingerprints if 50 <= f.stability_score < 80)
                low_stable = sum(1 for f in self.web_fingerprints if f.stability_score < 50)
                
                self._log(f"✅ 发现 {len(self.web_fingerprints)} 个输入字段", "success")
                self._log(f"   🟢 高稳定性: {high_stable} | 🟡 中等: {mid_stable} | 🔵 低: {low_stable}")
            else:
                self._log("⚠️ 未找到任何输入字段", "warning")
                
            return self.web_fingerprints
            
        except Exception as e:
            self._log(f"❌ 扫描失败: {e}", "error")
            return []
    
    def match_fields(self) -> Dict[str, ElementFingerprint]:
        """
        执行智能匹配
        
        Returns:
            自动匹配结果 {excel_col: ElementFingerprint}
        """
        if not self.web_fingerprints:
            return {}
        
        excel_columns = self.excel_data.columns.tolist()
        if not excel_columns:
            return {}
        
        self._log("🎯 执行智能匹配...")
        
        match_result = SmartMatcher.match_fields(excel_columns, self.web_fingerprints)
        
        # 去重逻辑
        unique_fingerprints = []
        seen_base_names = set()
        
        for excel_col, fp, score in match_result['matched']:
            base_name = self._get_base_name(fp)
            if base_name and base_name not in seen_base_names:
                unique_fingerprints.append(fp)
                seen_base_names.add(base_name)
        
        unmatched_sorted = sorted(
            match_result['unmatched_web'],
            key=lambda fp: fp.stability_score,
            reverse=True
        )
        
        for fp in unmatched_sorted:
            base_name = self._get_base_name(fp)
            if base_name and base_name not in seen_base_names:
                unique_fingerprints.append(fp)
                seen_base_names.add(base_name)
        
        self.matched_fingerprints = unique_fingerprints
        
        # 保存自动匹配建议
        self.auto_mappings.clear()
        for excel_col, fp, score in match_result['matched']:
            if score >= 90:
                fp.stability_score = 100
                self.auto_mappings[excel_col] = fp
            elif score >= 80:
                self.auto_mappings[excel_col] = fp
        
        if self.auto_mappings:
            self._log(f"✅ 自动建议 {len(self.auto_mappings)} 个高质量映射", "success")
        
        return self.auto_mappings
    
    def _get_base_name(self, fp: ElementFingerprint) -> str:
        """获取基础名称（用于去重）"""
        if fp.anchors.get('label'):
            return fp.anchors['label'].strip()
        if fp.anchors.get('visual_label'):
            return fp.anchors['visual_label'].strip()
        if fp.table_info.get('table_header'):
            return fp.table_info['table_header'].strip()
        if fp.anchors.get('placeholder'):
            return fp.anchors['placeholder'].strip()
        return fp.features.get('name', '') or fp.raw_data.get('id', '')
    
    # ==================== 翻页服务 ====================
    
    def detect_pagination(self) -> List[dict]:
        """
        检测翻页按钮
        
        Returns:
            翻页按钮列表
        """
        js_detect = """
        (function() {
            const keywords = ['下一页', '下一条', 'Next', 'next', '下页', '后一页', 
                              '翻页', '下一步', '向后', '››', '»', '>>', '>', '→'];
            const results = [];
            
            const elements = document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"], .btn, .page-btn');
            
            elements.forEach((el, idx) => {
                const text = (el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim();
                const className = el.className || '';
                const id = el.id || '';
                
                let isMatch = false;
                let matchKeyword = '';
                
                for (let kw of keywords) {
                    if (text.includes(kw) || className.toLowerCase().includes('next') || id.toLowerCase().includes('next')) {
                        isMatch = true;
                        matchKeyword = text || kw;
                        break;
                    }
                }
                
                if (isMatch && text.length < 50) {
                    let xpath = '';
                    if (el.id) {
                        xpath = `//*[@id="${el.id}"]`;
                    } else {
                        let path = [];
                        let current = el;
                        while (current && current !== document.body) {
                            let tag = current.tagName.toLowerCase();
                            let parent = current.parentElement;
                            if (parent) {
                                let siblings = Array.from(parent.children).filter(c => c.tagName === current.tagName);
                                if (siblings.length > 1) {
                                    let index = siblings.indexOf(current) + 1;
                                    tag += '[' + index + ']';
                                }
                            }
                            path.unshift(tag);
                            current = parent;
                        }
                        xpath = '//' + path.join('/');
                    }
                    
                    results.push({
                        text: matchKeyword.substring(0, 30),
                        tagName: el.tagName.toLowerCase(),
                        id: el.id || '',
                        className: (el.className || '').substring(0, 50),
                        xpath: xpath
                    });
                }
            });
            
            return results;
        })();
        """
        
        try:
            result = self.tab.run_js(js_detect)
            
            self.pagination_elements = []
            if result and isinstance(result, list):
                seen_texts = set()
                for item in result:
                    text = item.get('text', '翻页按钮')
                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        self.pagination_elements.append({
                            'text': text,
                            'xpath': item.get('xpath', ''),
                            'id': item.get('id', ''),
                            'tag': item.get('tagName', 'button')
                        })
            
            self.pagination_elements = self.pagination_elements[:10]
            
            if self.pagination_elements:
                self._log(f"检测到 {len(self.pagination_elements)} 个翻页按钮")
            
            return self.pagination_elements
            
        except Exception as e:
            self._log(f"翻页检测异常: {e}", "error")
            return []
    
    def setup_pagination(self, xpath: str):
        """设置翻页按钮"""
        self.pagination_controller = PaginationController(self.tab)
        self.pagination_controller.set_next_button(xpath=xpath)
        self.config.pagination_xpath = xpath
    
    # ==================== 填充服务 ====================
    
    def set_config(
        self,
        fill_mode: str = "single_form",
        key_column: Optional[str] = None,
        pagination_mode: str = "manual"
    ):
        """设置填充配置"""
        self.config.fill_mode = fill_mode
        self.config.key_column = key_column
        self.config.pagination_mode = pagination_mode
    
    def set_mappings(self, mappings: Dict[str, ElementFingerprint]):
        """设置字段映射"""
        self.field_mapping = mappings
    
    def start_fill(self) -> threading.Thread:
        """
        启动填充任务（异步）
        
        Returns:
            工作线程
        """
        self.abort_event.clear()
        self.state = FillSessionState(is_running=True)
        
        thread = threading.Thread(target=self._execute_fill, daemon=True)
        thread.start()
        return thread
    
    def stop_fill(self):
        """停止填充任务"""
        self.abort_event.set()
        self._log("🛑 用户手动终止，正在保存进度...", "warning")
    
    def pause_fill(self):
        """暂停填充"""
        self.state.is_paused = True
        self.progress_manager.pause()
    
    def resume_fill(self) -> threading.Thread:
        """
        恢复填充
        
        Returns:
            工作线程
        """
        self.state.is_paused = False
        self.progress_manager.resume()
        
        thread = threading.Thread(target=self._execute_fill_continue, daemon=True)
        thread.start()
        return thread
    
    def resume_anchor_fill(self, matched_rows: List[dict] = None, 
                           key_column: str = None,
                           start_idx: int = None) -> threading.Thread:
        """
        恢复锚点模式填充
        
        Args:
            matched_rows: 匹配的行数据（如果为 None，使用 state 中保存的）
            key_column: 锚点列（如果为 None，使用 state 中保存的）
            start_idx: 起始索引（如果为 None，使用 state.current_row_idx）
            
        Returns:
            工作线程
        """
        # 使用传入的或 state 中保存的数据
        if matched_rows is not None:
            self.state.matched_rows = matched_rows
        if key_column is not None:
            self.state.anchor_key_column = key_column
        if start_idx is not None:
            self.state.current_row_idx = start_idx
            
        self.state.is_paused = False
        self.state.is_running = True
        
        def _do_anchor_fill():
            try:
                self._execute_anchor_fill(
                    self.state.matched_rows,
                    self.state.anchor_key_column,
                    self.config.fill_mode
                )
            finally:
                self.state.is_running = False
        
        thread = threading.Thread(target=_do_anchor_fill, daemon=True)
        thread.start()
        return thread
    
    def _execute_fill(self):
        """执行填充主逻辑 - 使用策略模式"""
        try:
            key_column = self.config.key_column
            
            # 初始化进度管理器
            effective_total = len(self.excel_data)
            self.progress_manager.start_new_session(
                excel_file="当前任务",
                total_rows=effective_total,
                anchor_column=key_column or ""
            )
            
            self._log(f"🚀 启动智能填表")
            self._log(f"   映射字段: {len(self.field_mapping)} 个")
            
            # 根据配置选择策略
            if key_column and key_column in self.field_mapping:
                # 锚点模式
                strategy = AnchorFillStrategy(self)
            else:
                # 普通模式
                strategy = NormalFillStrategy(self)
            
            # 执行策略
            strategy.execute()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._log(f"❌ 执行异常: {e}", "error")
        finally:
            self.state.is_running = False
    
    def _build_anchor_map(self, key_column: str) -> List[dict]:
        """构建锚点匹配映射"""
        self._log(f"⚓ 锚点模式：正在扫描网页锚点列...")
        
        anchor_fp = self.field_mapping[key_column]
        xpath = anchor_fp.selectors.get('xpath', '')
        
        if not xpath:
            self._log("锚点列没有有效的XPath", "error")
            return []
        
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
    
    def _execute_normal_fill(self, fill_mode: str, has_pagination: bool, is_auto_mode: bool):
        """执行普通模式填充"""
        total_rows = len(self.excel_data)
        current_row_idx = self.state.current_row_idx
        page_number = self.state.current_page
        
        while current_row_idx < total_rows:
            if self.abort_event.is_set():
                self._log("🛑 用户手动终止", "warning")
                break
            
            rows_on_page = self._count_rows_on_current_page()
            if rows_on_page == 0:
                rows_on_page = 5
            
            end_row_idx = min(current_row_idx + rows_on_page, total_rows)
            page_data = self.excel_data.iloc[current_row_idx:end_row_idx]
            
            self._log(f"📄 第 {page_number} 页: 填充第 {current_row_idx+1}-{end_row_idx} 行")
            self._progress(current_row_idx, total_rows, page_number)
            
            result = SmartFormFiller.fill_form_with_healing(
                tab=self.tab,
                excel_data=page_data.reset_index(drop=True),
                fingerprint_mappings=self.field_mapping,
                fill_mode=fill_mode,
                key_column=None,
                progress_callback=lambda c, t, m, s: self._log(m, s)
            )
            
            self.state.total_success += result['success']
            self.state.total_error += result['error']
            self.state.total_healed += result['healed']
            self.state.errors.extend(result['errors'])
            
            current_row_idx = end_row_idx
            
            if current_row_idx < total_rows:
                if has_pagination and is_auto_mode:
                    # 全自动翻页
                    page_turned = self.pagination_controller.click_next_page(wait_after=1.5)
                    if page_turned:
                        page_number += 1
                        self.pagination_controller.wait_for_page_ready(timeout=5)
                        self._log(f"✅ 已翻至第 {page_number} 页")
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
    
    def _execute_fill_continue(self):
        """继续填充 - 使用策略模式"""
        if self.config.key_column:
            strategy = AnchorFillStrategy(self)
        else:
            strategy = NormalFillStrategy(self)
        
        strategy.continue_fill()
    
    def _execute_anchor_page_fill(self):
        """锚点模式翻页后继续填充"""
        key_column = self.config.key_column
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
    
    def _count_rows_on_current_page(self) -> int:
        """检测当前页面的表格行数"""
        try:
            js = """
            (() => {
                let rows = document.querySelectorAll('table tbody tr');
                if (rows.length > 0) return rows.length;
                
                let inputGroups = document.querySelectorAll('.form-row, .data-row, [class*="row"]');
                if (inputGroups.length > 0) return inputGroups.length;
                
                let inputs = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
                return inputs.length;
            })();
            """
            result = self.tab.run_js(js)
            return int(result) if result else 5
        except:
            return 5
    
    def _complete_fill(self):
        """填充完成"""
        self.progress_manager.complete()
        self.state.is_running = False
        
        self._log("=" * 40)
        self._log("✅ 填表完成!", "success")
        self._log(f"   成功: {self.state.total_success} 行", "success")
        if self.state.total_error:
            self._log(f"   失败: {self.state.total_error} 行", "error")
        if self.state.total_healed > 0:
            self._log(f"   🩹 自动修复: {self.state.total_healed} 个", "success")
        self._log("=" * 40)
    
    # ==================== 工具方法 ====================
    
    def highlight_element(self, fingerprint: ElementFingerprint):
        """高亮显示元素"""
        id_selector = fingerprint.selectors.get('id', '')
        css_selector = fingerprint.selectors.get('css', '')
        xpath = fingerprint.selectors.get('xpath', '')
        elem_id = fingerprint.raw_data.get('id', '')
        shadow_depth = fingerprint.raw_data.get('shadow_depth', 0)
        shadow_host_id = fingerprint.raw_data.get('shadow_host_id', '')
        
        js_highlight = f"""
        (function() {{
            let el = null;
            
            function findInShadowDOM(hostSelector, targetSelector) {{
                try {{
                    const hosts = document.querySelectorAll('*');
                    for (let host of hosts) {{
                        if (host.shadowRoot) {{
                            let found = host.shadowRoot.querySelector('input, textarea, select');
                            if (found) return found;
                        }}
                    }}
                }} catch(e) {{}}
                return null;
            }}
            
            if ({shadow_depth} > 0) {{
                el = findInShadowDOM('{shadow_host_id}', 'input, textarea, select');
            }}
            
            if (!el && '{elem_id}') {{
                el = document.getElementById('{elem_id}');
            }}
            
            if (!el && '{id_selector}') {{
                try {{ el = document.querySelector('{id_selector}'); }} catch(e) {{}}
            }}
            
            if (!el && `{css_selector}`) {{
                try {{ el = document.querySelector(`{css_selector}`); }} catch(e) {{}}
            }}
            
            if (!el && `{xpath}`) {{
                try {{
                    let result = document.evaluate(`{xpath}`, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                    el = result.singleNodeValue;
                }} catch(e) {{}}
            }}
            
            if (el) {{
                el.scrollIntoView({{behavior: "smooth", block: "center"}});
                
                let originalBorder = el.style.border;
                let originalBg = el.style.backgroundColor;
                let originalOutline = el.style.outline;
                let originalBoxShadow = el.style.boxShadow;
                
                el.style.transition = 'all 0.15s ease-in-out';
                el.style.border = '1px solid #8E8E93';
                el.style.outline = '2px solid #636366';
                el.style.boxShadow = '0 0 0 4px rgba(99, 99, 102, 0.2)';
                el.style.backgroundColor = 'rgba(142, 142, 147, 0.12)';
                
                let count = 0;
                let flashInterval = setInterval(() => {{
                    if (count % 2 === 0) {{
                        el.style.backgroundColor = 'rgba(142, 142, 147, 0.15)';
                    }} else {{
                        el.style.backgroundColor = 'rgba(142, 142, 147, 0.08)';
                    }}
                    count++;
                    if (count >= 6) {{
                        clearInterval(flashInterval);
                        setTimeout(() => {{
                            el.style.border = originalBorder;
                            el.style.backgroundColor = originalBg;
                            el.style.outline = originalOutline;
                            el.style.boxShadow = originalBoxShadow;
                        }}, 300);
                    }}
                }}, 150);
                
                return true;
            }}
            return false;
        }})();
        """
        
        try:
            self.tab.run_js(js_highlight)
        except Exception as e:
            print(f"Highlight error: {e}")
