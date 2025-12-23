# Weaver (维沃) 智能填表工作台 - 项目开发文档

> 版本: v1.0 Beta
> 更新日期: 2025-12-23

## 1. 项目概述

**Weaver (维沃)** 是一款基于 Python 的高性能、Agentic（代理式）网页自动化填表工具。它旨在解决传统 RPA 工具配置繁琐、脆性高的问题，通过**智能视觉匹配**和**自愈机制**，实现“Excel 到 网页”的无缝数据流转。

### 核心价值
*   **低代码/零代码**：通过可视化连线即可完成字段映射，无需编写选择器。
*   **高鲁棒性**：内置自愈机制，当网页结构微调时能自动寻找替代定位策略。
*   **断点续传**：支持长任务的暂停、恢复和异常后的进度保存。
*   **智能锚点**：支持基于行内特定文本（锚点）的复杂表格填充。

---

## 2. 系统架构

项目采用分层架构设计，实现了 UI 与业务逻辑的解耦，便于维护和扩展。

```mermaid
graph TD
    UI[UI Layer (Presentation)] --> App[Application Layer (Orchestration)]
    App --> Domain[Domain/Core Layer (Business Logic)]
    App --> Infra[Infrastructure Layer (Data/IO)]
    
    subgraph UI Layer
        MainWindow
        ProcessWindow
        MappingCanvas
        Components[Toolbar, Dialogs]
    end
    
    subgraph Application Layer
        FillSessionController
        PaginationController
    end
    
    subgraph Domain Layer
        SmartMatcher
        SmartFormFiller
        SmartFormAnalyzer
        ElementFingerprint
    end
    
    subgraph Infrastructure Layer
        ExcelAdapter
        ConfigStore
        DrissionPageDriver
    end
```

### 2.1 目录结构

```
app/
├── application/       # 应用层：协调器、控制器
│   └── orchestrator/  # 填充会话管理 (FillSessionController)
├── core/              # 核心业务逻辑
│   ├── smart_matcher.py       # 智能匹配算法
│   ├── smart_form_filler.py   # 填充执行引擎
│   └── smart_form_analyzer.py # 网页结构分析
├── domain/            # 领域实体
│   └── entities/      # 元素指纹 (ElementFingerprint) 等
├── infrastructure/    # 基础设施
│   ├── excel/         # Excel 文件处理
│   └── persistence/   # 配置持久化
└── ui/                # 用户界面 (CustomTkinter)
    ├── components/    # 通用组件 (Toolbar, Buttons)
    ├── dialogs/       # 对话框
    ├── main_window.py # 首页/文件选择
    ├── process_window.py # 核心工作台
    └── mapping_canvas.py # 可视化映射画布
```

---

## 3. 核心模块详解

### 3.1 UI 层 (User Interface)
基于 `CustomTkinter` 构建，提供现代化的深色模式界面。
*   **ProcessWindow**: 核心工作台，经过激进精简（Phase 4），目前主要负责 UI 状态展示，核心逻辑已委托给 Agent 层。
*   **MappingCanvas**: 创新的可视化映射界面。左侧为 Excel 列，右侧为网页元素，中间通过贝塞尔曲线连接。支持拖拽连线和自动吸附。
*   **ProcessToolbar**: 独立封装的工具栏组件，管理操作按钮和模式选择。

### 3.2 应用层 (Application Layer)
*   **FillSessionController**: 填充会话的大脑。管理填充状态（暂停/运行/恢复）、进度统计、错误处理，并协调 Matcher 和 Filler 工作。
*   **PaginationController**: 负责处理多页数据填充时的翻页逻辑（自动/手动模式）。

### 3.3 领域核心层 (Core Domain)
*   **SmartFormAnalyzer**: 使用 JS 注入和 DOM 分析技术，提取网页表单元素的“指纹”（Label, Placeholder, Name, ID, XPath 等）。
*   **SmartMatcher**: 使用模糊匹配算法（Levenshtein Distance 等）自动关联 Excel 列头和网页表单标签。
*   **SmartFormFiller**: 执行具体的填充动作。包含“自愈”逻辑：如果首选选择器失败，尝试使用指纹中的备选特征重新定位元素。
*   **ElementFingerprint**: 核心数据结构，存储元素的特征集合，用于跨页面、跨会话的元素重定位。

### 3.4 基础设施层 (Infrastructure)
*   **ExcelAdapter**: 封装 Pandas 操作，处理 Excel 数据的读取、列计算（GroupBy/Transform）和清理。
*   **ConfigStore**: JSON 格式的配置存储，保存字段映射关系，支持配置的导入导出。

---

## 4. 关键技术特性

### 4.1 智能填表与自愈 (Self-Healing)
系统不依赖单一的 XPath 或 CSS Selector。在扫描阶段，系统会捕获元素的多个特征（Label 文本、相对位置、属性等）。
当执行填充时，如果在原路径找不到元素，系统会根据 Label 或邻近元素关系重新搜索，从而适应网页的小幅改动。

### 4.2 锚点行级填充 (Anchor Row Filling)
针对复杂的动态表格（如每一行有一个“操作”按钮或一组输入框），系统支持“锚点模式”：
1.  用户指定 Excel 中的某一列作为 Key（如“姓名”）。
2.  系统在网页表格中寻找包含该 Key 值的行。
3.  系统利用相对 XPath (`//tr[contains(., 'Key')]//input`) 定位该行内的特定输入框进行填充。

### 4.3 激进 UI 精简与架构重构 (Recent Refactoring)
为了提高代码可维护性，项目近期进行了大规模重构：
*   **ProcessWindow 瘦身**：从 1800+ 行 减少至 ~770 行。
*   **逻辑下沉**：将填充循环、状态管理、分页逻辑从 UI 文件移至 `FillSessionController`。
*   **组件化**：提取了 `Toolbar` 和 `ColumnComputerDialog` 等独立组件。

---

## 5. 开发指南

### 环境依赖
*   Python 3.8+
*   依赖库：`customtkinter`, `drissionpage`, `pandas`, `openpyxl`, `pillow`
*   详情见 `requirements.txt`

### 运行方式
```bash
python main.py
```

### 调试建议
*   日志系统会输出到 UI 的日志面板，同时在控制台有详细的 Debug 信息。
*   使用 `FillSessionController` 的 `resume_fill` 方法可以测试断点恢复逻辑。
