"""
版本注册表

所有定制版本在此注册，启动时根据用户选择加载对应版本。
"""

from typing import Dict, List, Type, Optional
from app.editions.base_edition import BaseEdition


# ============================================================
# 版本注册表
# ============================================================

EDITIONS: Dict[str, Dict] = {
    "generic": {
        "name": "通用版本",
        "icon": "🌐",
        "description": "适用于所有用户的标准功能",
        "module": "app.editions.generic",
        "class": "GenericEdition",
    },
    "kuche_hospital": {
        "name": "库车市人民医院",
        "icon": "🏥",
        "description": "库车市人民医院专属定制功能",
        "module": "app.editions.kuche_hospital",
        "class": "KucheHospitalEdition",
    },
    # ========== 添加新客户在此处 ==========
    # "new_customer": {
    #     "name": "新客户名称",
    #     "icon": "🏢",
    #     "description": "新客户描述",
    #     "module": "app.editions.new_customer",
    #     "class": "NewCustomerEdition",
    # },
}


def get_edition_names() -> List[str]:
    """
    获取所有已注册版本的 ID 列表
    
    Returns:
        版本 ID 列表
    """
    return list(EDITIONS.keys())


def get_edition_info(edition_id: str) -> Optional[Dict]:
    """
    获取版本信息
    
    Args:
        edition_id: 版本 ID
        
    Returns:
        版本信息字典，不存在返回 None
    """
    return EDITIONS.get(edition_id)


def get_edition(edition_id: str) -> BaseEdition:
    """
    动态加载并实例化指定版本
    
    Args:
        edition_id: 版本 ID (如 "generic", "kuche_hospital")
        
    Returns:
        版本实例
        
    Raises:
        ValueError: 版本不存在
        ImportError: 模块加载失败
    """
    if edition_id not in EDITIONS:
        raise ValueError(f"版本 '{edition_id}' 未注册")
    
    info = EDITIONS[edition_id]
    module_path = info["module"]
    class_name = info["class"]
    
    try:
        # 动态导入模块
        import importlib
        module = importlib.import_module(module_path)
        
        # 获取版本类
        edition_class = getattr(module, class_name)
        
        # 实例化并返回
        return edition_class()
        
    except ImportError as e:
        print(f"[Registry] 加载版本模块失败: {module_path} - {e}")
        # 回退到通用版本
        from app.editions.generic import GenericEdition
        return GenericEdition()
    except AttributeError as e:
        print(f"[Registry] 版本类不存在: {class_name} - {e}")
        from app.editions.generic import GenericEdition
        return GenericEdition()
