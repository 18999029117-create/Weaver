# Weaver (维沃) - 智能网页自动化填表工具

![Version](https://img.shields.io/badge/version-v1.0_Beta-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)

Weaver 是一个现代化的、智能的网页自动化填表工具，旨在帮助用户将 Excel 数据高效、准确地录入到各种网页表单中。它结合了视觉识别、智能模糊匹配和自愈技术，让自动化任务配置变得简单直观。

---

## ✨ 核心特性

- **🧠 智能字段匹配**：自动分析网页表单结构，将其与 Excel 列头进行模糊匹配，减少 90% 的手动配置工作。
- **🔌 可视化映射连线**：提供直观的 "连连看" 界面，通过拖拽即可建立数据与表单的映射关系。
- **🛡️ 填表自愈机制**：当网页微调（如 ID 变化、布局微调）时，系统能根据元素指纹自动寻找新的定位方式，无需修改代码。
- **⚓ 锚点行级定位**：支持在复杂的动态表格中，根据特定列（如"姓名"）定位到正确的一行进行操作。
- **⏯️ 断点续传**：任务支持随时暂停，或在异常中断后从断点处（精确到行）恢复执行。
- **📄 智能分页处理**：自动处理表格翻页，支持"下一页"按钮的自动识别和点击。

---

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8 或更高版本。

```bash
# 克隆项目 (或下载源码)
git clone [your-repo-url]
cd weaver

# 创建虚拟环境 (可选)
python -m venv venv
# Windows 激活
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python main.py
```

---

## 📖 使用指南

1.  **加载数据**：在主页点击 "选择文件"，加载包含数据的 Excel 文件 (`.xlsx`, `.xls`, `.csv`)。
2.  **准备环境**：软件会自动打开 Chrome 浏览器，请导航到需要填写的网页（如登录系统、打开表单页）。
3.  **扫描网页**：点击工作台的 "重新扫描" 按钮，系统将分析当前网页结构。
4.  **建立映射**：
    *   系统会自动尝试匹配 Excel 列与网页字段。
    *   在中间的画布区域，手动拖拽连线调整映射关系。
5.  **配置规则**：
    *   **录入模式**：选择 "单条录入" (提交后跳回) 或 "表格批量" (在同一页填多行)。
    *   **锚点规则**：如果是表格录入，选择用于定位行的 Excel 列（Key Column）。
6.  **开始运行**：点击 "启动"，观察自动化执行过程。

---

## 📂 目录结构

```
Weaver/
├── app/                  # 源代码目录
│   ├── application/      # 业务流程控制
│   ├── core/             # 核心算法 (AI 匹配, 填充引擎)
│   ├── domain/           # 实体定义
│   ├── infrastructure/   # 基础设施 (Excel, 配置 IO)
│   └── ui/               # 用户界面 (CustomTkinter)
├── main.py               # 启动入口
├── requirements.txt      # 项目依赖
└── PROJECT_DOCS.md       # 详细开发文档
```

## 🛠️ 技术栈

*   **UI 框架**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
*   **浏览器自动化**: [DrissionPage](https://g1879.gitee.io/drissionpagedocs/)
*   **数据处理**: Pandas, OpenPyXL
*   **打包工具**: PyInstaller

## 📄 许可证

[MIT License](LICENSE)
