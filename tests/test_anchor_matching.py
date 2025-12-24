"""
测试锚定匹配功能

验证:
1. AnchorConfig 数据结构
2. AnchorMatcher 自动匹配算法
3. 多重锚定匹配逻辑
"""

import sys
sys.path.insert(0, '.')

from app.domain.entities.anchor_config import AnchorConfig, AnchorPair, WebColumnInfo
from app.core.anchor_matcher import AnchorMatcher


def test_anchor_config():
    """测试 AnchorConfig 数据结构"""
    print("\n=== 测试 AnchorConfig 数据结构 ===")
    
    # 创建配置
    config = AnchorConfig()
    
    # 添加锚定对
    config.add_anchor_pair("医保编码", "//table/tr/td[1]", "医保编码")
    config.add_anchor_pair("物资名称", "//table/tr/td[2]", "物资名称")
    
    print(f"锚定配置: {config}")
    print(f"已启用锚定列: {config.anchor_count}")
    print(f"Excel 锚定列: {config.get_excel_anchor_columns()}")
    
    # 禁用一个
    config.toggle_anchor_pair(0)
    print(f"禁用第一个后: {config.anchor_count} 个启用")
    
    # 验证
    assert config.anchor_count == 1, "禁用后应该只有 1 个启用"
    print("✅ AnchorConfig 测试通过")


def test_similarity():
    """测试相似度算法"""
    print("\n=== 测试相似度算法 ===")
    
    test_cases = [
        ("医保编码", "医保编码", 1.0),
        ("物资名称", "物资名称", 1.0),
        ("消耗数量", "消耗量", 0.8),
        ("领用科室", "领用部门", 0.6),
        ("完全不相关", "ABC", 0.0),
    ]
    
    for s1, s2, expected_min in test_cases:
        score = AnchorMatcher.calculate_similarity(s1, s2)
        status = "✅" if score >= expected_min else "❌"
        print(f"  {status} '{s1}' vs '{s2}' = {score:.2f} (期望 >= {expected_min})")
    
    print("✅ 相似度算法测试完成")


def test_auto_match():
    """测试自动匹配"""
    print("\n=== 测试自动匹配 ===")
    
    # 模拟 Excel 列
    excel_columns = ["医保编码", "物资名称", "领用科室", "消耗数量", "备注"]
    
    # 模拟网页列
    web_columns = [
        WebColumnInfo(label="医保编码", xpath="//td[1]", is_readonly=True),
        WebColumnInfo(label="物资名称", xpath="//td[2]", is_readonly=True),
        WebColumnInfo(label="规格", xpath="//td[3]", is_readonly=True),
        WebColumnInfo(label="领用部门", xpath="//td[4]", is_readonly=True),
        WebColumnInfo(label="消耗数量", xpath="//input[1]", is_readonly=False, is_input=True),
        WebColumnInfo(label="备注", xpath="//input[2]", is_readonly=False, is_input=True),
    ]
    
    # 执行自动匹配
    config = AnchorMatcher.auto_match(excel_columns, web_columns)
    
    print(f"\n匹配结果:")
    print(f"  锚定列数量: {config.anchor_count}")
    print(f"  待填列数量: {len(config.fill_mappings)}")
    print(f"  置信度: {config.match_confidence:.0f}%")
    
    # 验证
    assert config.anchor_count >= 2, "应该至少匹配 2 个锚定列"
    assert len(config.fill_mappings) >= 1, "应该至少有 1 个待填列"
    
    print("✅ 自动匹配测试通过")


def test_validation():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    
    excel_columns = ["医保编码", "消耗数量"]
    web_columns = [WebColumnInfo(label="医保编码", xpath="//td[1]")]
    
    # 空配置
    empty_config = AnchorConfig()
    errors = AnchorMatcher.validate_anchor_config(empty_config, excel_columns, web_columns)
    print(f"  空配置错误: {errors}")
    assert len(errors) > 0, "空配置应该有错误"
    
    # 有效配置
    valid_config = AnchorConfig()
    valid_config.add_anchor_pair("医保编码", "//td[1]", "医保编码")
    valid_config.fill_mappings["消耗数量"] = {"web_label": "消耗数量"}
    
    errors = AnchorMatcher.validate_anchor_config(valid_config, excel_columns, web_columns)
    print(f"  有效配置错误: {errors}")
    assert len(errors) == 0, "有效配置不应该有错误"
    
    print("✅ 配置验证测试通过")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 锚定匹配功能单元测试")
    print("=" * 50)
    
    try:
        test_anchor_config()
        test_similarity()
        test_auto_match()
        test_validation()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
