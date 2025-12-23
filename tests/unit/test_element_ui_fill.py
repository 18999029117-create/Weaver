"""
Element UI + Vue 填充测试脚本
针对 https://tps.xjylbz.cn 政府级平台测试
"""

from DrissionPage import ChromiumPage
from app.core.smart_form_filler import SmartFormFiller
from app.core.smart_form_analyzer import SmartFormAnalyzer

def test_element_ui_fill():
    """测试 Element UI 填充功能"""
    
    print("=" * 60)
    print("🧪 Element UI + Vue 双向绑定填充测试")
    print("=" * 60)
    
    try:
        # 连接到已打开的 Chrome
        page = ChromiumPage()
        tab = page.latest_tab
        
        print(f"\n📍 当前页面: {tab.url}")
        
        # ===== 测试1: 扫描页面（包含 iframe）=====
        print("\n--- 测试1: 扫描页面元素（含 Iframe 穿透）---")
        fingerprints = SmartFormAnalyzer.deep_scan_page(tab)
        print(f"✅ 扫描到 {len(fingerprints)} 个元素")
        
        # 打印前5个元素信息
        for i, fp in enumerate(fingerprints[:5]):
            print(f"   {i+1}. {fp.get_display_name()} | frame: {fp.frame_info.get('in_iframe', False)}")
        
        if len(fingerprints) > 5:
            print(f"   ... 还有 {len(fingerprints) - 5} 个元素")
        
        # ===== 测试2: 使用 placeholder 填充 =====
        print("\n--- 测试2: fill_element_ui_input (placeholder 定位) ---")
        
        # 常见的 Element UI 输入框 placeholder
        test_cases = [
            ("请输入", "测试值123"),
            ("搜索", "测试搜索"),
        ]
        
        for placeholder, value in test_cases:
            print(f"\n尝试填充: placeholder='{placeholder}' value='{value}'")
            result = SmartFormFiller.fill_element_ui_input(tab, placeholder, value)
            print(f"结果: {'✅ 成功' if result else '❌ 失败'}")
        
        # ===== 测试3: 使用标签文本填充 =====
        print("\n--- 测试3: fill_element_ui_by_label (标签文本定位) ---")
        
        label_test_cases = [
            ("医疗机构名称", "测试医院"),
            ("身份证号", "650101199001011234"),
        ]
        
        for label, value in label_test_cases:
            print(f"\n尝试填充: label='{label}' value='{value}'")
            result = SmartFormFiller.fill_element_ui_by_label(tab, label, value)
            print(f"结果: {'✅ 成功' if result else '❌ 失败'}")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_element_ui_fill()
