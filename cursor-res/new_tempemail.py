from DrissionPage import ChromiumPage, ChromiumOptions
import time
import os
import sys
from colorama import Fore, Style, init
import requests
import random
import string

# 初始化 colorama
init()

class NewTempEmail:
    def __init__(self, translator=None):
        self.translator = translator
        # Randomly choose between mail.tm and mail.gw
        self.services = [
            {"name": "mail.tm", "api_url": "https://api.mail.tm"},
            {"name": "mail.gw", "api_url": "https://api.mail.gw"}
        ]
        self.selected_service = random.choice(self.services)
        self.api_url = self.selected_service["api_url"]
        self.token = None
        self.email = None
        self.password = None
        self.blocked_domains = self.get_blocked_domains()
        
    def get_blocked_domains(self):
        """Get blocked domains list"""
        try:
            block_url = "https://raw.githubusercontent.com/yeongpin/cursor-free-vip/main/block_domain.txt"
            response = requests.get(block_url, timeout=5)
            if response.status_code == 200:
                # Split text and remove empty lines
                domains = [line.strip() for line in response.text.split('\n') if line.strip()]
                if self.translator:
                    print(f"{Fore.CYAN}ℹ️ {self.translator.get('email.blocked_domains_loaded', count=len(domains))}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}ℹ️ 已加载 {len(domains)} 个被屏蔽的域名{Style.RESET_ALL}")
                return domains
            return []
        except Exception as e:
            if self.translator:
                print(f"{Fore.YELLOW}⚠️ {self.translator.get('email.blocked_domains_error', error=str(e))}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ 获取被屏蔽域名列表失败: {str(e)}{Style.RESET_ALL}")
            return []
    
    def exclude_blocked_domains(self, domains):
        """Exclude blocked domains"""
        if not self.blocked_domains:
            return domains
            
        filtered_domains = []
        for domain in domains:
            if domain['domain'] not in self.blocked_domains:
                filtered_domains.append(domain)
                
        excluded_count = len(domains) - len(filtered_domains)
        if excluded_count > 0:
            if self.translator:
                print(f"{Fore.YELLOW}⚠️ {self.translator.get('email.domains_excluded', domains=excluded_count)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ 已排除 {excluded_count} 个被屏蔽的域名{Style.RESET_ALL}")
                
        return filtered_domains
        
    def _generate_credentials(self):
        """生成随机用户名和密码"""
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
        return username, password
        
    def create_email(self):
        """创建临时邮箱"""
        try:
            if self.translator:
                print(f"{Fore.CYAN}ℹ️ {self.translator.get('email.visiting_site').replace('mail.tm', self.selected_service['name'])}{Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}ℹ️ 正在访问 {self.selected_service['name']}...{Style.RESET_ALL}")
            
            # 获取可用域名列表
            try:
                domains_response = requests.get(f"{self.api_url}/domains", timeout=10)
                if domains_response.status_code != 200:
                    print(f"{Fore.RED}❌ {self.translator.get('email.domains_list_error', error=domains_response.status_code)}{Style.RESET_ALL}")
                    print(f"{Fore.RED}❌ {self.translator.get('email.domains_list_error', error=domains_response.text)}{Style.RESET_ALL}")
                    raise Exception(f"{self.translator.get('email.failed_to_get_available_domains') if self.translator else 'Failed to get available domains'}")
                    
                domains = domains_response.json()["hydra:member"]
                print(f"{Fore.CYAN}ℹ️ {self.translator.get('email.available_domains_loaded', count=len(domains))}{Style.RESET_ALL}")
                
                if not domains:
                    raise Exception(f"{self.translator.get('email.no_available_domains') if self.translator else '没有可用域名'}")
            except Exception as e:
                print(f"{Fore.RED}❌ 获取域名列表时出错: {str(e)}{Style.RESET_ALL}")
                raise
                
            # 排除被屏蔽的域名
            try:
                filtered_domains = self.exclude_blocked_domains(domains)
                if self.translator:
                    print(f"{Fore.CYAN}ℹ️ {self.translator.get('email.domains_filtered', count=len(filtered_domains))}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.CYAN}ℹ️ 过滤后剩余 {len(filtered_domains)} 个可用域名{Style.RESET_ALL}")
                
                if not filtered_domains:
                    if self.translator:
                        print(f"{Fore.RED}❌ {self.translator.get('email.all_domains_blocked')}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ 所有域名都被屏蔽了，尝试切换服务{Style.RESET_ALL}")
                    
                    # 切换到另一个服务
                    for service in self.services:
                        if service["api_url"] != self.api_url:
                            self.selected_service = service
                            self.api_url = service["api_url"]
                            if self.translator:
                                print(f"{Fore.CYAN}ℹ️ {self.translator.get('email.switching_service', service=service['name'])}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.CYAN}ℹ️ 切换到 {service['name']} 服务{Style.RESET_ALL}")
                            return self.create_email()  # 递归调用
                    
                    raise Exception(f"{self.translator.get('email.no_available_domains_after_filtering') if self.translator else '过滤后没有可用域名'}")
            except Exception as e:
                print(f"{Fore.RED}❌ 过滤域名时出错: {str(e)}{Style.RESET_ALL}")
                raise
                
            # 生成随机用户名和密码
            try:
                username, password = self._generate_credentials()
                self.password = password
                
                # 创建邮箱账户
                selected_domain = filtered_domains[0]['domain']
                email = f"{username}@{selected_domain}"
                
                print(f"{Fore.CYAN}ℹ️ 尝试创建邮箱: {email}{Style.RESET_ALL}")
                
                account_data = {
                    "address": email,
                    "password": password
                }
            except Exception as e:
                print(f"{Fore.RED}❌ 生成凭据时出错: {str(e)}{Style.RESET_ALL}")
                raise
            
            # 创建账户
            try:
                create_response = requests.post(f"{self.api_url}/accounts", json=account_data, timeout=15)
                
                if create_response.status_code != 201:
                    print(f"{Fore.RED}❌ 创建账户失败: 状态码 {create_response.status_code}{Style.RESET_ALL}")
                    print(f"{Fore.RED}❌ 响应内容: {create_response.text}{Style.RESET_ALL}")
                    
                    # 如果是域名问题，尝试下一个域名
                    if len(filtered_domains) > 1 and ("domain" in create_response.text.lower() or "address" in create_response.text.lower()):
                        print(f"{Fore.YELLOW}⚠️ 尝试使用下一个可用域名...{Style.RESET_ALL}")
                        # 将当前域名添加到屏蔽列表
                        if selected_domain not in self.blocked_domains:
                            self.blocked_domains.append(selected_domain)
                        # 递归调用自己
                        return self.create_email()
                        
                    raise Exception(f"{self.translator.get('email.failed_to_create_account') if self.translator else '创建账户失败'}")
            except Exception as e:
                print(f"{Fore.RED}❌ 创建账户时出错: {str(e)}{Style.RESET_ALL}")
                raise
                
            # 获取访问令牌
            try:
                token_data = {
                    "address": email,
                    "password": password
                }
                
                token_response = requests.post(f"{self.api_url}/token", json=token_data, timeout=10)
                if token_response.status_code != 200:
                    print(f"{Fore.RED}❌ 获取令牌失败: 状态码 {token_response.status_code}{Style.RESET_ALL}")
                    print(f"{Fore.RED}❌ 响应内容: {token_response.text}{Style.RESET_ALL}")
                    raise Exception(f"{self.translator.get('email.failed_to_get_access_token') if self.translator else '获取访问令牌失败'}")
                    
                self.token = token_response.json()["token"]
                self.email = email
            except Exception as e:
                print(f"{Fore.RED}❌ 获取令牌时出错: {str(e)}{Style.RESET_ALL}")
                raise
                
            if self.translator:
                print(f"{Fore.GREEN}✅ {self.translator.get('email.create_success')}: {email}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ 创建邮箱成功: {email}{Style.RESET_ALL}")
            return email
            
        except Exception as e:
            if self.translator:
                print(f"{Fore.RED}❌ {self.translator.get('email.create_error')}: {str(e)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ 创建邮箱出错: {str(e)}{Style.RESET_ALL}")
            return None
            
    def close(self):
        """关闭浏览器"""
        if self.page:
            self.page.quit()

    def refresh_inbox(self):
        """刷新邮箱"""
        try:
            if self.translator:
                print(f"{Fore.CYAN}🔄 {self.translator.get('email.refreshing')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}🔄 正在刷新邮箱...{Style.RESET_ALL}")
            
            # 使用 API 获取最新邮件
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_url}/messages", headers=headers)
            
            if response.status_code == 200:
                if self.translator:
                    print(f"{Fore.GREEN}✅ {self.translator.get('email.refresh_success')}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.GREEN}✅ 邮箱刷新成功{Style.RESET_ALL}")
                return True
            
            if self.translator:
                print(f"{Fore.RED}❌ {self.translator.get('email.refresh_failed')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ 刷新邮箱失败{Style.RESET_ALL}")
            return False
            
        except Exception as e:
            if self.translator:
                print(f"{Fore.RED}❌ {self.translator.get('email.refresh_error')}: {str(e)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ 刷新邮箱出错: {str(e)}{Style.RESET_ALL}")
            return False

    def check_for_cursor_email(self):
        """检查是否有 Cursor 的验证邮件"""
        try:
            # 使用 API 获取邮件列表
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_url}/messages", headers=headers)
            
            if response.status_code == 200:
                messages = response.json()["hydra:member"]
                for message in messages:
                    if message["from"]["address"] == "no-reply@cursor.sh" and "Verify your email address" in message["subject"]:
                        # 获取邮件内容
                        message_id = message["id"]
                        message_response = requests.get(f"{self.api_url}/messages/{message_id}", headers=headers)
                        if message_response.status_code == 200:
                            if self.translator:
                                print(f"{Fore.GREEN}✅ {self.translator.get('email.verification_found')}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.GREEN}✅ 找到验证邮件{Style.RESET_ALL}")
                            return True
                            
            if self.translator:
                print(f"{Fore.YELLOW}⚠️ {self.translator.get('email.verification_not_found')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ 未找到验证邮件{Style.RESET_ALL}")
            return False
            
        except Exception as e:
            if self.translator:
                print(f"{Fore.RED}❌ {self.translator.get('email.verification_error')}: {str(e)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ 检查验证邮件出错: {str(e)}{Style.RESET_ALL}")
            return False

    def get_verification_code(self):
        """获取验证码"""
        try:
            # 使用 API 获取邮件列表
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_url}/messages", headers=headers)
            
            if response.status_code == 200:
                messages = response.json()["hydra:member"]
                for message in messages:
                    if message["from"]["address"] == "no-reply@cursor.sh" and "Verify your email address" in message["subject"]:
                        # 获取邮件内容
                        message_id = message["id"]
                        message_response = requests.get(f"{self.api_url}/messages/{message_id}", headers=headers)
                        
                        if message_response.status_code == 200:
                            # 从邮件内容中提取验证码
                            email_content = message_response.json()["text"]
                            # 查找6位数字验证码
                            import re
                            code_match = re.search(r'\b\d{6}\b', email_content)
                            
                            if code_match:
                                code = code_match.group(0)
                                if self.translator:
                                    print(f"{Fore.GREEN}✅ {self.translator.get('email.verification_code_found')}: {code}{Style.RESET_ALL}")
                                else:
                                    print(f"{Fore.GREEN}✅ 获取验证码成功: {code}{Style.RESET_ALL}")
                                return code
            
            if self.translator:
                print(f"{Fore.YELLOW}⚠️ {self.translator.get('email.verification_code_not_found')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ 未找到有效的验证码{Style.RESET_ALL}")
            return None
            
        except Exception as e:
            if self.translator:
                print(f"{Fore.RED}❌ {self.translator.get('email.verification_code_error')}: {str(e)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ 获取验证码出错: {str(e)}{Style.RESET_ALL}")
            return None

def main(translator=None):
    temp_email = NewTempEmail(translator)
    
    try:
        email = temp_email.create_email()
        if email:
            if translator:
                print(f"\n{Fore.CYAN}📧 {translator.get('email.address')}: {email}{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.CYAN}📧 临时邮箱地址: {email}{Style.RESET_ALL}")
            
            # 测试刷新功能
            while True:
                if translator:
                    choice = input(f"\n{translator.get('email.refresh_prompt')}: ").lower()
                else:
                    choice = input("\n按 R 刷新邮箱，按 Q 退出: ").lower()
                if choice == 'r':
                    temp_email.refresh_inbox()
                elif choice == 'q':
                    break
                    
    finally:
        temp_email.close()

if __name__ == "__main__":
    main()