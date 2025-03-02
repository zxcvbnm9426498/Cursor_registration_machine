import tkinter as tk
from tkinter import ttk, scrolledtext, BooleanVar, IntVar, StringVar, filedialog, messagebox
from colorama import Fore, Style, init
import threading
import queue
import time
import os
import datetime
import traceback
from reset_machine_manual import MachineIDResetter
from cursor_register import CursorRegistration
from main import Translator
import sys

# 初始化colorama
init()

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.updating = True
        threading.Thread(target=self.update_widget_loop, daemon=True).start()

    def write(self, string):
        self.queue.put(string)

    def update_widget_loop(self):
        while self.updating:
            try:
                while True:
                    string = self.queue.get_nowait()
                    self.text_widget.insert(tk.END, string)
                    self.text_widget.see(tk.END)
                    self.text_widget.update()
            except queue.Empty:
                time.sleep(0.1)
            except tk.TclError:
                self.updating = False
                break

    def flush(self):
        pass

class CursorRegistrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Cursor批量注册工具')
        self.translator = Translator()
        self.start_time = None
        self.registered_count = 0
        # 设置默认账号文件路径
        self.accounts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cursor_accounts.txt')
        self.setup_gui()
        self.update_status()

    def setup_gui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 控制区域（上方）
        control_frame = ttk.LabelFrame(main_frame, text='控制面板', padding="5")
        control_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志区域（下方）
        log_frame = ttk.LabelFrame(main_frame, text='运行日志', padding="5")
        log_frame.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=50, height=20)
        self.log_text.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏（底部）
        status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=1)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # 运行时间
        self.runtime_var = StringVar(value="运行时间: 00:00:00")
        ttk.Label(status_frame, textvariable=self.runtime_var).grid(row=0, column=0, padx=10, pady=2, sticky=tk.W)
        
        # 注册账号数
        self.count_var = StringVar(value="注册进度: 0/0")
        ttk.Label(status_frame, textvariable=self.count_var).grid(row=0, column=1, padx=10, pady=2, sticky=tk.E)
        
        # 帮助按钮
        self.help_button = ttk.Button(status_frame, text="帮助", command=self.show_help)
        self.help_button.grid(row=0, column=2, padx=10, pady=2, sticky=tk.E)
        
        # 配置grid权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=3)  # 日志区域占据更多垂直空间
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        status_frame.columnconfigure(2, weight=0)  # 帮助按钮不需要扩展

        # 线程设置
        ttk.Label(control_frame, text='线程数量:').grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.thread_count = ttk.Entry(control_frame, width=10)
        self.thread_count.insert(0, '1')
        self.thread_count.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 目标注册数量设置
        ttk.Label(control_frame, text='目标注册数:').grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.target_count = ttk.Entry(control_frame, width=10)
        self.target_count.insert(0, '10')
        self.target_count.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # 无头浏览器选项
        self.headless_var = BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text='无头浏览器模式', variable=self.headless_var).grid(
            row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # 代理设置
        proxy_frame = ttk.LabelFrame(control_frame, text='代理设置', padding="5")
        proxy_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 启用代理开关
        self.use_proxy_var = BooleanVar(value=False)
        ttk.Checkbutton(proxy_frame, text='启用代理', variable=self.use_proxy_var, 
                        command=self.toggle_proxy).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        # SecretId输入
        ttk.Label(proxy_frame, text='SecretId:').grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.secret_id_entry = ttk.Entry(proxy_frame, width=30)
        self.secret_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.secret_id_entry['state'] = 'disabled'  # 默认禁用

        # SecretKey输入
        ttk.Label(proxy_frame, text='SecretKey:').grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.secret_key_entry = ttk.Entry(proxy_frame, width=30)
        self.secret_key_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.secret_key_entry['state'] = 'disabled'  # 默认禁用
        
        # 账号文件设置
        file_frame = ttk.LabelFrame(control_frame, text='账号文件设置', padding="5")
        file_frame.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 显示当前保存路径
        self.file_path_var = StringVar(value=self.accounts_file)
        ttk.Label(file_frame, text='保存路径:').grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=40, state='readonly').grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 选择路径按钮
        ttk.Button(file_frame, text='选择路径', command=self.choose_save_path).grid(row=0, column=2, padx=5, pady=5)
        
        # 打开文件按钮
        ttk.Button(file_frame, text='打开账号文件', command=self.open_accounts_file).grid(row=0, column=3, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        self.reset_button = ttk.Button(button_frame, text='重置机器码', command=self.reset_machine_id)
        self.reset_button.grid(row=0, column=0, padx=5)
        
        self.start_button = ttk.Button(button_frame, text='开始注册', command=self.start_registration)
        self.start_button.grid(row=0, column=1, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text='停止', command=self.stop_registration)
        self.stop_button.grid(row=0, column=2, padx=5)
        self.stop_button['state'] = 'disabled'
        
        # 重定向标准输出到日志窗口
        self.redirect = RedirectText(self.log_text)
        sys.stdout = self.redirect
        
        self.running = False
        self.threads = []
        self.stop_event = threading.Event()  # 添加停止事件用于线程同步
    
    def toggle_proxy(self):
        """启用或禁用代理输入框"""
        if self.use_proxy_var.get():
            self.secret_id_entry['state'] = 'normal'
            self.secret_key_entry['state'] = 'normal'
        else:
            self.secret_id_entry['state'] = 'disabled'
            self.secret_key_entry['state'] = 'disabled'
    
    def reset_machine_id(self):
        def reset_thread():
            self.reset_button['state'] = 'disabled'
            try:
                resetter = MachineIDResetter(self.translator)
                resetter.reset_machine_ids()
            finally:
                self.reset_button['state'] = 'normal'
        
        threading.Thread(target=reset_thread, daemon=True).start()
    
    def start_registration(self):
        try:
            thread_count = int(self.thread_count.get())
            target_count = int(self.target_count.get())
            if thread_count < 1:
                raise ValueError('线程数必须大于0')
            if target_count < 1:
                raise ValueError('目标注册数必须大于0')
        except ValueError as e:
            print(f"错误: {e}")
            return
        
        self.running = True
        self.stop_event.clear()  # 重置停止事件
        self.start_time = time.time()
        self.registered_count = 0
        self.target_count_value = target_count
        self.count_var.set(f"注册进度: 0/{target_count}")
        self.start_button['state'] = 'disabled'
        self.stop_button['state'] = 'normal'
        self.thread_count['state'] = 'disabled'
        self.target_count['state'] = 'disabled'
        self.reset_button['state'] = 'disabled'
        
        # 禁用所有控制选项
        self.secret_id_entry['state'] = 'disabled'
        self.secret_key_entry['state'] = 'disabled'
        self.headless_var.set(self.headless_var.get())  # 保持当前值
        
        # 清空线程列表
        self.threads = []
        
        for _ in range(thread_count):
            thread = threading.Thread(target=self.registration_thread, daemon=True)
            self.threads.append(thread)
            thread.start()
    
    def stop_registration(self):
        self.running = False
        self.stop_event.set()  # 设置停止事件，通知所有线程停止
        self.stop_button['state'] = 'disabled'
        print("正在停止所有注册任务...")
        
        # 立即关闭所有浏览器实例
        from browser import BrowserManager
        BrowserManager.quit_all_browsers()
        
        # 强制终止所有Chrome相关进程
        def kill_chrome_processes():
            try:
                if sys.platform == 'darwin':  # macOS
                    os.system('pkill -f "Google Chrome"')
                    os.system('pkill -f chromedriver')
                elif sys.platform == 'win32':  # Windows
                    os.system('taskkill /F /IM chrome.exe /T 2>nul')
                    os.system('taskkill /F /IM chromedriver.exe /T 2>nul')
                else:  # Linux
                    os.system('pkill -f chrome')
                    os.system('pkill -f chromedriver')
                print(f"{Fore.GREEN}✅ 已强制终止所有浏览器进程{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ 终止浏览器进程时出错: {e}{Style.RESET_ALL}")
        
        # 在单独的线程中执行进程终止操作
        threading.Thread(target=kill_chrome_processes, daemon=True).start()
        
        # 等待所有线程结束
        for thread in self.threads:
            if thread.is_alive():
                thread.join(0.1)  # 非阻塞等待
        
        # 使用after方法定期检查线程状态
        self.check_threads_status()
    
    def check_threads_status(self):
        """检查线程状态，如果所有线程都已结束，则重置GUI状态"""
        active_threads = [t for t in self.threads if t.is_alive()]
        if active_threads:
            # 还有活动线程，继续检查
            self.root.after(500, self.check_threads_status)
        else:
            # 所有线程已结束，重置GUI状态
            self.reset_gui_state()
    
    def registration_thread(self):
        while self.running and not self.stop_event.is_set():
            try:
                # 检查是否达到目标注册数
                if self.registered_count >= self.target_count_value:
                    self.running = False
                    break

                # 处理代理设置
                proxy_manager = None
                if self.use_proxy_var.get():
                    secret_id = self.secret_id_entry.get().strip()
                    secret_key = self.secret_key_entry.get().strip()
                    if secret_id and secret_key:
                        from proxy_manager import ProxyManager
                        proxy_manager = ProxyManager(secret_id=secret_id, secret_key=secret_key, translator=self.translator)
                        proxy = proxy_manager.get_valid_proxy()
                        if proxy:
                            os.environ['HTTP_PROXY'] = f'http://{proxy}'
                            os.environ['HTTPS_PROXY'] = f'http://{proxy}'
                            print(f"{Fore.GREEN}✅ 成功配置代理: {proxy}{Style.RESET_ALL}")
                else:
                    # 清除代理设置
                    if 'HTTP_PROXY' in os.environ:
                        del os.environ['HTTP_PROXY']
                    if 'HTTPS_PROXY' in os.environ:
                        del os.environ['HTTPS_PROXY']
                
                # 创建注册实例并启动
                registration = CursorRegistration(self.translator, proxy=proxy if proxy_manager else None, headless=self.headless_var.get())
                
                # 修改注册实例的保存路径
                original_save_method = registration._save_account_info
                
                def custom_save_method(token, total_usage):
                    """自定义保存方法，使用指定的保存路径"""
                    try:
                        print(f"\n{Fore.CYAN}[DEBUG] 开始保存账户信息...{Style.RESET_ALL}")
                        print(f"[DEBUG] 保存路径: {self.accounts_file}")
                        print(f"[DEBUG] 文件是否存在: {os.path.exists(self.accounts_file)}")
                        print(f"[DEBUG] 目录是否可写: {os.access(os.path.dirname(self.accounts_file), os.W_OK)}")
                        
                        # 保存账户信息到文件，使用-------分隔每组账号
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[DEBUG] 当前时间: {current_time}")
                        print(f"[DEBUG] 邮箱地址: {registration.email_address}")
                        
                        with open(self.accounts_file, 'a', encoding='utf-8') as f:
                            print(f"[DEBUG] 文件已打开，准备写入数据")
                            f.write(f"Email: {registration.email_address}\n")
                            f.write(f"Password: {registration.password}\n")
                            f.write(f"Token: {token}\n")
                            f.write(f"Usage Limit: {total_usage}\n")
                            f.write(f"Register Time: {current_time}\n")
                            f.write("-------\n")
                            f.flush()  # 确保数据立即写入磁盘
                            print(f"[DEBUG] 数据写入完成")
                            
                        print(f"{Fore.GREEN}{registration.EMOJI['SUCCESS']} {registration.translator.get('register.account_info_saved')}...{Style.RESET_ALL}")
                        return True
                        
                    except Exception as e:
                        print(f"\n{Fore.RED}[DEBUG] 保存账户信息时出错:{Style.RESET_ALL}")
                        print(f"[DEBUG] 错误类型: {type(e).__name__}")
                        print(f"[DEBUG] 错误信息: {str(e)}")
                        print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
                        print(f"{Fore.RED}{registration.EMOJI['ERROR']} {registration.translator.get('register.save_account_info_failed', error=str(e))}{Style.RESET_ALL}")
                        return False
                
                # 替换保存方法
                registration._save_account_info = custom_save_method
                
                success = registration.start()
                
                # 如果注册成功，增加计数
                if success:
                    self.registered_count += 1
                    self.count_var.set(f"注册进度: {self.registered_count}/{self.target_count_value}")
                    
                    # 如果达到目标数量，停止所有线程
                    if self.registered_count >= self.target_count_value:
                        print(f"{Fore.GREEN}✅ 已达到目标注册数量，正在停止所有任务...{Style.RESET_ALL}")
                        self.running = False
                        break
                
            except Exception as e:
                print(f"注册过程出错: {e}")
            
            if not self.running or self.stop_event.is_set():
                break
    
    def reset_gui_state(self):
        self.start_button['state'] = 'normal'
        self.thread_count['state'] = 'normal'
        self.target_count['state'] = 'normal'
        self.reset_button['state'] = 'normal'
        
        # 恢复代理设置状态
        if self.use_proxy_var.get():
            self.secret_id_entry['state'] = 'normal'
            self.secret_key_entry['state'] = 'normal'
        
        print("所有注册任务已停止")
    
    def update_status(self):
        """更新状态栏信息"""
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.runtime_var.set(f"运行时间: {time_str}")
        
        # 每秒更新一次
        self.root.after(1000, self.update_status)

    def show_help(self):
        """显示帮助信息对话框"""
        help_text = """
功能说明：

1. 线程设置
   - 线程数量：同时运行的注册任务数，建议1-5个
   - 目标注册数：需要注册的总账号数量

2. 无头浏览器模式
   - 启用后将隐藏浏览器界面，提高运行效率
   - 建议在确认配置正确后使用

3. 账号文件设置
   - 保存路径：账号文件的保存位置，默认为程序所在目录
   - 选择路径：更改账号文件保存位置
   - 打开账号文件：直接打开已保存的账号文件

4. 代理设置
   - 启用代理：使用代理IP进行注册
   - SecretId/SecretKey：快代理API认证信息

5. 操作按钮
   - 重置机器码：重置本机标识，避免重复注册
   - 开始注册：启动注册任务
   - 停止：终止所有正在运行的注册任务

6. 状态信息
   - 运行时间：任务开始后的持续时间
   - 注册进度：已完成数量/目标数量

注意事项：
- 使用代理可以提高注册成功率
- 建议定期重置机器码
- 运行日志区域会显示详细的执行状态
        """
        messagebox.showinfo("使用帮助", help_text)

    def choose_save_path(self):
        """选择账号文件保存路径"""
        new_path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text Files', '*.txt')],
            initialfile='cursor_accounts.txt',
            title='选择账号文件保存位置'
        )
        if new_path:
            self.accounts_file = new_path
            self.file_path_var.set(new_path)
    
    def open_accounts_file(self):
        """打开账号文件"""
        if os.path.exists(self.accounts_file):
            if sys.platform == 'darwin':  # macOS
                os.system(f'open {self.accounts_file}')
            elif sys.platform == 'win32':  # Windows
                os.system(f'start {self.accounts_file}')
            else:  # Linux
                os.system(f'xdg-open {self.accounts_file}')
        else:
            messagebox.showwarning('警告', '账号文件不存在！')

def main():
    root = tk.Tk()
    root.geometry("800x600")  # 设置初始窗口大小
    app = CursorRegistrationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()