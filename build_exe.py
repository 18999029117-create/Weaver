
import PyInstaller.__main__
import os

print("🚀 开始构建 Weaver_Kuche_v5.0.exe ...")

# 1. 配置参数
params = [
    'main.py',
    '--name=Weaver_Kuche_v5.0_Ultra',       # 终极版
    '--onefile',
    '--noconsole',
    '--add-data=element_selectors.json;.',  # 包含配置文件
    '--add-data=app;app',                   # 【核弹修复】包含完整 app 源码，解决一切 import 问题
    '--collect-all=customtkinter',          # 收集 ctk 资源
    '--collect-all=DrissionPage',           # 收集 DrissionPage 资源 (修复自动化失效)
    '--hidden-import=pandas',
    '--hidden-import=openpyxl',
    '--hidden-import=PIL._tkinter_finder',
    # 显式导入动态加载的版本模块
    '--hidden-import=app.editions.generic',
    '--hidden-import=app.editions.kuche_hospital',
    # 显式导入库车定制版的所有依赖模块（防止分析遗漏）
    '--hidden-import=app.customizations.kuche_hospital.element_loader',
    '--hidden-import=app.customizations.kuche_hospital.consumable_processor',
    '--hidden-import=app.customizations.kuche_hospital.start_dialog',
    '--clean',
    '--distpath=dist',
    '--workpath=build',
    '--specpath=.',
    '--noconfirm',
]

# 2. 执行构建
PyInstaller.__main__.run(params)

print("✅ 构建完成！文件位于 dist/Weaver_Kuche_v5.0.exe")
