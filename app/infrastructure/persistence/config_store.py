"""
配置持久化适配器 - 基础设施层

负责保存和加载填表配置。
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigurationStore:
    """配置存储管理器"""
    
    DEFAULT_CONFIG_DIR = "configs"
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, self.DEFAULT_CONFIG_DIR)
        os.makedirs(self.config_dir, exist_ok=True)
    
    def save(self, name: str, config: Dict[str, Any]) -> str:
        """
        保存配置
        
        Args:
            name: 配置名称
            config: 配置字典
            
        Returns:
            保存的文件路径
        """
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.config_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2, default=str)
        
        return filepath
    
    def load(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        加载配置
        
        Args:
            filepath: 配置文件路径
            
        Returns:
            配置字典或 None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ConfigurationStore.load error: {e}")
            return None
    
    def list_configs(self) -> list:
        """列出所有配置文件"""
        configs = []
        for f in os.listdir(self.config_dir):
            if f.endswith('.json'):
                configs.append(os.path.join(self.config_dir, f))
        return sorted(configs, reverse=True)
    
    def get_latest(self, prefix: str = "") -> Optional[str]:
        """获取最新的配置文件路径"""
        configs = self.list_configs()
        for c in configs:
            if prefix in os.path.basename(c):
                return c
        return configs[0] if configs else None
