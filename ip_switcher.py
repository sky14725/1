import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, \
    QLabel, QFileDialog, QMessageBox, QSizePolicy, QGroupBox, QGraphicsDropShadowEffect, QLineEdit, QProgressBar
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor, QFont, QPalette, QBrush, QImage
import requests
import winreg
from concurrent.futures import ThreadPoolExecutor
import logging
import random

# 设置日志
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", filename="ip_switcher.log")


def resource_path(relative_path):
    """获取打包后文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class ProxyTester(QThread):
    result_ready = pyqtSignal(list)
    progress_update = pyqtSignal(int)

    def __init__(self, proxies, max_workers):
        super().__init__()
        self.proxies = proxies
        self.max_workers = max_workers  # 接收自定义线程数

    def run(self):
        def test_proxy(proxy):
            try:
                proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                response = requests.get("http://ipinfo.io/ip", proxies=proxies, timeout=2)
                return proxy, response.status_code == 200, response.text.strip()
            except requests.exceptions.ConnectionError:
                logging.error(f"代理 {proxy} 连接失败")
                return proxy, False, "连接失败"
            except requests.exceptions.Timeout:
                logging.error(f"代理 {proxy} 超时")
                return proxy, False, "超时"
            except requests.exceptions.RequestException as e:
                logging.error(f"代理 {proxy} 测试失败: {str(e)}")
                return proxy, False, str(e)
            except Exception as e:
                logging.error(f"代理 {proxy} 未知错误: {str(e)}")
                return proxy, False, str(e)

        results = []
        total = len(self.proxies)
        completed = 0

        # 使用用户指定的线程数
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in self.proxies}
            for future in future_to_proxy:
                result = future.result()
                results.append(result)
                completed += 1
                progress = int(completed / total * 100)
                self.progress_update.emit(progress)

        self.result_ready.emit(results)


class IPSwitcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP自动更换工具")
        self.setGeometry(100, 100, 1080, 720)
        self.setMinimumSize(400, 500)

        # 设置无边框和透明背景
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 添加窗口阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)

        # 主窗口部件
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 200);
                border-radius: 15px;
            }
        """)
        self.setCentralWidget(self.central_widget)

        # 设置背景图片
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

        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(20)
        self.central_widget.setLayout(self.main_layout)

        # 标题栏布局
        self.title_layout = QHBoxLayout()
        self.title_label = QLabel("IP自动更换工具")
        self.title_label.setStyleSheet("font-size: 16px; color: #333; font-weight: bold;")
        self.title_layout.addWidget(self.title_label)

        self.title_layout.addStretch(1)

        self.minimize_button = QPushButton("—")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #FFB300;
                color: white;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFA000;
            }
        """)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.title_layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 15px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        self.close_button.clicked.connect(self.close)
        self.title_layout.addWidget(self.close_button)

        self.main_layout.addLayout(self.title_layout)

        # 设置全局字体
        self.setFont(QFont("Microsoft YaHei", 11))

        # 代理列表区域
        self.proxy_group = QGroupBox("代理列表")
        self.proxy_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #333;
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.proxy_layout = QVBoxLayout()
        self.proxy_list = QListWidget()
        self.proxy_list.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 5px;
                padding: 5px;
                background-color: rgba(255, 255, 255, 220);
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
        """)
        self.proxy_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.proxy_list.setMinimumHeight(300)
        self.proxy_layout.addWidget(self.proxy_list)
        self.proxy_group.setLayout(self.proxy_layout)
        self.main_layout.addWidget(self.proxy_group)

        # 信息区域
        self.info_group = QGroupBox("当前状态")
        self.info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #333;
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.info_layout = QVBoxLayout()

        self.current_ip_label = QLabel("当前IP：未知")
        self.current_ip_label.setStyleSheet("font-size: 16px; color: #2196F3; font-weight: bold;")
        self.current_ip_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_layout.addWidget(self.current_ip_label)

        self.config_label = QLabel("说明：本工具通过系统代理更换IP，将影响所有网络请求。异常代理将被跳过。")
        self.config_label.setWordWrap(True)
        self.config_label.setStyleSheet("color: #555;")
        self.info_layout.addWidget(self.config_label)

        self.test_result_label = QLabel("测试结果：未测试")
        self.test_result_label.setStyleSheet("color: #333;")
        self.test_result_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_layout.addWidget(self.test_result_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #1976D2;
                border-radius: 8px;
                text-align: center;
                background-color: #e0e0e0;
                font-size: 12px;
                color: #333;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #42A5F5, stop:1 #1976D2);
                border-radius: 6px;
            }
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.info_layout.addWidget(self.progress_bar)

        self.info_group.setLayout(self.info_layout)
        self.main_layout.addWidget(self.info_group)

        # 按钮区域
        self.button_group = QGroupBox("操作")
        self.button_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #333;
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(15)

        self.load_button = QPushButton("加载代理列表")
        self.test_button = QPushButton("测试代理可用性")
        self.start_button = QPushButton("开始自动更换IP")
        self.stop_button = QPushButton("停止自动更换")

        self.interval_label = QLabel("切换间隔（秒）：")
        self.interval_label.setStyleSheet("color: #333;")
        self.interval_input = QLineEdit("60")
        self.interval_input.setFixedWidth(60)
        self.interval_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
        """)

        # 添加线程数输入框
        self.thread_label = QLabel("测试线程数：")
        self.thread_label.setStyleSheet("color: #333;")
        self.thread_input = QLineEdit("10")  # 默认 10 个线程
        self.thread_input.setFixedWidth(60)
        self.thread_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
        """)

        for btn in [self.load_button, self.test_button, self.start_button, self.stop_button]:
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2196F3, stop:1 #1976D2);
                    color: white;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42A5F5, stop:1 #1E88E5);
                    box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.2);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1976D2, stop:1 #1565C0);
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)
            self.button_layout.addWidget(btn)

        self.button_layout.addWidget(self.interval_label)
        self.button_layout.addWidget(self.interval_input)
        self.button_layout.addWidget(self.thread_label)
        self.button_layout.addWidget(self.thread_input)

        self.stop_button.setEnabled(False)
        self.button_group.setLayout(self.button_layout)
        self.main_layout.addWidget(self.button_group)

        # 添加伸缩项
        self.main_layout.addStretch(1)

        # 连接信号
        self.load_button.clicked.connect(self.load_proxies)
        self.test_button.clicked.connect(self.test_proxies)
        self.start_button.clicked.connect(self.start_auto_switch)
        self.stop_button.clicked.connect(self.stop_auto_switch)
        self.proxy_list.itemDoubleClicked.connect(self.manual_switch_ip)

        # 存储代理数据
        self.proxies = []
        self.valid_proxies = []
        self.current_proxy = None
        self.auto_running = False

        # 设置定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_switch_ip)

        # IP切换动画
        self.ip_animation = QPropertyAnimation(self.current_ip_label, b"windowOpacity")
        self.ip_animation.setDuration(500)
        self.ip_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # 拖动窗口所需变量
        self.dragging = False
        self.drag_position = QPoint()

        # 自动加载 proxies.txt
        self.load_default_proxies()

    def set_system_proxy(self, proxy):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                                 0, winreg.KEY_ALL_ACCESS)
            if proxy:
                proxy_ip, proxy_port = proxy.split(":")
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{proxy_ip}:{proxy_port}")
                logging.info(f"设置系统代理成功: {proxy}")
            else:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                logging.info("已关闭系统代理")
            winreg.CloseKey(key)
            return True
        except PermissionError:
            logging.error("权限不足，无法设置系统代理，请以管理员身份运行")
            QMessageBox.critical(self, "错误", "权限不足，请以管理员身份运行程序")
            return False
        except ValueError as e:
            logging.error(f"代理格式错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"代理格式错误: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"设置系统代理失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"设置系统代理失败: {str(e)}")
            return False

    def load_default_proxies(self):
        txt_path = resource_path("proxies.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as file:
                    self.proxies = [line.strip() for line in file if line.strip()]
                if self.proxies:
                    self.proxy_list.clear()
                    self.proxy_list.addItems(self.proxies)
                    self.valid_proxies = []
                    logging.info(f"自动加载 proxies.txt 成功，代理数: {len(self.proxies)}")
                    QMessageBox.information(self, "成功", f"已自动加载 {len(self.proxies)} 个代理")
                else:
                    logging.warning("proxies.txt 为空")
                    QMessageBox.warning(self, "警告", "proxies.txt 文件为空，请手动加载")
            except Exception as e:
                logging.error(f"自动加载 proxies.txt 失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"自动加载 proxies.txt 失败: {str(e)}，请手动加载")
        else:
            logging.warning("proxies.txt 文件不存在")
            QMessageBox.warning(self, "提示", "未找到 proxies.txt 文件，请手动加载代理列表")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def load_proxies(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择代理列表文件", "", "文本文件 (*.txt)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.proxies = [line.strip() for line in file if line.strip()]
                self.proxy_list.clear()
                self.proxy_list.addItems(self.proxies)
                self.valid_proxies = []
                QMessageBox.information(self, "成功", f"已加载 {len(self.proxies)} 个代理")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载文件失败: {str(e)}")

    def test_proxies(self):
        if not self.proxies:
            QMessageBox.warning(self, "警告", "请先加载代理列表")
            return

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
        self.test_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        self.tester = ProxyTester(self.proxies, max_workers)
        self.tester.progress_update.connect(self.update_progress)
        self.tester.result_ready.connect(self.on_test_finished)
        self.tester.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_test_finished(self, results):
        self.valid_proxies = []
        self.proxy_list.clear()
        for proxy, is_valid, ip_or_error in results:
            if is_valid and isinstance(ip_or_error, str) and ip_or_error:
                self.valid_proxies.append((proxy, ip_or_error))
                self.proxy_list.addItem(f"{proxy} - 可用 (IP: {ip_or_error})")

        self.test_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "完成", f"测试完成，可用代理数: {len(self.valid_proxies)}")
        if self.valid_proxies and not self.current_proxy:
            self.switch_ip(self.valid_proxies[0][0])

    def switch_ip(self, proxy):
        try:
            self.current_proxy = proxy
            if not self.set_system_proxy(proxy):
                raise Exception("设置系统代理失败")
            response = requests.get("http://ipinfo.io/ip", timeout=5)
            new_ip = response.text.strip()

            self.ip_animation.setStartValue(1.0)
            self.ip_animation.setEndValue(0.0)
            self.ip_animation.start()
            self.ip_animation.finished.connect(lambda: self.update_ip_label(new_ip, proxy))

            logging.info(f"IP切换成功，新IP: {new_ip}, 代理: {proxy}")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException,
                Exception) as e:
            logging.error(f"代理 {proxy} 失败: {str(e)}")
            self.test_result_label.setText(f"代理 {proxy} 失败: {str(e)}，跳过")
            self.valid_proxies = [(p, ip) for p, ip in self.valid_proxies if p != proxy]
            self.proxy_list.clear()
            for p, ip in self.valid_proxies:
                self.proxy_list.addItem(f"{p} - 可用 (IP: {ip})")
            if self.valid_proxies:
                next_proxy = random.choice(self.valid_proxies)[0]
                logging.info(f"跳到下一个代理: {next_proxy}")
                self.switch_ip(next_proxy)
            else:
                self.current_ip_label.setText("当前IP：无可用代理")
                self.test_result_label.setText("所有代理不可用")
                self.set_system_proxy(None)

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
            try:
                self.switch_ip(new_proxy)
                return
            except Exception:
                attempts += 1
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
            self.set_system_proxy(None)
            self.current_ip_label.setText("当前IP：无")
            self.test_result_label.setText("测试结果：未测试")
            QMessageBox.information(self, "停止", "已停止自动更换IP，系统代理已关闭")


def main():
    app = QApplication(sys.argv)
    window = IPSwitcher()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()