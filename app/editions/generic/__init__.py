"""
通用版本

默认版本，不做任何定制，使用所有默认行为。
"""

from app.editions.base_edition import BaseEdition


class GenericEdition(BaseEdition):
    """
    通用版本
    
    继承基类的所有默认行为，不做任何修改。
    """
    
    name = "通用版本"
    icon = "🌐"
    description = "适用于所有用户的标准功能"
