from DrissionPage import ChromiumOptions, ChromiumPage
import sys
import os
import logging
import random


# 全局浏览器实例列表，用于跟踪所有活动的浏览器实例
_active_browsers = []

class BrowserManager:
    def __init__(self, noheader=False, proxy=None):
        self.browser = None
        self.noheader = noheader
        self.proxy = proxy
        self._browser_initialized = False

    def init_browser(self):
        """初始化浏览器"""
        if self._browser_initialized:
            return self.browser
            
        co = self._get_browser_options()
        
        # 如果设置了 noheader，添加相应的参数
        if self.noheader:
            co.set_argument('--headless=new')
            co.set_argument('--disable-gpu')
            co.set_argument('--no-sandbox')
            co.set_argument('--disable-dev-shm-usage')
            co.set_argument('--disable-extensions')  # 禁用扩展以提高稳定性
            co.set_argument('--disable-software-rasterizer')
            co.set_argument('--disable-dev-shm')
            co.set_argument('--disable-setuid-sandbox')
            co.set_argument('--single-process')
            co.set_argument('--ignore-certificate-errors')
            co.set_argument('--window-size=1920,1080')
            
        # 如果设置了代理，添加代理配置
        if self.proxy:
            co.set_proxy(f"http://{self.proxy}")
            
        self.browser = ChromiumPage(co)
        self._browser_initialized = True
        _active_browsers.append(self.browser)
        return self.browser

    def _get_browser_options(self):
        """获取浏览器配置"""
        co = ChromiumOptions()
        try:
            extension_path = self._get_extension_path()
            co.add_extension(extension_path)
            co.set_argument("--allow-extensions-in-incognito")

            extension_block_path = self.get_extension_block()
            co.add_extension(extension_block_path)
            co.set_argument("--allow-extensions-in-incognito")
        except FileNotFoundError as e:
            logging.warning(f"警告: {e}")

        # 设置更真实的用户代理
        co.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 基本设置
        co.set_pref("credentials_enable_service", False)
        
        # 随机端口
        co.auto_port()

        # 系统特定设置
        if sys.platform == "darwin":  # macOS
            co.set_argument("--disable-gpu")
            co.set_argument("--no-sandbox")
        elif sys.platform == "win32":  # Windows
            co.set_argument("--disable-software-rasterizer")

        # 设置窗口大小
        window_width = random.randint(1024, 1920)
        window_height = random.randint(768, 1080)
        co.set_argument(f"--window-size={window_width},{window_height}")

        return co

    def _get_extension_path(self):
        """获取插件路径"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "turnstilePatch")

        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "turnstilePatch")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")

        return extension_path
    
    def get_extension_block(self):
        """获取插件路径"""
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, "PBlock")
        
        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, "PBlock")

        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")

        return extension_path

    def quit(self):
        """关闭浏览器"""
        if self.browser:
            try:
                self.browser.quit()
                if self.browser in _active_browsers:
                    _active_browsers.remove(self.browser)
            except:
                pass
            finally:
                self.browser = None
                self._browser_initialized = False

    @staticmethod
    def quit_all_browsers():
        """关闭所有活动的浏览器实例"""
        for browser in _active_browsers.copy():
            try:
                browser.quit()
                _active_browsers.remove(browser)
            except:
                pass
        _active_browsers.clear()