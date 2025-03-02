import argparse
import threading
import os
import json
from colorama import Fore, Style, init
from cursor_register import CursorRegistration
from reset_machine_manual import MachineIDResetter
from main import Translator
from proxy_manager import ProxyManager

# 初始化colorama
init()

# 定义emoji常量
EMOJI = {
    'START': '🚀',
    'FORM': '📝',
    'VERIFY': '🔄',
    'PASSWORD': '🔑',
    'CODE': '📱',
    'DONE': '✨',
    'ERROR': '❌',
    'WAIT': '⏳',
    'SUCCESS': '✅',
    'MAIL': '📧',
    'KEY': '🔐',
    'UPDATE': '🔄',
    'INFO': 'ℹ️'
}

class BatchRegistration:
    def __init__(self, thread_count=1, proxy=None, api_key=None, order_id=None, translator=None):
        self.thread_count = thread_count
        self.proxy = proxy
        self.api_key = api_key
        self.order_id = order_id
        self.translator = translator
        self.stop_event = threading.Event()
        self.threads = []
        self.proxy_manager = None
        
        # 如果提供了API密钥和订单号，初始化代理管理器
        if api_key and order_id:
            self.proxy_manager = ProxyManager(api_key, order_id, translator)

    def reset_machine_id(self):
        """重置机器码"""
        try:
            resetter = MachineIDResetter(self.translator)
            resetter.reset_machine_ids()
            return True
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} 重置机器码失败: {e}{Style.RESET_ALL}")
            return False

    def registration_thread(self):
        """注册线程"""
        while not self.stop_event.is_set():
            try:
                current_proxy = None
                
                # 优先使用代理管理器获取代理
                if self.proxy_manager:
                    current_proxy = self.proxy_manager.get_valid_proxy()
                    if current_proxy:
                        print(f"{Fore.CYAN}{EMOJI['INFO']} 使用快代理IP: {current_proxy}{Style.RESET_ALL}")
                # 如果没有代理管理器或获取失败，使用手动指定的代理
                elif self.proxy:
                    current_proxy = self.proxy
                    print(f"{Fore.CYAN}{EMOJI['INFO']} 使用手动指定代理: {current_proxy}{Style.RESET_ALL}")
                
                # 设置代理环境变量
                if current_proxy:
                    os.environ['HTTP_PROXY'] = f'http://{current_proxy}'
                    os.environ['HTTPS_PROXY'] = f'http://{current_proxy}'
                else:
                    # 清除代理环境变量
                    if 'HTTP_PROXY' in os.environ:
                        del os.environ['HTTP_PROXY']
                    if 'HTTPS_PROXY' in os.environ:
                        del os.environ['HTTPS_PROXY']

                registration = CursorRegistration(self.translator, current_proxy)
                registration.start()

            except Exception as e:
                print(f"{Fore.RED}{EMOJI['ERROR']} 注册过程出错: {e}{Style.RESET_ALL}")

            if self.stop_event.is_set():
                break

    def start(self):
        """启动批量注册"""
        print(f"{Fore.CYAN}{EMOJI['START']} 开始批量注册任务...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['INFO']} 线程数量: {self.thread_count}{Style.RESET_ALL}")
        
        if self.proxy_manager:
            print(f"{Fore.CYAN}{EMOJI['INFO']} 使用快代理API动态获取代理IP{Style.RESET_ALL}")
        elif self.proxy:
            print(f"{Fore.CYAN}{EMOJI['INFO']} 使用固定代理: {self.proxy}{Style.RESET_ALL}")

        try:
            # 启动注册线程
            for _ in range(self.thread_count):
                thread = threading.Thread(target=self.registration_thread, daemon=True)
                self.threads.append(thread)
                thread.start()

            # 等待用户输入q退出
            print(f"\n{Fore.YELLOW}{EMOJI['INFO']} 按下 'q' 并回车可以停止注册任务{Style.RESET_ALL}")
            while True:
                try:
                    if input().lower() == 'q':
                        break
                except KeyboardInterrupt:
                    break

            # 停止所有线程
            self.stop_event.set()
            print(f"\n{Fore.YELLOW}{EMOJI['INFO']} 正在停止所有注册任务...{Style.RESET_ALL}")
            
            # 等待所有线程结束
            for thread in self.threads:
                thread.join()

            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} 所有注册任务已停止{Style.RESET_ALL}")

        except Exception as e:
            self.stop_event.set()
            print(f"\n{Fore.RED}{EMOJI['ERROR']} 发生错误: {e}{Style.RESET_ALL}")
            for thread in self.threads:
                thread.join()
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} 所有注册任务已停止{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description='Cursor批量注册工具')
    parser.add_argument('-t', '--threads', type=int, default=1, help='注册线程数量')
    parser.add_argument('-p', '--proxy', type=str, help='代理服务器地址 (格式: ip:port)')
    parser.add_argument('-r', '--reset', action='store_true', help='重置机器码')
    parser.add_argument('-k', '--api-key', type=str, help='快代理API密钥')
    parser.add_argument('-o', '--order-id', type=str, help='快代理订单号')
    parser.add_argument('-c', '--config', type=str, help='配置文件路径')
    
    args = parser.parse_args()
    
    # 创建翻译器实例
    translator = Translator()
    
    # 从配置文件加载API密钥和订单号
    api_key = args.api_key
    order_id = args.order_id
    
    if args.config and not (api_key and order_id):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get('api_key')
                order_id = config.get('order_id')
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} 从配置文件加载API信息成功{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} 加载配置文件失败: {e}{Style.RESET_ALL}")
    
    # 如果指定了重置参数，先重置机器码
    if args.reset:
        resetter = MachineIDResetter(translator)
        resetter.reset_machine_ids()
    
    # 创建批量注册实例并启动
    batch = BatchRegistration(args.threads, args.proxy, api_key, order_id, translator)
    batch.start()

if __name__ == '__main__':
    main()