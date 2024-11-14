import os
import time
import requests
from termcolor import colored
import pyfiglet
import inquirer
from threading import Thread
from datetime import datetime
import itertools
import traceback
import random

def read_lines(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

class Config:
    def __init__(self):
        self.base_url = 'https://nodepay.org'
        self.ping_url = 'http://13.215.134.222/api/network/ping'
        self.retry_interval = 3  # 初始重试间隔为3秒
        self.session_url = 'http://api.nodepay.ai/api/auth/session'

class Logger:
    @staticmethod
    def info(message, data=None):
        print(colored(f"[INFO] {message}: {data}", 'green'))

    @staticmethod
    def error(message, data=None):
        print(colored(f"[ERROR] {message}: {data}", 'red'))

class Bot:
    def __init__(self, config, logger, proxies=None):
        self.config = config
        self.logger = logger
        self.proxies = proxies or []
        self.proxy_cycle = itertools.cycle(self.proxies)  # 用于循环遍历代理
        self.successful_pings = 0  # 统计成功的Ping次数
        self.dynamic_retry_interval = self.config.retry_interval  # 初始间隔

    def connect(self, token):
        print(f"开始连接令牌: {token[:10]}...")  # 调试输出
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            account_info = self.get_session(token, user_agent)
            print(f"成功获取会话信息: {account_info}")  # 调试输出
            print(f"成功连接到令牌 {token[:10]} 的会话...")

            self.logger.info('Session info', {'status': 'success', 'token': token[:10] + '...'})

            # Start pinging process for the token
            self.ping_all_proxies(account_info, token, user_agent)

        except Exception as error:
            print(f"令牌 {token[:10]} 的连接失败: {error}")  # 调试输出
            print(traceback.format_exc())  # 打印完整的错误堆栈
            self.logger.error('连接错误', {'error': str(error), 'token': token[:10] + '...'})

    def get_session(self, token, user_agent):
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }

        try:
            if self.proxies:
                response = requests.post(self.config.session_url, headers=headers, proxies=self.proxies[0])
            else:
                response = requests.post(self.config.session_url, headers=headers)
            response.raise_for_status()  # 如果请求失败，则抛出异常
            return response.json()['data']
        except requests.RequestException as e:
            print(f"获取会话信息时出错: {e}")
            print(traceback.format_exc())  # 打印完整的错误堆栈
            self.logger.error('会话获取错误', {'error': str(e)})

    def ping_all_proxies(self, account_info, token, user_agent):
        """依次ping所有代理，完成后等待6分钟再开始下一轮ping"""
        while True:
            for proxy in self.proxies:
                device_info = self.generate_device_info()  # 获取随机设备信息
                self.send_ping(account_info, token, user_agent, proxy, device_info)

            # 所有代理完成后，等待6分钟
            print("所有代理已完成Ping，开始等待6分钟...")
            self.logger.info('所有代理已Ping完，开始等待 6 分钟...')
            time.sleep(360)  # 等待6分钟

    def send_ping(self, account_info, token, user_agent, proxy, device_info):
        ping_data = {
            'id': account_info.get('uid', 'Unknown'),
            'browser_id': account_info.get('browser_id', 'random_browser_id'),
            'timestamp': int(time.time()),
            'version': '2.2.7',
            'device_info': device_info  # 添加设备信息
        }

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': user_agent,
            'Accept': 'application/json'
        }

        try:
            start_time = time.time()

            response = requests.post(self.config.ping_url, json=ping_data, headers=headers, proxies=proxy)

            response.raise_for_status()  # 如果请求失败，则抛出异常

            end_time = time.time()

            ping_duration = end_time - start_time

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(colored(f"[{timestamp}] 成功发送Ping给令牌 {token[:10]} 使用代理 {proxy['http']}... | 时长: {ping_duration:.2f} 秒", 'magenta'))
            self.logger.info('Ping已发送', {'status': 'success', 'token': token[:10] + '...', 'proxy': proxy['http'], 'duration': f'{ping_duration:.2f}秒'})
        except Exception as error:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(colored(f"[{timestamp}] 令牌 {token[:10]} 的Ping失败 使用代理 {proxy['http']} : {error}", 'yellow'))
            print(traceback.format_exc())  # 打印完整的错误堆栈
            self.logger.error('Ping错误', {'error': str(error), 'token': token[:10] + '...', 'proxy': proxy['http']})

    def generate_device_info(self):
        """随机生成设备信息（仅限网页端设备）"""
        devices = [
            {'device': 'Windows 10', 'os': 'Windows', 'browser': 'Chrome'},
            {'device': 'Windows 10', 'os': 'Windows', 'browser': 'Firefox'},
            {'device': 'MacBook Pro', 'os': 'macOS', 'browser': 'Safari'},
            {'device': 'MacBook Pro', 'os': 'macOS', 'browser': 'Chrome'},
            {'device': 'Linux', 'os': 'Linux', 'browser': 'Firefox'},
            {'device': 'Linux', 'os': 'Linux', 'browser': 'Chrome'}
        ]
        return random.choice(devices)

def display_welcome():
    ascii_art = pyfiglet.figlet_format("Nodepay Bot")
    print(colored(ascii_art, 'yellow'))
    print(colored("========================================", 'cyan'))
    print(colored("=        欢迎使用 MiweAirdrop        =", 'cyan'))
    print(colored("=       自动化强力机器人             =", 'cyan'))
    print(colored("========================================", 'cyan'))

def ask_proxy_mode():
    questions = [
        inquirer.List('proxy_mode',
                      message="是否使用代理？",
                      choices=['不使用代理', '使用代理'],
                      default='不使用代理',
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer['proxy_mode']

def configure_proxy():
    proxies = read_lines('proxy.txt')
    if not proxies:
        print(colored("proxy.txt 中没有找到代理", 'red'))
        return None

    proxies = proxies[:100]

    proxy_list = []
    for proxy in proxies:
        proxy_parts = proxy.split(':')
        if len(proxy_parts) == 4:
            host, port, username, password = proxy_parts
            proxy_dict = {
                'http': f'http://{username}:{password}@{host}:{port}',
                'https': f'http://{username}:{password}@{host}:{port}'
            }
            proxy_list.append(proxy_dict)
    
    return proxy_list

def main():
    display_welcome()

    tokens = read_lines('token.txt')
    if not tokens:
        print("没有找到令牌文件，退出程序")
        return

    config = Config()
    logger = Logger()

    proxy_mode = ask_proxy_mode()
    print(f"代理模式: {proxy_mode}")  # 调试输出

    proxies = None
    if proxy_mode == '使用代理':
        proxies = configure_proxy()
        if proxies:
            print(f"使用了 {len(proxies)} 个代理")
        else:
            print("未配置有效代理，使用直连方式。")  # 修复了这行

    # 启动线程处理每个令牌
    for token in tokens:
        bot = Bot(config, logger, proxies)
        thread = Thread(target=bot.connect, args=(token,))
        thread.start()

if __name__ == "__main__":
    main()
