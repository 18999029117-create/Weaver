import subprocess
import os
from DrissionPage import ChromiumPage
from DrissionPage.common import ChromiumOptions

class BrowserLauncher:
    @staticmethod
    def launch_automated_browser():
        """
        启动一个带有 9222 端口的浏览器实例。
        使用用户临时目录作为数据目录，确保与用户日常浏览器隔离，不冲突。
        """
        co = ChromiumOptions()
        co.set_paths(local_port=9222)
        # 为自动化浏览器设置独立的存储空间，防止冲突
        user_data_path = os.path.join(os.getcwd(), "browser_profile")
        co.set_user_data_path(user_data_path)
        
        # 启动浏览器并返回页面对象
        page = ChromiumPage(addr_or_opts=co)
        return page
