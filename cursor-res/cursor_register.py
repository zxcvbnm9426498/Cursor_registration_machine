import os
from colorama import Fore, Style, init
import time
import random
import traceback
import threading
from browser import BrowserManager
from control import BrowserControl
from cursor_auth import CursorAuth
from reset_machine_manual import MachineIDResetter
import datetime

os.environ["PYTHONVERBOSE"] = "0"
os.environ["PYINSTALLER_VERBOSE"] = "0"

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

# 定义表情符号字典
EMOJI = {
    'START': '🚀',
    'SUCCESS': '✅',
    'ERROR': '❌',
    'WAIT': '⏳',
    'INFO': 'ℹ️',
    'KEY': '🔑',
    'CODE': '📝',
    'UPDATE': '🔄',
    'DONE': '🎉'
}

class CursorRegistration:
    def __init__(self, translator=None, proxy=None, headless=False):
        self.translator = translator
        self.proxy = proxy
        self.headless = headless
        # 根据 headless 参数设置浏览器模式
        os.environ['BROWSER_HEADLESS'] = str(headless)
        # 确保无头模式参数正确传递
        self.browser_manager = BrowserManager(noheader=headless, proxy=self.proxy)
        self.browser = None
        self.controller = None
        self.mail_url = "https://yopmail.com/zh/email-generator"
        self.sign_up_url = "https://authenticator.cursor.sh/sign-up"
        self.settings_url = "https://www.cursor.com/settings"
        self.email_address = None
        self.signup_tab = None
        self.email_tab = None
        self.EMOJI = EMOJI  # 添加EMOJI属性
        
        # 账号信息
        self.password = self._generate_password()
        self.first_name = self._generate_name()
        self.last_name = self._generate_name()
        print(f"Password: {self.password}\n")
        print(f"First Name: {self.first_name}\n")
        print(f"Last Name: {self.last_name}\n")

    def _generate_password(self, length=12):
        """Generate Random Password"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(random.choices(chars, k=length))

    def _generate_name(self, length=6):
        """Generate Random Name"""
        first_letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        rest_letters = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=length-1))
        return first_letter + rest_letters

    def setup_email(self):
        """设置邮箱"""
        try:
            print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.browser_start')}...{Style.RESET_ALL}")
            
            # 使用 new_tempemail 创建临时邮箱，传入 translator
            from new_tempemail import NewTempEmail
            self.temp_email = NewTempEmail(self.translator)  # 传入 translator
            
            # 创建临时邮箱
            email_address = self.temp_email.create_email()
            if not email_address:
                print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.email_create_failed')}{Style.RESET_ALL}")
                return False
            
            # 保存邮箱地址
            self.email_address = email_address
            print(f"Email Address: {self.email_address}\n")
            self.email_tab = self.temp_email  # 传递 NewTempEmail 实例
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.email_setup_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def register_cursor(self):
        """注册 Cursor"""
        browser_tab = None
        try:
            print(f"{Fore.CYAN}{EMOJI['START']} {self.translator.get('register.register_start')}...{Style.RESET_ALL}")
            
            # 直接使用 new_signup.py 进行注册
            from new_signup import main as new_signup_main
            
            # 执行新的注册流程，传入 translator
            result, browser_tab = new_signup_main(
                email=self.email_address,
                password=self.password,
                first_name=self.first_name,
                last_name=self.last_name,
                email_tab=self.email_tab,
                controller=self.controller,
                translator=self.translator
            )
            
            if result:
                # 使用返回的浏览器实例获取账户信息
                self.signup_tab = browser_tab  # 保存浏览器实例
                success = self._get_account_info()
                
                # 获取信息后关闭浏览器
                if browser_tab:
                    try:
                        browser_tab.quit()
                    except:
                        pass
                
                return success
            
            return False
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.register_process_error', error=str(e))}{Style.RESET_ALL}")
            return False
        finally:
            # 确保在任何情况下都关闭浏览器
            if browser_tab:
                try:
                    browser_tab.quit()
                except:
                    pass
                
    def _get_account_info(self):
        """获取账户信息和 Token"""
        try:
            self.signup_tab.get(self.settings_url)
            time.sleep(2)
            
            usage_selector = (
                "css:div.col-span-2 > div > div > div > div > "
                "div:nth-child(1) > div.flex.items-center.justify-between.gap-2 > "
                "span.font-mono.text-sm\/\[0\.875rem\]"
            )
            usage_ele = self.signup_tab.ele(usage_selector)
            total_usage = "未知"
            if usage_ele:
                total_usage = usage_ele.text.split("/")[-1].strip()

            print(f"Total Usage: {total_usage}\n")
            print(f"{Fore.CYAN}{EMOJI['WAIT']} {self.translator.get('register.get_token')}...{Style.RESET_ALL}")
            max_attempts = 30
            retry_interval = 2
            attempts = 0

            while attempts < max_attempts:
                try:
                    cookies = self.signup_tab.cookies()
                    for cookie in cookies:
                        if cookie.get("name") == "WorkosCursorSessionToken":
                            token = cookie["value"].split("%3A%3A")[1]
                            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('register.token_success')}{Style.RESET_ALL}")
                            self._save_account_info(token, total_usage)
                            return True

                    attempts += 1
                    if attempts < max_attempts:
                        print(f"{Fore.YELLOW}{EMOJI['WAIT']} {self.translator.get('register.token_attempt', attempt=attempts, time=retry_interval)}{Style.RESET_ALL}")
                        time.sleep(retry_interval)
                    else:
                        print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.token_max_attempts', max=max_attempts)}{Style.RESET_ALL}")

                except Exception as e:
                    print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.token_failed', error=str(e))}{Style.RESET_ALL}")
                    attempts += 1
                    if attempts < max_attempts:
                        print(f"{Fore.YELLOW}{EMOJI['WAIT']} {self.translator.get('register.token_attempt', attempt=attempts, time=retry_interval)}{Style.RESET_ALL}")
                        time.sleep(retry_interval)

            return False

        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.account_error', error=str(e))}{Style.RESET_ALL}")
            return False

    def _save_account_info(self, token, total_usage):
        """保存账户信息到文件"""
        try:
            # 保存账户信息到文件，使用-------分隔每组账号
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open('cursor_accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"Email: {self.email_address}\n")
                f.write(f"Password: {self.password}\n")
                f.write(f"Token: {token}\n")
                f.write(f"Usage Limit: {total_usage}\n")
                f.write(f"Register Time: {current_time}\n")
                f.write("-------\n")
                
            print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {self.translator.get('register.account_info_saved')}...{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} {self.translator.get('register.save_account_info_failed', error=str(e))}{Style.RESET_ALL}")
            return False

    def start(self):
        """启动注册流程"""
        try:
            # 检查是否有停止信号
            if hasattr(threading, 'current_thread') and hasattr(threading.current_thread(), '_stop_event') and threading.current_thread()._stop_event.is_set():
                return False
                
            if self.setup_email():
                if self.register_cursor():
                    print(f"\n{Fore.GREEN}{EMOJI['DONE']} {self.translator.get('register.cursor_registration_completed')}...{Style.RESET_ALL}")
                    return True
            return False
        except Exception as e:
            print(f"{Fore.RED}{EMOJI['ERROR']} 注册过程中断: {str(e)}{Style.RESET_ALL}")
            return False
        finally:
            # 关闭邮箱标签页
            if hasattr(self, 'temp_email'):
                try:
                    self.temp_email.close()
                except:
                    pass
            # 确保所有浏览器实例都被关闭
            if self.browser_manager and hasattr(self.browser_manager, 'quit'):
                self.browser_manager.quit()

def main(translator=None):
    """Main function to be called from main.py"""
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['START']} {translator.get('register.title')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    registration = CursorRegistration(translator)
    registration.start()

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {translator.get('register.press_enter')}...")

if __name__ == "__main__":
    from main import translator as main_translator
    main(main_translator)