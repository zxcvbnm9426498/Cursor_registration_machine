import requests
import time
import random
from colorama import Fore, Style

class ProxyManager:
    def __init__(self, secret_id=None, secret_key=None, translator=None):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.translator = translator
        self.proxy_list = []
        self.current_proxy = None
        self.last_fetch_time = 0
        self.fetch_interval = 1  # 获取IP的最小时间间隔（秒）

    def get_proxy(self):
        """获取代理IP"""
        try:
            # 检查是否需要重新获取代理列表
            if not self.proxy_list or time.time() - self.last_fetch_time >= self.fetch_interval:
                self._fetch_proxy_list()

            if self.proxy_list:
                self.current_proxy = self.proxy_list.pop(0)
                return self.current_proxy
            return None

        except Exception as e:
            print(f"{Fore.RED}❌ 获取代理IP失败: {str(e)}{Style.RESET_ALL}")
            return None

    def _fetch_proxy_list(self):
        """从快代理API获取代理IP列表"""
        try:
            if not self.secret_id or not self.secret_key:
                raise ValueError("SecretId和SecretKey不能为空")

            # 快代理API接口
            api_url = f"https://dps.kdlapi.com/api/getdps/?orderid={self.secret_id}&num=10&signature={self.secret_key}&format=json&sep=1"

            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data["code"] == 0:
                    self.proxy_list = data["data"]["proxy_list"]
                    self.last_fetch_time = time.time()
                    print(f"{Fore.GREEN}✅ 成功获取 {len(self.proxy_list)} 个代理IP{Style.RESET_ALL}")
                else:
                    raise Exception(f"API返回错误: {data['msg']}")
            else:
                raise Exception(f"API请求失败: {response.status_code}")

        except Exception as e:
            print(f"{Fore.RED}❌ 获取代理列表失败: {str(e)}{Style.RESET_ALL}")
            self.proxy_list = []

    def verify_proxy(self, proxy):
        """验证代理IP是否可用"""
        try:
            test_url = "https://authenticator.cursor.sh/"
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            response = requests.get(test_url, proxies=proxies, timeout=10)
            return response.status_code == 200
        except:
            return False

    def get_valid_proxy(self):
        """获取一个有效的代理IP"""
        max_attempts = 3
        for _ in range(max_attempts):
            proxy = self.get_proxy()
            if proxy and self.verify_proxy(proxy):
                return proxy
            time.sleep(1)
        return None