import os
from datetime import datetime
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

def save_target_page():
    """
    交互式网页保存工具
    
    功能：
    1. 启动浏览器
    2. 等待用户手动操作（如登录、跳转）
    3. 一键保存当前网页的完整 HTML 结构（包含 JS 渲染后的内容）
    """
    
    # 1. 配置浏览器路径 (如有需要可修改，默认自动寻找)
    co = ChromiumOptions()
    # co.set_browser_path(r'C:\Program Files\Google\Chrome\Application\chrome.exe') # 如果找不到浏览器，取消注释并修改路径
    
    print("🚀 正在启动浏览器...")
    page = ChromiumPage(co)
    
    # 2. 询问用户要访问的地址
    url = input("请输入你要分析的网页地址 (直接回车则打开空白页): ").strip()
    if url:
        page.get(url)
    
    print("\n" + "="*50)
    print("✋ 请在弹出的浏览器中进行操作：")
    print("1. 输入账号密码登录")
    print("2. 跳转到你需要分析的【耗材录入】或【表格】页面")
    print("3. 等页面完全加载出来后，回到这里")
    print("="*50 + "\n")
    
    input("👉 准备好保存了吗？请按【回车键】开始保存...")

    # 3. 获取页面信息
    title = page.title
    # 清理文件名中的非法字符
    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
    if not safe_title:
        safe_title = "unknown_page"
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 4. 创建保存目录
    save_dir = Path("saved_pages")
    save_dir.mkdir(exist_ok=True)
    
    file_name = f"{safe_title}_{timestamp}.html"
    file_path = save_dir / file_name

    # 5. 保存 HTML
    # 注意：page.html 获取的是经过 JS 渲染后的“真实”DOM结构，正是自动化填表需要的
    print(f"⏳ 正在抓取代码...")
    html_content = page.html
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"\n✅ 成功保存！")
    print(f"📂 文件路径: {file_path.absolute()}")
    print(f"📊 字符长度: {len(html_content)}")
    print("\n你可以用 VS Code 打开这个文件，分析里面的 id, class 和 xpath 了。")

if __name__ == "__main__":
    try:
        save_target_page()
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        # input("按回车键退出...") # 如果想保留窗口，取消注释
        pass