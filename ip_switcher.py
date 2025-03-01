import sys
import os
import time
import requests
import re
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, \
    QListWidgetItem, QLabel, QFileDialog, QMessageBox, QSizePolicy, QGroupBox, QGraphicsDropShadowEffect, QLineEdit, \
    QProgressBar, QComboBox
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PyQt5.QtGui import QColor, QFont, QPalette, QBrush, QImage
import winreg
from concurrent.futures import ThreadPoolExecutor
import logging
import random
import ctypes
import traceback

# 设置日志
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", filename="ip_switcher.log",
                    filemode='a')


def log_exception(e):
    """记录异常的详细信息"""
    logging.error(f"发生异常: {str(e)}")
    logging.error(f"异常堆栈: {traceback.format_exc()}")


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        log_exception(e)
        return False


# 代理网站配置（保持不变）
PROXY_SITES = [
    {
        "name": "齐云代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "https://proxy.ip3366.net/free/?action=china&page=1,https://proxy.ip3366.net/free/?action=china&page=2,https://proxy.ip3366.net/free/?action=china&page=3",
        "ip_regex": r'\"IP\">(\d+?\.\d+?\.\d+?\.\d+?)</td>',
        "port_regex": r'\"PORT\">(\d+?)</td>',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "89代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "https://www.89ip.cn/index_1.html,https://www.89ip.cn/index_2.html,https://www.89ip.cn/index_3.html",
        "ip_regex": r'<td>[\s]*?(\d+?\.\d+?\.\d+?\.\d+?)[\s]*?</td>',
        "port_regex": r'<td>[\s]*?\d+?\.\d+?.\d+?.\d+?[\s]*?</td>[\s]*?<td>[\s]*?(\d+?)[\s]*?</td>',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "开心代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "http://www.kxdaili.com/daili/ip/7713.html",
        "ip_regex": r'\[.+?\](\d+?\.\d+?\.\d+?\.\d+?):\d+?@.+?#',
        "port_regex": r'\[.+?\]\d+?\.\d+?.\d+?.\d+?:(\d+?)@.+?#',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "快代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "http://www.ip3366.net/?stype=1&page=1,http://www.ip3366.net/?stype=1&page=2,http://www.ip3366.net/?stype=3&page=1,http://www.ip3366.net/?stype=3&page=2",
        "ip_regex": r'<td>[\s]*?(\d+?\.\d+?\.\d+?\.\d+?)[\s]*?</td>',
        "port_regex": r'<td>[\s]*?\d+?\.\d+?.\d+?.\d+?[\s]*?</td>[\s]*?<td>[\s]*?(\d+?)[\s]*?</td>',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "高可用代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "https://ip.jiangxianli.com/?page=1",
        "ip_regex": r'<td>[\s]*?(\d+?\.\d+?\.\d+?\.\d+?)[\s]*?</td>',
        "port_regex": r'<td>[\s]*?\d+?\.\d+?.\d+?.\d+?[\s]*?</td>[\s]*?<td>[\s]*?(\d+?)[\s]*?</td>',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "小舒代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "https://xsdaili.cn/dayProxy/ip/1796.html",
        "ip_regex": r'(\d+?\.\d+?\.\d+?\.\d+?):\d+?@.+?#\[.+?\]',
        "port_regex": r'\d+?\.\d+?.\d+?.\d+?:(\d+?)@.+?#\[.+?\]',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "命运零代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "http://proxylist.fatezero.org/proxy.list",
        "ip_regex": r'\"host\": \"(.+?)\"',
        "port_regex": r'\"port\": (\d+)',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "自由代理",
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"},
        "urls": "https://www.freeproxylists.net/zh/?c=CN&u=50&page=1",
        "ip_regex": r'%3e(\d+?\.\d+?\.\d+?\.\d+?)%3c%2f',
        "port_regex": r'center\">(\d+?)</td><td',
        "proxy": True,
        "interval": 0
    },
    {
        "name": "db代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "http://proxydb.net/?protocol=http&country=CN,http://proxydb.net/?protocol=https&country=CN,http://proxydb.net/?protocol=socks5&country=CN",
        "ip_regex": r'href=\"/(\d+?\.\d+?.\d+?\.\d+?)/\d+?#http.{0,1}\">',
        "port_regex": r'href=\"/\d+?\.\d+?.\d+?.\d+?/(\d+?)#http.{0,1}\">',
        "proxy": False,
        "interval": 0
    },
    {
        "name": "hidemy代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "https://hidemy.name/cn/proxy-list/?maxtime=1000&type=h#list,https://hidemy.name/cn/proxy-list/?maxtime=1000&type=h&start=64#list,https://hidemy.name/cn/proxy-list/?maxtime=1000&type=h&start=128#list,https://hidemy.name/cn/proxy-list/?maxtime=5000&type=5#list,https://hidemy.name/cn/proxy-list/?maxtime=5000&type=s#list",
        "ip_regex": r'<td>(\d+?\.\d+?\.\d+?\.\d+?)</td>',
        "port_regex": r'<td>\d+?\.\d+?.\d+?.\d+?</td><td>(\d+)</td>',
        "proxy": True,
        "interval": 0
    },
    {
        "name": "scrape代理",
        "method": "GET",
        "headers": {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"},
        "urls": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=CN&ssl=all&anonymity=all",
        "ip_regex": r'(\d+?\.\d+?\.\d+?\.\d+?):\d+',
        "port_regex": r'\d+?\.\d+?.\d+?.\d+?:(\d+)',
        "proxy": True,
        "interval": 0
    },
    {
        "name": "my代理",
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"},
        "urls": "https://www.my-proxy.com/free-socks-5-proxy.html,https://www.my-proxy.com/free-elite-proxy.html,https://www.my-proxy.com/free-anonymous-proxy.html",
        "ip_regex": r'>(\d+?\.\d+?\.\d+?\.\d+?):\d+#',
        "port_regex": r'>\d+?\.\d+?.\d+?.\d+?:(\d+)#',
        "proxy": True,
        "interval": 0
    },
    {
        "name": "proxy代理",
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"},
        "urls": "https://free-proxy-list.net/,https://www.us-proxy.org/,https://www.socks-proxy.net/",
        "ip_regex": r'<td>(\d+?\.\d+?\.\d+?\.\d+?)</td>',
        "port_regex": r'<td>\d+?\.\d+?.\d+?.\d+?</td><td>(\d+)</td>',
        "proxy": True,
        "interval": 0
    }
]


class ProxyFetcher(QThread):
    fetch_completed = pyqtSignal(list)
    fetch_failed = pyqtSignal(str)

    def __init__(self, sites):
        super().__init__()
        self.sites = sites

    def run(self):
        try:
            all_proxies = set()

            def fetch_site(site):
                proxies = []
                urls = site["urls"].split(",")
                headers = site.get("headers", {})
                ip_pattern = re.compile(site["ip_regex"])
                port_pattern = re.compile(site["port_regex"])
                use_proxy = site.get("proxy", False)
                interval = site.get("interval", 0)

                for url in urls:
                    try:
                        response = requests.get(url, headers=headers, timeout=5,
                                                proxies=None if not use_proxy else {"http": "http://127.0.0.1:8080"})
                        if response.status_code == 200:
                            content = response.text
                            if site["name"] == "命运零代理":
                                for line in content.splitlines():
                                    try:
                                        data = json.loads(line)
                                        ip = data.get("host")
                                        port = str(data.get("port"))
                                        if ip and port:
                                            proxies.append(f"{ip}:{port}")
                                    except json.JSONDecodeError:
                                        logging.warning(f"命运零代理 JSON 解析失败: {line}")
                                        continue
                            else:
                                ip_matches = ip_pattern.findall(content)
                                port_matches = port_pattern.findall(content)
                                if len(ip_matches) != len(port_matches):
                                    logging.warning(
                                        f"{site['name']} ({url}) IP 和端口数量不匹配: {len(ip_matches)} IPs, {len(port_matches)} Ports")
                                for ip, port in zip(ip_matches, port_matches):
                                    proxy = f"{ip}:{port}"
                                    proxies.append(proxy)
                            logging.info(f"从 {site['name']} ({url}) 爬取到 {len(proxies)} 个代理")
                        else:
                            logging.warning(f"爬取 {site['name']} ({url}) 失败，状态码: {response.status_code}")
                        time.sleep(interval)
                    except requests.exceptions.RequestException as e:
                        logging.error(f"爬取 {site['name']} ({url}) 网络错误: {str(e)}")
                    except Exception as e:
                        log_exception(e)
                return proxies

            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_site = {executor.submit(fetch_site, site): site for site in self.sites}
                for future in future_to_site:
                    try:
                        site_proxies = future.result()
                        all_proxies.update(site_proxies)
                    except Exception as e:
                        logging.error(f"处理 {future_to_site[future]['name']} 失败: {str(e)}")

            proxy_list = list(all_proxies)
            if proxy_list:
                logging.info(f"总共爬取到 {len(proxy_list)} 个唯一代理")
                self.fetch_completed.emit(proxy_list)
            else:
                self.fetch_failed.emit("未爬取到任何代理")
        except Exception as e:
            log_exception(e)
            self.fetch_failed.emit(f"爬取代理时发生错误: {str(e)}")


class ProxyTester(QThread):
    result_ready = pyqtSignal(list)
    progress_update = pyqtSignal(int)

    def __init__(self, proxies, max_workers):
        super().__init__()
        self.proxies = proxies
        self.max_workers = max_workers

    def run(self):
        try:
            def test_proxy(proxy):
                try:
                    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                    response = requests.get("https://www.baidu.com", proxies=proxies, timeout=2)
                    if response.status_code == 200:  # 百度返回 200 表示成功
                        ip_response = requests.get("http://ipinfo.io/ip", proxies=proxies, timeout=2)
                        return proxy, True, ip_response.text.strip()
                    return proxy, False, f"状态码: {response.status_code}"
                except requests.exceptions.RequestException as e:
                    logging.error(f"代理 {proxy} 测试网络错误: {str(e)}")
                    return proxy, False, str(e)
                except Exception as e:
                    log_exception(e)
                    return proxy, False, str(e)

            results = []
            total = len(self.proxies)
            completed = 0

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in self.proxies}
                for future in future_to_proxy:
                    try:
                        result = future.result()
                        results.append(result)
                        completed += 1
                        progress = int(completed / total * 100)
                        self.progress_update.emit(progress)
                    except Exception as e:
                        logging.error(f"测试代理 {future_to_proxy[future]} 失败: {str(e)}")
                        results.append((future_to_proxy[future], False, str(e)))
                        completed += 1
                        progress = int(completed / total * 100)
                        self.progress_update.emit(progress)

            self.result_ready.emit(results)
        except Exception as e:
            log_exception(e)
            self.result_ready.emit([])


class ProxySwitcher(QThread):
    switch_completed = pyqtSignal(str, str)
    switch_failed = pyqtSignal(str)

    def __init__(self, proxy):
        super().__init__()
        self.proxy = proxy

    def run(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                 0, winreg.KEY_ALL_ACCESS)
            proxy_ip, proxy_port = self.proxy.split(":")
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{proxy_ip}:{proxy_port}")
            winreg.CloseKey(key)
            logging.info(f"设置系统代理成功: {self.proxy}")

            time.sleep(1)
            response = requests.get("https://www.baidu.com", proxies=None, timeout=3)
            if response.status_code != 200:  # 百度返回 200 表示成功
                raise Exception(f"代理未生效，状态码: {response.status_code}")
            ip_response = requests.get("http://ipinfo.io/ip", proxies=None, timeout=3)
            new_ip = ip_response.text.strip()
            self.switch_completed.emit(new_ip, self.proxy)
        except requests.exceptions.RequestException as e:
            logging.error(f"代理切换网络错误: {str(e)}")
            self.switch_failed.emit(f"网络错误: {str(e)}")
        except Exception as e:
            log_exception(e)
            self.switch_failed.emit(f"设置代理失败: {str(e)}")


class IPSwitcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP自动更换工具")
        self.setGeometry(100, 100, 1280, 800)
        self.setMinimumSize(600, 600)

        if not is_admin():
            QMessageBox.warning(self, "警告", "请以管理员身份运行程序以确保系统代理生效")

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: rgba(255, 255, 255, 200); border-radius: 15px;")
        self.setCentralWidget(self.central_widget)

        palette = QPalette()
        bg_path = resource_path("background.jpg")
        bg_image = QImage(bg_path)
        if bg_image.isNull():
            logging.warning("背景图片加载失败，使用默认背景色")
            palette.setBrush(QPalette.Background, QBrush(QColor(240, 240, 240)))
        else:
            palette.setBrush(QPalette.Background,
                             QBrush(bg_image.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)
        self.central_widget.setLayout(self.main_layout)

        self.title_layout = QHBoxLayout()
        self.title_label = QLabel("IP自动更换工具")
        self.title_label.setStyleSheet("font-size: 18px; color: #333; font-weight: bold;")
        self.title_layout.addWidget(self.title_label)

        self.title_layout.addStretch(1)
        self.minimize_button = QPushButton("—")
        self.minimize_button.setFixedSize(40, 40)
        self.minimize_button.setStyleSheet(
            "background-color: #FFB300; color: white; border-radius: 20px; font-size: 18px; QPushButton:hover {background-color: #FFA000;}")
        self.minimize_button.clicked.connect(self.showMinimized)
        self.title_layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(40, 40)
        self.close_button.setStyleSheet(
            "background-color: #F44336; color: white; border-radius: 20px; font-size: 22px; QPushButton:hover {background-color: #D32F2F;}")
        self.close_button.clicked.connect(self.close)
        self.title_layout.addWidget(self.close_button)

        self.main_layout.addLayout(self.title_layout)

        self.setFont(QFont("Microsoft YaHei", 12))

        self.proxy_group = QGroupBox("代理列表")
        self.proxy_group.setStyleSheet(
            "QGroupBox {font-weight: bold; color: #333; background-color: rgba(255, 255, 255, 180); border: 1px solid #d0d0d0; border-radius: 8px; padding: 15px; font-size: 14px;}")
        self.proxy_layout = QVBoxLayout()
        self.proxy_list = QListWidget()
        self.proxy_list.setStyleSheet(
            "QListWidget {border: none; border-radius: 5px; padding: 10px; background-color: rgba(255, 255, 255, 220); color: #333; font-size: 14px; line-height: 30px;} QListWidget::item {height: 30px;} QListWidget::item:selected {background-color: #2196F3; color: white;} QListWidget::item:hover {background-color: #e0e0e0;}")
        self.proxy_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.proxy_list.setMinimumHeight(400)
        self.proxy_layout.addWidget(self.proxy_list)
        self.proxy_group.setLayout(self.proxy_layout)
        self.main_layout.addWidget(self.proxy_group)

        self.info_group = QGroupBox("当前状态")
        self.info_group.setStyleSheet(
            "QGroupBox {font-weight: bold; color: #333; background-color: rgba(255, 255, 255, 180); border: 1px solid #d0d0d0; border-radius: 8px; padding: 15px; font-size: 14px;}")
        self.info_group.setMinimumWidth(600)  # 增加宽度
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(20)
        self.info_layout.setAlignment(Qt.AlignLeft)  # 左对齐

        self.current_ip_label = QLabel("当前IP：未知")
        self.current_ip_label.setStyleSheet("font-size: 18px; color: #2196F3; font-weight: bold;")
        self.current_ip_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 调整为 Preferred
        self.current_ip_label.setWordWrap(False)
        self.current_ip_label.setMinimumWidth(400)  # 增加最小宽度
        self.info_layout.addWidget(self.current_ip_label)

        self.config_label = QLabel("说明：本工具通过系统代理更换IP，将影响所有网络请求。异常代理将被跳过。")
        self.config_label.setWordWrap(True)
        self.config_label.setStyleSheet("color: #555; font-size: 14px;")
        self.config_label.setMinimumWidth(400)
        self.config_label.setMinimumHeight(50)
        self.info_layout.addWidget(self.config_label)

        self.test_result_label = QLabel("测试结果：未测试")
        self.test_result_label.setStyleSheet("color: #333; font-size: 14px;")
        self.test_result_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.test_result_label.setMinimumWidth(400)
        self.test_result_label.setMinimumHeight(30)
        self.info_layout.addWidget(self.test_result_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {border: 2px solid #1976D2; border-radius: 8px; text-align: center; background-color: #e0e0e0; font-size: 14px; color: #333; height: 25px;}
            QProgressBar::chunk {background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #42A5F5, stop:1 #1976D2); border-radius: 6px;}
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.info_layout.addWidget(self.progress_bar)

        self.info_group.setLayout(self.info_layout)
        self.main_layout.addWidget(self.info_group)

        self.button_group = QGroupBox("操作")
        self.button_group.setStyleSheet(
            "QGroupBox {font-weight: bold; color: #333; background-color: rgba(255, 255, 255, 180); border: 1px solid #d0d0d0; border-radius: 8px; padding: 15px; font-size: 14px;}")

        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(15)

        self.button_row1 = QHBoxLayout()
        self.button_row1.setSpacing(30)

        self.load_button = QPushButton("加载文件代理")
        self.fetch_button = QPushButton("爬取网站代理")
        self.test_file_button = QPushButton("测试文件代理")
        self.test_web_button = QPushButton("测试网站代理")

        for btn in [self.load_button, self.fetch_button, self.test_file_button, self.test_web_button]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumWidth(150)
            btn.setStyleSheet("""
                QPushButton {background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2196F3, stop:1 #1976D2); color: white; border-radius: 8px; padding: 12px; font-size: 12px;}
                QPushButton:hover {background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42A5F5, stop:1 #1E88E5); box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.2);}
                QPushButton:pressed {background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1976D2, stop:1 #1565C0);}
                QPushButton:disabled {background-color: #cccccc; color: #666666;}
            """)
            self.button_row1.addWidget(btn)

        self.button_layout.addLayout(self.button_row1)

        self.button_row2 = QHBoxLayout()
        self.button_row2.setSpacing(30)

        self.source_combo = QComboBox()
        self.source_combo.addItems(["文件代理", "网站代理"])
        self.source_combo.setStyleSheet(
            "QComboBox {border: 1px solid #d0d0d0; border-radius: 5px; padding: 8px; background-color: white; font-size: 14px; min-width: 150px;}")

        self.start_button = QPushButton("开始自动更换IP")
        self.stop_button = QPushButton("停止自动更换")

        for btn in [self.start_button, self.stop_button]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumWidth(150)
            btn.setStyleSheet("""
                QPushButton {background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2196F3, stop:1 #1976D2); color: white; border-radius: 8px; padding: 12px; font-size: 12px;}
                QPushButton:hover {background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42A5F5, stop:1 #1E88E5); box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.2);}
                QPushButton:pressed {background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1976D2, stop:1 #1565C0);}
                QPushButton:disabled {background-color: #cccccc; color: #666666;}
            """)
            self.button_row2.addWidget(btn)

        self.button_row2.addWidget(self.source_combo)

        self.interval_label = QLabel("切换间隔（秒）：")
        self.interval_label.setStyleSheet("color: #333; font-size: 14px;")
        self.interval_input = QLineEdit("60")
        self.interval_input.setFixedWidth(80)
        self.interval_input.setStyleSheet(
            "QLineEdit {border: 1px solid #d0d0d0; border-radius: 5px; padding: 8px; background-color: white; font-size: 14px;}")

        self.thread_label = QLabel("测试线程数：")
        self.thread_label.setStyleSheet("color: #333; font-size: 14px;")
        self.thread_input = QLineEdit("10")
        self.thread_input.setFixedWidth(80)
        self.thread_input.setStyleSheet(
            "QLineEdit {border: 1px solid #d0d0d0; border-radius: 5px; padding: 8px; background-color: white; font-size: 14px;}")

        self.button_row2.addWidget(self.interval_label)
        self.button_row2.addWidget(self.interval_input)
        self.button_row2.addWidget(self.thread_label)
        self.button_row2.addWidget(self.thread_input)

        self.button_layout.addLayout(self.button_row2)

        self.stop_button.setEnabled(False)
        self.button_group.setLayout(self.button_layout)
        self.main_layout.addWidget(self.button_group)

        self.main_layout.addStretch(1)

        self.load_button.clicked.connect(self.load_file_proxies)
        self.fetch_button.clicked.connect(self.fetch_web_proxies)
        self.test_file_button.clicked.connect(self.test_file_proxies)
        self.test_web_button.clicked.connect(self.test_web_proxies)
        self.start_button.clicked.connect(self.start_auto_switch)
        self.stop_button.clicked.connect(self.stop_auto_switch)
        self.proxy_list.itemDoubleClicked.connect(self.manual_switch_ip)

        self.file_proxies = []
        self.web_proxies = []
        self.valid_proxies = []
        self.current_proxy = None
        self.auto_running = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_switch_ip)

        self.ip_animation = QPropertyAnimation(self.current_ip_label, b"windowOpacity")
        self.ip_animation.setDuration(500)
        self.ip_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.dragging = False
        self.drag_position = QPoint()

        self.load_default_proxies()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def load_default_proxies(self):
        try:
            txt_path = resource_path("proxies.txt")
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as file:
                    self.file_proxies = [line.strip() for line in file if line.strip()]
                if self.file_proxies:
                    self.proxy_list.clear()
                    for proxy in self.file_proxies:
                        item = QListWidgetItem(proxy)
                        item.setSizeHint(QSize(0, 30))
                        self.proxy_list.addItem(item)
                    self.valid_proxies = []
                    logging.info(f"自动加载 proxies.txt 成功，代理数: {len(self.file_proxies)}")
                    QMessageBox.information(self, "成功", f"已自动加载 {len(self.file_proxies)} 个文件代理")
                else:
                    logging.warning("proxies.txt 为空")
                    QMessageBox.warning(self, "警告", "proxies.txt 文件为空，请手动加载或爬取")
            else:
                logging.warning("proxies.txt 文件不存在")
                QMessageBox.warning(self, "提示", "未找到 proxies.txt 文件，请手动加载或爬取代理列表")
        except Exception as e:
            log_exception(e)
            QMessageBox.critical(self, "错误", f"加载默认代理失败: {str(e)}")

    def fetch_web_proxies(self):
        self.test_result_label.setText("正在从网站爬取代理...")
        self.fetch_button.setEnabled(False)
        self.fetcher = ProxyFetcher(PROXY_SITES)
        self.fetcher.fetch_completed.connect(self.on_fetch_web_completed)
        self.fetcher.fetch_failed.connect(self.on_fetch_failed)
        self.fetcher.start()

    def on_fetch_web_completed(self, proxies):
        self.fetch_button.setEnabled(True)
        if proxies:
            self.web_proxies = proxies
            self.proxy_list.clear()
            for proxy in self.web_proxies:
                item = QListWidgetItem(proxy)
                item.setSizeHint(QSize(0, 30))
                self.proxy_list.addItem(item)
            self.valid_proxies = []
            self.source_combo.setCurrentText("网站代理")
            self.test_result_label.setText(f"从网站爬取到 {len(proxies)} 个代理")
            QMessageBox.information(self, "成功", f"已从网站爬取 {len(proxies)} 个代理")
        else:
            self.test_result_label.setText("爬取到 0 个代理")
            QMessageBox.warning(self, "警告", "未从网站爬取到任何代理")

    def on_fetch_failed(self, error):
        self.fetch_button.setEnabled(True)
        logging.error(f"爬取代理失败: {error}")
        self.test_result_label.setText(f"爬取代理失败: {error}")
        QMessageBox.warning(self, "错误", f"爬取代理失败: {error}")

    def load_file_proxies(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "选择代理列表文件", "", "文本文件 (*.txt)")
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.file_proxies = [line.strip() for line in file if line.strip()]
                self.proxy_list.clear()
                for proxy in self.file_proxies:
                    item = QListWidgetItem(proxy)
                    item.setSizeHint(QSize(0, 30))
                    self.proxy_list.addItem(item)
                self.valid_proxies = []
                self.source_combo.setCurrentText("文件代理")
                QMessageBox.information(self, "成功", f"已加载 {len(self.file_proxies)} 个文件代理")
        except Exception as e:
            log_exception(e)
            QMessageBox.critical(self, "错误", f"加载文件失败: {str(e)}")

    def test_file_proxies(self):
        if not self.file_proxies:
            QMessageBox.warning(self, "警告", "请先加载文件代理")
            return
        self.test_proxies(self.file_proxies, "文件代理")

    def test_web_proxies(self):
        if not self.web_proxies:
            QMessageBox.warning(self, "警告", "请先爬取网站代理")
            return
        self.test_proxies(self.web_proxies, "网站代理")

    def test_proxies(self, proxies, source):
        try:
            max_workers = int(self.thread_input.text())
            if max_workers <= 0 or max_workers > 50:
                raise ValueError("线程数必须在 1-50 之间")
        except ValueError as e:
            logging.error(f"无效的线程数: {self.thread_input.text()}")
            QMessageBox.warning(self, "警告", f"无效的线程数: {self.thread_input.text()}，请输入 1-50 之间的整数")
            self.thread_input.setText("10")
            return

        self.valid_proxies = []
        self.proxy_list.clear()
        self.test_file_button.setEnabled(False)
        self.test_web_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.test_result_label.setText(f"正在测试{source}...")

        self.tester = ProxyTester(proxies, max_workers)
        self.tester.progress_update.connect(self.update_progress)
        self.tester.result_ready.connect(lambda results: self.on_test_finished(results, source))
        self.tester.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_test_finished(self, results, source):
        self.valid_proxies = []
        self.proxy_list.clear()
        for proxy, is_valid, ip_or_error in results:
            if is_valid:
                self.valid_proxies.append((proxy, ip_or_error))
                item = QListWidgetItem(f"{proxy} - 可用 (IP: {ip_or_error})")
                item.setSizeHint(QSize(0, 30))
                self.proxy_list.addItem(item)

        self.test_file_button.setEnabled(True)
        self.test_web_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.test_result_label.setText(f"{source}测试完成")
        QMessageBox.information(self, "完成", f"{source}测试完成，可用代理数: {len(self.valid_proxies)}")
        if self.valid_proxies and not self.current_proxy:
            self.switch_ip(self.valid_proxies[0][0])

    def switch_ip(self, proxy):
        self.test_result_label.setText(f"正在切换到代理：{proxy}")
        self.load_button.setEnabled(False)
        self.fetch_button.setEnabled(False)
        self.test_file_button.setEnabled(False)
        self.test_web_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        self.switcher = ProxySwitcher(proxy)
        self.switcher.switch_completed.connect(self.on_switch_completed)
        self.switcher.switch_failed.connect(self.on_switch_failed)
        self.switcher.start()

    def on_switch_completed(self, new_ip, proxy):
        self.current_proxy = proxy
        self.ip_animation.setStartValue(1.0)
        self.ip_animation.setEndValue(0.0)
        self.ip_animation.start()
        self.ip_animation.finished.connect(lambda: self.update_ip_label(new_ip, proxy))
        self.load_button.setEnabled(True)
        self.fetch_button.setEnabled(True)
        self.test_file_button.setEnabled(True)
        self.test_web_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(self.auto_running)

    def on_switch_failed(self, error):
        logging.error(f"代理切换失败: {error}")
        self.test_result_label.setText(f"切换失败: {error}，跳过")
        self.valid_proxies = [(p, ip) for p, ip in self.valid_proxies if p != self.current_proxy]
        self.proxy_list.clear()
        for p, ip in self.valid_proxies:
            item = QListWidgetItem(f"{p} - 可用 (IP: {ip})")
            item.setSizeHint(QSize(0, 30))
            self.proxy_list.addItem(item)
        if self.valid_proxies:
            next_proxy = random.choice(self.valid_proxies)[0]
            logging.info(f"跳到下一个代理: {next_proxy}")
            self.switch_ip(next_proxy)
        else:
            self.current_ip_label.setText("当前IP：无可用代理")
            self.test_result_label.setText("所有代理不可用")
            self.load_button.setEnabled(True)
            self.fetch_button.setEnabled(True)
            self.test_file_button.setEnabled(True)
            self.test_web_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(self.auto_running)

    def update_ip_label(self, new_ip, proxy):
        self.current_ip_label.setText(f"当前IP：{new_ip}")
        self.test_result_label.setText(f"已切换到代理：{proxy}")
        self.ip_animation.setStartValue(0.0)
        self.ip_animation.setEndValue(1.0)
        self.ip_animation.start()

    def manual_switch_ip(self, item):
        proxy = item.text().split(" - ")[0]
        if proxy in [p[0] for p in self.valid_proxies]:
            self.switch_ip(proxy)

    def auto_switch_ip(self):
        if not self.valid_proxies:
            QMessageBox.warning(self, "警告", "没有可用的代理，请先测试")
            self.stop_auto_switch()
            return

        max_attempts = len(self.valid_proxies)
        attempts = 0
        while self.valid_proxies and attempts < max_attempts:
            new_proxy = random.choice(self.valid_proxies)[0]
            self.switch_ip(new_proxy)
            return
        if not self.valid_proxies:
            QMessageBox.warning(self, "警告", "所有代理不可用，自动切换已停止")
            self.stop_auto_switch()

    def start_auto_switch(self):
        if not self.valid_proxies:
            QMessageBox.warning(self, "警告", "请先测试代理并确保有可用代理")
            return

        try:
            interval = int(self.interval_input.text())
            if interval <= 0:
                raise ValueError("切换间隔必须为正整数")
        except ValueError as e:
            logging.error(f"无效的切换间隔: {self.interval_input.text()}")
            QMessageBox.warning(self, "警告", f"无效的切换间隔: {self.interval_input.text()}，请输入正整数")
            self.interval_input.setText("60")
            return

        if not self.auto_running:
            self.auto_running = True
            self.timer.start(interval * 1000)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.start_button.setText(f"自动更换IP（每{interval}秒）")
            QMessageBox.information(self, "启动", f"已启动自动更换IP，每{interval}秒一次")
            self.auto_switch_ip()

    def stop_auto_switch(self):
        if self.auto_running:
            self.auto_running = False
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.start_button.setText("开始自动更换IP")
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                     0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                logging.info("系统代理已关闭")
            except Exception as e:
                log_exception(e)
            self.current_ip_label.setText("当前IP：无")
            self.test_result_label.setText("测试结果：未测试")
            QMessageBox.information(self, "停止", "已停止自动更换IP，系统代理已关闭")


def main():
    try:
        app = QApplication(sys.argv)
        window = IPSwitcher()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        log_exception(e)
        sys.exit(1)


if __name__ == '__main__':
    main()