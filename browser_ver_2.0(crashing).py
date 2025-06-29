import sys
import json
import os
from datetime import datetime
import hashlib
import base64
from urllib.parse import urlparse

# FIXED: Proper scaling setup before importing PyQt5
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0" 
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_FONT_DPI"] = "96"

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QMenu, QMenuBar,
    QProgressBar, QLabel, QSplitter, QListWidget, QTextEdit, QPushButton,
    QDialog, QFormLayout, QSpinBox, QCheckBox, QComboBox, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QShortcut, QInputDialog, QFileDialog,
    QTabBar, QToolButton, QSlider, QStatusBar, QSystemTrayIcon, QStyle,
    QColorDialog, QFontDialog, QTextBrowser, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEngineProfile, QWebEngineSettings, QWebEnginePage,
    QWebEngineScript, QWebEngineDownloadItem
)
from PyQt5.QtCore import (
    QUrl, QTimer, pyqtSignal, Qt, QThread, pyqtSlot, QPropertyAnimation, 
    QRect, QSize, QSettings, QStandardPaths, QByteArray, QBuffer, QIODevice
)
from PyQt5.QtGui import (
    QIcon, QFont, QKeySequence, QPixmap, QPainter, QColor, QGuiApplication, 
    QContextMenuEvent, QPalette, QLinearGradient, QRadialGradient, QBrush,
    QFontDatabase, QDesktopServices
)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from math import ceil

# Enhanced Circular Loading Indicator
class CircularLoader(QWidget):
    def __init__(self, parent=None, color=QColor(70, 130, 180), penWidth=4, animationDuration=1000):
        super().__init__(parent)
        self.color = color
        self.penWidth = penWidth
        self.animationDuration = animationDuration
        self.numberOfLines = 12
        self.lineLength = 10
        self.innerRadius = 20
        self.currentCounter = 0
        self.isSpinning = False
        
        self.setFixedSize(80, 80)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.hide()
        
    def rotate(self):
        self.currentCounter += 1
        if self.currentCounter >= self.numberOfLines:
            self.currentCounter = 0
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        
        for i in range(self.numberOfLines):
            painter.save()
            painter.translate(self.width() / 2, self.height() / 2)
            rotateAngle = 360.0 * i / self.numberOfLines
            painter.rotate(rotateAngle)
            painter.translate(self.innerRadius, 0)
            
            distance = self.lineCountDistanceFromPrimary(i, self.currentCounter, self.numberOfLines)
            color = self.currentLineColor(distance, self.numberOfLines, 70.0, 20.0, self.color)
            painter.setBrush(color)
            painter.drawRoundedRect(0, -self.penWidth // 2, self.lineLength, self.penWidth, 70.0, 70.0)
            painter.restore()
            
    def lineCountDistanceFromPrimary(self, current, primary, totalNrOfLines):
        distance = primary - current
        if distance < 0:
            distance += totalNrOfLines
        return distance
        
    def currentLineColor(self, countDistance, totalNrOfLines, trailFadePerc, minOpacity, color):
        if countDistance == 0:
            return color
            
        minAlphaF = minOpacity / 100.0
        distanceThreshold = ceil((totalNrOfLines - 1) * trailFadePerc / 100.0)
        
        if countDistance > distanceThreshold:
            color.setAlphaF(minAlphaF)
        else:
            alphaDiff = color.alphaF() - minAlphaF
            gradient = alphaDiff / (distanceThreshold + 1.0)
            resultAlpha = color.alphaF() - gradient * countDistance
            resultAlpha = min(1.0, max(0.0, resultAlpha))
            color.setAlphaF(resultAlpha)
        return color
        
    def start(self):
        self.isSpinning = True
        self.show()
        if not self.timer.isActive():
            self.timer.start(1000 // (self.numberOfLines * 2))
            
    def stop(self):
        self.isSpinning = False
        self.hide()
        if self.timer.isActive():
            self.timer.stop()

# FIXED: Security-Enhanced Network Access Manager
class SecureNetworkAccessManager(QNetworkAccessManager):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocked_domains = set()
        self.ad_filters = [
            "doubleclick.net", "googleadservices.com", "googlesyndication.com",
            "amazon-adsystem.com", "ads.yahoo.com", "facebook.com/tr",
            "google-analytics.com", "googletagmanager.com"
        ]
        
    def createRequest(self, operation, request, outgoingData=None):
        url = request.url().toString()
        domain = urlparse(url).netloc
        
        # Block ads and trackers
        if any(ad_domain in domain for ad_domain in self.ad_filters):
            return super().createRequest(QNetworkAccessManager.GetOperation, 
                                       QNetworkRequest(QUrl("about:blank")))
        
        # Add security headers
        request.setRawHeader(b"X-Requested-With", b"SecureBrowser")
        request.setRawHeader(b"DNT", b"1")  # Do Not Track
        
        return super().createRequest(operation, request, outgoingData)

# Enhanced Tab Widget with proper new tab button
class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_browser = parent
        
        # Create the new tab button
        self.new_tab_button = QToolButton(self)
        self.new_tab_button.setText("➕")
        self.new_tab_button.setFixedSize(30, 30)
        self.new_tab_button.setToolTip("New Tab (Ctrl+T)")
        self.new_tab_button.setStyleSheet("""
            QToolButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f8f8, stop: 1 #e8e8e8);
                border: 1px solid #c0c0c0;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
            QToolButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e8e8e8, stop: 1 #d8d8d8);
                border-color: #a0a0a0;
            }
            QToolButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #d8d8d8, stop: 1 #c8c8c8);
            }
        """)
        
        self.new_tab_button.clicked.connect(self.on_new_tab_clicked)
        self.setTabsClosable(True)
        self.setMovable(True)
        
        # Connect signals for button positioning
        self.tabBar().tabMoved.connect(self.update_new_tab_button_position)
        self.currentChanged.connect(self.update_new_tab_button_position)
        
        self.update_new_tab_button_position()
        
    def on_new_tab_clicked(self):
        if self.parent_browser and hasattr(self.parent_browser, 'add_new_tab'):
            self.parent_browser.add_new_tab()
        
    def update_new_tab_button_position(self):
        try:
            total_width = 0
            for i in range(self.tabBar().count()):
                total_width += self.tabBar().tabRect(i).width()
            
            button_x = total_width + 5
            button_y = 3
            
            max_x = self.width() - self.new_tab_button.width() - 10
            if button_x > max_x:
                button_x = max_x
                
            self.new_tab_button.move(button_x, button_y)
            self.new_tab_button.show()
        except Exception as e:
            print(f"Error updating new tab button position: {e}")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_new_tab_button_position()
        
    def tabInserted(self, index):
        super().tabInserted(index)
        self.update_new_tab_button_position()
        
    def tabRemoved(self, index):
        super().tabRemoved(index)
        self.update_new_tab_button_position()

# Security-Enhanced WebEngine classes
class SecureWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up secure network access manager
        self.secure_nam = SecureNetworkAccessManager(self)
        
        # Configure security settings
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, False)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        
    def createWindow(self, window_type):
        if hasattr(self.view(), 'browser_window'):
            browser = self.view().browser_window
            if window_type == QWebEnginePage.WebBrowserTab:
                new_tab = browser.add_new_tab()
                return new_tab.webview.page() if new_tab else None
            elif window_type == QWebEnginePage.WebBrowserWindow:
                new_tab = browser.add_new_tab()
                return new_tab.webview.page() if new_tab else None
        return super().createWindow(window_type)

class SecureWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser_window = None
        self.zoom_factor = 1.0
        
    def createWindow(self, window_type):
        if self.browser_window:
            if window_type == QWebEnginePage.WebBrowserTab:
                new_tab = self.browser_window.add_new_tab()
                return new_tab.webview if new_tab else None
            elif window_type == QWebEnginePage.WebBrowserWindow:
                new_tab = self.browser_window.add_new_tab()
                return new_tab.webview if new_tab else None
        return super().createWindow(window_type)
        
    def contextMenuEvent(self, event):
        try:
            menu = self.page().createStandardContextMenu()
            if menu is None:
                return
                
            hit_test = self.page().hitTestContent(event.pos())
            actions = menu.actions()
            
            # Enhance existing actions
            for action in actions:
                if action.text() == "Open link in new window":
                    action.setText("🔗 Open Link in New Window")
                    action.triggered.disconnect()
                    action.triggered.connect(lambda: self.open_link_in_new_window(hit_test))
                elif action.text() == "Open link in new tab":
                    action.setText("📑 Open Link in New Tab")
                    action.triggered.disconnect()
                    action.triggered.connect(lambda: self.open_link_in_new_tab(hit_test))
                elif "Open link" in action.text():
                    action.setText("🌐 Open Link in This Tab")
                    
            # Add custom actions
            if hasattr(hit_test, 'linkUrl') and not hit_test.linkUrl().isEmpty():
                link_url = hit_test.linkUrl().toString()
                
                menu.addSeparator()
                copy_link_action = QAction("📋 Copy Link Address", menu)
                copy_link_action.triggered.connect(lambda: self.copy_link_to_clipboard(link_url))
                menu.addAction(copy_link_action)
                
                save_link_action = QAction("💾 Save Link As...", menu)
                save_link_action.triggered.connect(lambda: self.save_link(link_url))
                menu.addAction(save_link_action)
                
            # Add page actions
            menu.addSeparator()
            refresh_action = QAction("🔄 Refresh Page", menu)
            refresh_action.triggered.connect(self.reload)
            menu.addAction(refresh_action)
            
            view_source_action = QAction("📄 View Page Source", menu)
            view_source_action.triggered.connect(self.view_page_source)
            menu.addAction(view_source_action)
            
            menu.popup(event.globalPos())
            
        except Exception as e:
            print(f"Error in context menu: {e}")
            super().contextMenuEvent(event)
            
    def open_link_in_new_tab(self, hit_test):
        try:
            if hasattr(hit_test, 'linkUrl') and not hit_test.linkUrl().isEmpty():
                url = hit_test.linkUrl().toString()
                self.open_url_in_new_tab(url)
        except:
            pass
            
    def open_link_in_new_window(self, hit_test):
        try:
            if hasattr(hit_test, 'linkUrl') and not hit_test.linkUrl().isEmpty():
                url = hit_test.linkUrl().toString()
                self.open_url_in_new_tab(url)
        except:
            pass
            
    def open_url_in_new_tab(self, url):
        if self.browser_window:
            self.browser_window.add_new_tab(url)
            
    def copy_link_to_clipboard(self, url):
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(url)
            if self.browser_window:
                self.browser_window.status_label.setText("Link copied to clipboard")
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            
    def save_link(self, url):
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Link As", os.path.basename(url))
            if filename:
                # This would need proper implementation for downloading
                if self.browser_window:
                    self.browser_window.status_label.setText(f"Saving link to {filename}")
        except Exception as e:
            print(f"Error saving link: {e}")
            
    def view_page_source(self):
        if self.browser_window:
            self.browser_window.show_page_source()

# Enhanced Password Manager
class PasswordManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 Password Manager")
        self.setGeometry(300, 300, 600, 500)
        self.passwords = {}
        self.load_passwords()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Saved Passwords")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Password list
        self.password_tree = QTreeWidget()
        self.password_tree.setHeaderLabels(["Website", "Username", "Password"])
        self.password_tree.setColumnWidth(0, 200)
        self.password_tree.setColumnWidth(1, 150)
        self.load_password_list()
        layout.addWidget(self.password_tree)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Password")
        add_btn.clicked.connect(self.add_password)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_password)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_password)
        button_layout.addWidget(delete_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def load_password_list(self):
        self.password_tree.clear()
        for site, data in self.passwords.items():
            item = QTreeWidgetItem([site, data['username'], '*' * len(data['password'])])
            self.password_tree.addTopLevelItem(item)
            
    def add_password(self):
        site, ok1 = QInputDialog.getText(self, 'Add Password', 'Website:')
        if ok1 and site:
            username, ok2 = QInputDialog.getText(self, 'Add Password', 'Username:')
            if ok2:
                password, ok3 = QInputDialog.getText(self, 'Add Password', 'Password:', QLineEdit.Password)
                if ok3:
                    self.passwords[site] = {'username': username, 'password': password}
                    self.save_passwords()
                    self.load_password_list()
                    
    def edit_password(self):
        current = self.password_tree.currentItem()
        if current:
            site = current.text(0)
            if site in self.passwords:
                data = self.passwords[site]
                username, ok1 = QInputDialog.getText(self, 'Edit Password', 'Username:', text=data['username'])
                if ok1:
                    password, ok2 = QInputDialog.getText(self, 'Edit Password', 'Password:', QLineEdit.Password, data['password'])
                    if ok2:
                        self.passwords[site] = {'username': username, 'password': password}
                        self.save_passwords()
                        self.load_password_list()
                        
    def delete_password(self):
        current = self.password_tree.currentItem()
        if current:
            site = current.text(0)
            reply = QMessageBox.question(self, 'Delete Password', 
                                       f'Delete password for {site}?',
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.passwords[site]
                self.save_passwords()
                self.load_password_list()
                
    def save_passwords(self):
        try:
            # Simple encryption (in real app, use proper encryption)
            encrypted_data = {}
            for site, data in self.passwords.items():
                encrypted_data[site] = {
                    'username': base64.b64encode(data['username'].encode()).decode(),
                    'password': base64.b64encode(data['password'].encode()).decode()
                }
            with open('passwords.json', 'w') as f:
                json.dump(encrypted_data, f)
        except Exception as e:
            print(f"Error saving passwords: {e}")
            
    def load_passwords(self):
        try:
            if os.path.exists('passwords.json'):
                with open('passwords.json', 'r') as f:
                    encrypted_data = json.load(f)
                    for site, data in encrypted_data.items():
                        self.passwords[site] = {
                            'username': base64.b64decode(data['username']).decode(),
                            'password': base64.b64decode(data['password']).decode()
                        }
        except Exception as e:
            print(f"Error loading passwords: {e}")

# Enhanced Theme Manager
class ThemeManager:
    def __init__(self):
        self.themes = {
            'Light': self.light_theme(),
            'Dark': self.dark_theme(),
            'Blue': self.blue_theme(),
            'Green': self.green_theme()
        }
        
    def light_theme(self):
        return """
        QMainWindow {
            background-color: #f8f9fa;
            color: #333;
        }
        
        QTabWidget::pane {
            border: 1px solid #dee2e6;
            background-color: #ffffff;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #ffffff, stop: 1 #f8f9fa);
            border: 1px solid #dee2e6;
            border-bottom-color: #dee2e6;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            min-width: 120px;
            padding: 10px 16px;
            margin-right: 2px;
            color: #495057;
            font-weight: 500;
        }
        
        QTabBar::tab:selected {
            background: #ffffff;
            border-bottom-color: #ffffff;
            color: #007bff;
        }
        
        QTabBar::tab:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f8f9fa, stop: 1 #e9ecef);
        }
        
        QToolBar {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #ffffff, stop: 1 #f8f9fa);
            border: none;
            spacing: 8px;
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
        }
        
        QLineEdit {
            border: 2px solid #ced4da;
            border-radius: 25px;
            padding: 12px 20px;
            font-size: 14px;
            background-color: #ffffff;
            color: #495057;
        }
        
        QLineEdit:focus {
            border-color: #007bff;
            box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
        }
        
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #007bff, stop: 1 #0056b3);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #0056b3, stop: 1 #004085);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #004085, stop: 1 #002752);
        }
        
        QStatusBar {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
        }
        
        QMenuBar {
            background-color: #ffffff;
            color: #495057;
            border-bottom: 1px solid #dee2e6;
        }
        
        QMenuBar::item:selected {
            background-color: #e9ecef;
            border-radius: 4px;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 4px;
        }
        
        QMenu::item:selected {
            background-color: #e9ecef;
            border-radius: 4px;
        }
        """
        
    def dark_theme(self):
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #404040;
            background-color: #3c3c3c;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #4a4a4a, stop: 1 #3c3c3c);
            border: 1px solid #404040;
            border-bottom-color: #404040;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            min-width: 120px;
            padding: 10px 16px;
            margin-right: 2px;
            color: #ffffff;
            font-weight: 500;
        }
        
        QTabBar::tab:selected {
            background: #3c3c3c;
            border-bottom-color: #3c3c3c;
            color: #64b5f6;
        }
        
        QTabBar::tab:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #5a5a5a, stop: 1 #4a4a4a);
        }
        
        QToolBar {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #4a4a4a, stop: 1 #3c3c3c);
            border: none;
            spacing: 8px;
            padding: 8px;
            border-bottom: 1px solid #404040;
        }
        
        QLineEdit {
            border: 2px solid #606060;
            border-radius: 25px;
            padding: 12px 20px;
            font-size: 14px;
            background-color: #4a4a4a;
            color: #ffffff;
        }
        
        QLineEdit:focus {
            border-color: #64b5f6;
        }
        
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #64b5f6, stop: 1 #42a5f5);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #42a5f5, stop: 1 #2196f3);
        }
        
        QStatusBar {
            background-color: #3c3c3c;
            border-top: 1px solid #404040;
            color: #cccccc;
        }
        
        QMenuBar {
            background-color: #4a4a4a;
            color: #ffffff;
            border-bottom: 1px solid #404040;
        }
        
        QMenuBar::item:selected {
            background-color: #606060;
            border-radius: 4px;
        }
        
        QMenu {
            background-color: #4a4a4a;
            border: 1px solid #606060;
            border-radius: 6px;
            color: #ffffff;
        }
        
        QMenu::item:selected {
            background-color: #606060;
            border-radius: 4px;
        }
        """
        
    def blue_theme(self):
        return """
        QMainWindow {
            background-color: #e3f2fd;
            color: #0d47a1;
        }
        
        QTabWidget::pane {
            border: 1px solid #90caf9;
            background-color: #ffffff;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #bbdefb, stop: 1 #90caf9);
            border: 1px solid #90caf9;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            min-width: 120px;
            padding: 10px 16px;
            margin-right: 2px;
            color: #0d47a1;
            font-weight: 500;
        }
        
        QTabBar::tab:selected {
            background: #ffffff;
            color: #1976d2;
        }
        
        QToolBar {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #e3f2fd, stop: 1 #bbdefb);
            border-bottom: 1px solid #90caf9;
        }
        
        QLineEdit {
            border: 2px solid #90caf9;
            border-radius: 25px;
            padding: 12px 20px;
            background-color: #ffffff;
            color: #0d47a1;
        }
        
        QLineEdit:focus {
            border-color: #1976d2;
        }
        
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #2196f3, stop: 1 #1976d2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
        }
        """
        
    def green_theme(self):
        return """
        QMainWindow {
            background-color: #e8f5e8;
            color: #2e7d32;
        }
        
        QTabWidget::pane {
            border: 1px solid #81c784;
            background-color: #ffffff;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #c8e6c9, stop: 1 #a5d6a7);
            border: 1px solid #81c784;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            min-width: 120px;
            padding: 10px 16px;
            margin-right: 2px;
            color: #2e7d32;
            font-weight: 500;
        }
        
        QTabBar::tab:selected {
            background: #ffffff;
            color: #388e3c;
        }
        
        QToolBar {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #e8f5e8, stop: 1 #c8e6c9);
            border-bottom: 1px solid #81c784;
        }
        
        QLineEdit {
            border: 2px solid #81c784;
            border-radius: 25px;
            padding: 12px 20px;
            background-color: #ffffff;
            color: #2e7d32;
        }
        
        QLineEdit:focus {
            border-color: #388e3c;
        }
        
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #4caf50, stop: 1 #388e3c);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
        }
        """

# Enhanced Browser Tab
class BrowserTab(QWidget):
    def __init__(self, url="https://www.google.com", private_mode=False, browser_window=None):
        super().__init__()
        self.is_loading = False
        self.private_mode = private_mode
        self.browser_window = browser_window
        self.zoom_factor = 1.0
        
        if not isinstance(url, str):
            print(f"Warning: Invalid URL type {type(url)}, using default")
            url = "https://www.google.com"
            
        self.init_ui(url, private_mode)
        
    def init_ui(self, url, private_mode):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
        self.main_container = QWidget()
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Enhanced loader container
        self.loader_container = QWidget()
        self.loader_container.setFixedHeight(100)
        loader_layout = QVBoxLayout(self.loader_container)
        loader_layout.setAlignment(Qt.AlignCenter)
        
        self.circular_loader = CircularLoader(color=QColor(70, 130, 180))
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #666; font-size: 14px; margin-top: 10px;")
        
        loader_layout.addWidget(self.circular_loader, 0, Qt.AlignCenter)
        loader_layout.addWidget(self.loading_label)
        
        try:
            if not url or not isinstance(url, str):
                url = "https://www.google.com"
                
            if not url.startswith(('http://', 'https://')):
                if '.' in url:
                    url = 'https://' + url
                else:
                    url = "https://www.google.com"
            
            # Use secure WebEngine classes
            if private_mode:
                profile = QWebEngineProfile()
                self.webview = SecureWebEngineView()
                page = SecureWebEnginePage()
                page.setProfile(profile)
                self.webview.setPage(page)
            else:
                self.webview = SecureWebEngineView()
                page = SecureWebEnginePage()
                self.webview.setPage(page)
                
            # Set browser window reference
            self.webview.browser_window = self.browser_window
            
            # FIXED: Set initial zoom for better display
            initial_zoom = 1.2  # 120% for better readability
            self.webview.setZoomFactor(initial_zoom)
            self.zoom_factor = initial_zoom
            
            self.webview.setUrl(QUrl(url))
            
            # Connect signals
            self.webview.loadStarted.connect(self.load_started)
            self.webview.loadProgress.connect(self.load_progress)
            self.webview.loadFinished.connect(self.load_finished)
            
            main_layout.addWidget(self.loader_container)
            main_layout.addWidget(self.webview)
            
        except Exception as e:
            print(f"Error creating browser tab: {e}")
            self.webview = SecureWebEngineView()
            self.webview.setUrl(QUrl("https://www.google.com"))
            main_layout.addWidget(self.webview)
            
        layout.addWidget(self.main_container)
        self.setLayout(layout)
        
        # Initially hide loader
        self.loader_container.hide()
        
    def load_started(self):
        self.is_loading = True
        self.loader_container.show()
        self.circular_loader.start()
        self.loading_label.setText("Loading...")
        
    def load_progress(self, progress):
        self.loading_label.setText(f"Loading... {progress}%")
        
    def load_finished(self, success):
        self.is_loading = False
        self.circular_loader.stop()
        self.loader_container.hide()
        if not success:
            self.loading_label.setText("Failed to load page")
            
    def zoom_in(self):
        self.zoom_factor = min(3.0, self.zoom_factor + 0.1)
        self.webview.setZoomFactor(self.zoom_factor)
        
    def zoom_out(self):
        self.zoom_factor = max(0.3, self.zoom_factor - 0.1)
        self.webview.setZoomFactor(self.zoom_factor)
        
    def reset_zoom(self):
        self.zoom_factor = 1.2  # Default 120%
        self.webview.setZoomFactor(self.zoom_factor)

# Other classes remain the same (DownloadItem, DownloadManager, BookmarkManager, HistoryManager, SettingsDialog, ExtensionManager)
# Including them to keep the code complete...

class DownloadItem(QWidget):
    def __init__(self, download_item):
        super().__init__()
        self.download = download_item
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        
        self.filename_label = QLabel(os.path.basename(self.download.path()))
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Downloading...")
        
        layout.addWidget(self.filename_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        self.download.downloadProgress.connect(self.update_progress)
        self.download.finished.connect(self.download_finished)
        
    def update_progress(self, bytes_received, bytes_total):
        if bytes_total > 0:
            progress = int((bytes_received / bytes_total) * 100)
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"{progress}% ({bytes_received}/{bytes_total} bytes)")
            
    def download_finished(self):
        self.status_label.setText("Completed")
        self.progress_bar.setValue(100)

class DownloadManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📥 Download Manager")
        self.setGeometry(300, 300, 700, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Downloads")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        self.scroll_area = QScrollArea()
        self.download_widget = QWidget()
        self.download_layout = QVBoxLayout(self.download_widget)
        self.scroll_area.setWidget(self.download_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Clear Completed")
        clear_btn.clicked.connect(self.clear_completed)
        button_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def add_download(self, download_item):
        download_widget = DownloadItem(download_item)
        self.download_layout.addWidget(download_widget)
        
    def clear_completed(self):
        # Implementation for clearing completed downloads
        pass

class BookmarkManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔖 Bookmark Manager")
        self.setGeometry(300, 300, 600, 500)
        self.parent_browser = parent
        self.init_ui()
        self.load_bookmarks()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Bookmarks")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        self.bookmark_list = QListWidget()
        self.bookmark_list.itemDoubleClicked.connect(self.open_bookmark)
        
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("🌐 Open")
        open_btn.clicked.connect(self.open_selected_bookmark)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_bookmark)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(self.bookmark_list)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_bookmarks(self):
        if hasattr(self.parent_browser, 'bookmarks'):
            self.bookmark_list.clear()
            for title, url in self.parent_browser.bookmarks.items():
                self.bookmark_list.addItem(f"🔖 {title} - {url}")
                
    def open_bookmark(self, item):
        url = item.text().split(" - ")[-1]
        if self.parent_browser:
            self.parent_browser.navigate_to_specific_url(url)
        self.close()
        
    def open_selected_bookmark(self):
        current_item = self.bookmark_list.currentItem()
        if current_item:
            self.open_bookmark(current_item)
            
    def delete_bookmark(self):
        current_item = self.bookmark_list.currentItem()
        if current_item:
            title = current_item.text().split(" - ")[0].replace("🔖 ", "")
            if title in self.parent_browser.bookmarks:
                del self.parent_browser.bookmarks[title]
                self.parent_browser.save_bookmarks()
                self.load_bookmarks()

class HistoryManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📜 History")
        self.setGeometry(300, 300, 700, 600)
        self.parent_browser = parent
        self.init_ui()
        self.load_history()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Browsing History")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.open_history_item)
        
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("🌐 Open")
        open_btn.clicked.connect(self.open_selected_item)
        
        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.clicked.connect(self.clear_history)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(self.history_list)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_history(self):
        if hasattr(self.parent_browser, 'history'):
            self.history_list.clear()
            for entry in reversed(self.parent_browser.history):
                timestamp = entry['timestamp']
                title = entry['title']
                url = entry['url']
                self.history_list.addItem(f"🕒 [{timestamp}] {title} - {url}")
                
    def open_history_item(self, item):
        url = item.text().split(" - ")[-1]
        if self.parent_browser:
            self.parent_browser.navigate_to_specific_url(url)
        self.close()
        
    def open_selected_item(self):
        current_item = self.history_list.currentItem()
        if current_item:
            self.open_history_item(current_item)
            
    def clear_history(self):
        reply = QMessageBox.question(self, 'Clear History', 
                                   'Are you sure you want to clear all history?',
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.parent_browser.history = []
            self.parent_browser.save_history()
            self.load_history()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Settings")
        self.setGeometry(300, 300, 500, 600)
        self.parent_browser = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Browser Settings")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Scroll area for settings
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # General Settings
        general_group = QGroupBox("🌐 General")
        general_layout = QFormLayout()
        
        self.homepage_edit = QLineEdit(self.parent_browser.homepage)
        general_layout.addRow("Homepage:", self.homepage_edit)
        
        self.download_path_edit = QLineEdit(self.parent_browser.download_path)
        general_layout.addRow("Download Path:", self.download_path_edit)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Light', 'Dark', 'Blue', 'Green'])
        self.theme_combo.setCurrentText(getattr(self.parent_browser, 'current_theme', 'Light'))
        general_layout.addRow("Theme:", self.theme_combo)
        
        # Zoom level
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(50)
        self.zoom_slider.setMaximum(300)
        self.zoom_slider.setValue(120)  # Default 120%
        self.zoom_label = QLabel("120%")
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_label.setText(f"{v}%"))
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_label)
        general_layout.addRow("Default Zoom:", zoom_layout)
        
        general_group.setLayout(general_layout)
        
        # Privacy Settings
        privacy_group = QGroupBox("🔒 Privacy & Security")
        privacy_layout = QFormLayout()
        
        self.private_browsing = QCheckBox("Enable Private Browsing by Default")
        self.javascript_enabled = QCheckBox("Enable JavaScript")
        self.javascript_enabled.setChecked(True)
        self.images_enabled = QCheckBox("Load Images")
        self.images_enabled.setChecked(True)
        self.plugins_enabled = QCheckBox("Enable Plugins")
        self.ad_blocking = QCheckBox("Enable Ad Blocking")
        self.ad_blocking.setChecked(True)
        
        privacy_layout.addRow(self.private_browsing)
        privacy_layout.addRow(self.javascript_enabled)
        privacy_layout.addRow(self.images_enabled)
        privacy_layout.addRow(self.plugins_enabled)
        privacy_layout.addRow(self.ad_blocking)
        
        privacy_group.setLayout(privacy_layout)
        
        # Advanced Settings
        advanced_group = QGroupBox("🔧 Advanced")
        advanced_layout = QFormLayout()
        
        self.auto_save_session = QCheckBox("Auto-save Session")
        self.auto_save_session.setChecked(True)
        self.developer_tools = QCheckBox("Enable Developer Tools")
        self.smooth_scrolling = QCheckBox("Smooth Scrolling")
        self.smooth_scrolling.setChecked(True)
        
        advanced_layout.addRow(self.auto_save_session)
        advanced_layout.addRow(self.developer_tools)
        advanced_layout.addRow(self.smooth_scrolling)
        
        advanced_group.setLayout(advanced_layout)
        
        scroll_layout.addWidget(general_group)
        scroll_layout.addWidget(privacy_group)
        scroll_layout.addWidget(advanced_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_settings)
        
        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.clicked.connect(self.reset_settings)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def save_settings(self):
        self.parent_browser.homepage = self.homepage_edit.text()
        self.parent_browser.download_path = self.download_path_edit.text()
        
        # Apply theme
        selected_theme = self.theme_combo.currentText()
        self.parent_browser.apply_theme(selected_theme)
        
        # Apply zoom to all tabs
        zoom_value = self.zoom_slider.value() / 100.0
        for i in range(self.parent_browser.tabs.count()):
            tab = self.parent_browser.tabs.widget(i)
            if hasattr(tab, 'webview'):
                tab.webview.setZoomFactor(zoom_value)
                tab.zoom_factor = zoom_value
        
        # Apply other settings
        for i in range(self.parent_browser.tabs.count()):
            tab = self.parent_browser.tabs.widget(i)
            if hasattr(tab, 'webview'):
                settings = tab.webview.settings()
                settings.setAttribute(QWebEngineSettings.JavascriptEnabled, 
                                    self.javascript_enabled.isChecked())
                settings.setAttribute(QWebEngineSettings.AutoLoadImages,
                                    self.images_enabled.isChecked())
                settings.setAttribute(QWebEngineSettings.PluginsEnabled,
                                    self.plugins_enabled.isChecked())
        
        self.parent_browser.save_settings()
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.close()
        
    def reset_settings(self):
        reply = QMessageBox.question(self, 'Reset Settings', 
                                   'Reset all settings to defaults?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.homepage_edit.setText("https://www.google.com")
            self.download_path_edit.setText(os.path.expanduser("~/Downloads"))
            self.theme_combo.setCurrentText("Light")
            self.zoom_slider.setValue(120)
            self.javascript_enabled.setChecked(True)
            self.images_enabled.setChecked(True)
            self.ad_blocking.setChecked(True)

class ExtensionManager:
    def __init__(self, browser):
        self.browser = browser
        self.extensions = {}
        self.extension_dir = "extensions"
        self.load_extensions()
        
    def load_extensions(self):
        if not os.path.exists(self.extension_dir):
            os.makedirs(self.extension_dir)
            
        for filename in os.listdir(self.extension_dir):
            if filename.endswith('.json'):
                self.load_extension(filename)
                
    def load_extension(self, filename):
        try:
            with open(os.path.join(self.extension_dir, filename), 'r') as f:
                extension_data = json.load(f)
                self.extensions[extension_data['id']] = extension_data
                print(f"Loaded extension: {extension_data['name']}")
        except Exception as e:
            print(f"Error loading extension {filename}: {e}")
            
    def install_extension(self, extension_path):
        try:
            with open(extension_path, 'r') as f:
                extension_data = json.load(f)
                
            filename = f"{extension_data['id']}.json"
            target_path = os.path.join(self.extension_dir, filename)
            
            with open(target_path, 'w') as f:
                json.dump(extension_data, f, indent=2)
                
            self.extensions[extension_data['id']] = extension_data
            QMessageBox.information(self.browser, "Extension Installed", 
                                  f"Extension '{extension_data['name']}' installed successfully!")
        except Exception as e:
            QMessageBox.critical(self.browser, "Error", f"Failed to install extension: {e}")

# Main Browser Class
class WebKitBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.homepage = "https://www.google.com"
        self.download_path = os.path.expanduser("~/Downloads")
        self.bookmarks = {}
        self.history = []
        self.private_mode = False
        self.current_theme = 'Light'
        
        # FIXED: Proper window sizing and positioning
        self.init_geometry()
        self.init_ui()
        self.apply_theme('Light')
        self.load_settings()
        self.load_bookmarks()
        self.load_history()
        self.setup_shortcuts()
        
        # Managers
        self.extension_manager = ExtensionManager(self)
        self.download_manager = DownloadManager(self)
        self.password_manager = PasswordManager(self)
        self.theme_manager = ThemeManager()
        
    def init_geometry(self):
        """FIXED: Proper window sizing and positioning for different screen sizes"""
        # Get screen geometry
        screen = QApplication.desktop().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Calculate window size (80% of screen)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # Calculate position (center of screen)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Ensure window doesn't go off screen
        x = max(0, x)
        y = max(0, y)
        
        self.setGeometry(x, y, window_width, window_height)
        
    def init_ui(self):
        self.setWindowTitle("🌐 Enhanced Secure Browser")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Custom tab widget
        self.tabs = CustomTabWidget(self)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        
        # Create enhanced toolbar
        self.create_toolbar()
        
        # Status bar with additional info
        self.create_status_bar()
        
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Start with one tab
        self.add_new_tab()
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('📁 File')
        
        new_tab_action = QAction('🆕 New Tab', self)
        new_tab_action.setShortcut('Ctrl+T')
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)
        
        new_private_tab_action = QAction('🔒 New Private Tab', self)
        new_private_tab_action.setShortcut('Ctrl+Shift+P')
        new_private_tab_action.triggered.connect(self.add_private_tab)
        file_menu.addAction(new_private_tab_action)
        
        file_menu.addSeparator()
        
        save_page_action = QAction('💾 Save Page As...', self)
        save_page_action.setShortcut('Ctrl+S')
        save_page_action.triggered.connect(self.save_page)
        file_menu.addAction(save_page_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction('❌ Close Tab', self)
        close_tab_action.setShortcut('Ctrl+W')
        close_tab_action.triggered.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))
        file_menu.addAction(close_tab_action)
        
        exit_action = QAction('🚪 Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('✏️ Edit')
        
        find_action = QAction('🔍 Find...', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)
        
        # View menu
        view_menu = menubar.addMenu('👁️ View')
        
        zoom_in_action = QAction('🔍➕ Zoom In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('🔍➖ Zoom Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction('🔍🔄 Reset Zoom', self)
        reset_zoom_action.setShortcut('Ctrl+0')
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction('🖥️ Toggle Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Bookmarks menu
        bookmarks_menu = menubar.addMenu('🔖 Bookmarks')
        
        add_bookmark_action = QAction('➕ Add Bookmark', self)
        add_bookmark_action.setShortcut('Ctrl+D')
        add_bookmark_action.triggered.connect(self.add_bookmark)
        bookmarks_menu.addAction(add_bookmark_action)
        
        manage_bookmarks_action = QAction('📂 Manage Bookmarks', self)
        manage_bookmarks_action.triggered.connect(self.show_bookmark_manager)
        bookmarks_menu.addAction(manage_bookmarks_action)
        
        # History menu
        history_menu = menubar.addMenu('📜 History')
        
        show_history_action = QAction('📖 Show History', self)
        show_history_action.setShortcut('Ctrl+H')
        show_history_action.triggered.connect(self.show_history)
        history_menu.addAction(show_history_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('🔧 Tools')
        
        downloads_action = QAction('📥 Downloads', self)
        downloads_action.setShortcut('Ctrl+J')
        downloads_action.triggered.connect(self.show_download_manager)
        tools_menu.addAction(downloads_action)
        
        password_manager_action = QAction('🔐 Password Manager', self)
        password_manager_action.triggered.connect(self.show_password_manager)
        tools_menu.addAction(password_manager_action)
        
        developer_tools_action = QAction('🛠️ Developer Tools', self)
        developer_tools_action.setShortcut('F12')
        developer_tools_action.triggered.connect(self.toggle_developer_tools)
        tools_menu.addAction(developer_tools_action)
        
        settings_action = QAction('⚙️ Settings', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Extensions menu
        extensions_menu = menubar.addMenu('🧩 Extensions')
        
        install_extension_action = QAction('📦 Install Extension', self)
        install_extension_action.triggered.connect(self.install_extension)
        extensions_menu.addAction(install_extension_action)
        
        manage_extensions_action = QAction('🔧 Manage Extensions', self)
        manage_extensions_action.triggered.connect(self.show_extension_manager)
        extensions_menu.addAction(manage_extensions_action)
        
    def create_toolbar(self):
        nav_bar = QToolBar()
        nav_bar.setMovable(False)
        nav_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(nav_bar)
        
        # Navigation buttons
        back_btn = QAction("◀️", self)
        back_btn.setToolTip("Go Back (Alt+Left)")
        back_btn.triggered.connect(self.go_back)
        nav_bar.addAction(back_btn)
        
        forward_btn = QAction("▶️", self)
        forward_btn.setToolTip("Go Forward (Alt+Right)")
        forward_btn.triggered.connect(self.go_forward)
        nav_bar.addAction(forward_btn)
        
        reload_btn = QAction("🔄", self)
        reload_btn.setToolTip("Reload (F5)")
        reload_btn.triggered.connect(self.reload_page)
        nav_bar.addAction(reload_btn)
        
        home_btn = QAction("🏠", self)
        home_btn.setToolTip("Home")
        home_btn.triggered.connect(self.go_home)
        nav_bar.addAction(home_btn)
        
        nav_bar.addSeparator()
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("🔍 Enter URL or search...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)
        
        nav_bar.addSeparator()
        
        # Action buttons
        bookmark_btn = QAction("⭐", self)
        bookmark_btn.setToolTip("Add Bookmark (Ctrl+D)")
        bookmark_btn.triggered.connect(self.add_bookmark)
        nav_bar.addAction(bookmark_btn)
        
        # Zoom controls
        zoom_out_btn = QAction("🔍➖", self)
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.triggered.connect(self.zoom_out)
        nav_bar.addAction(zoom_out_btn)
        
        zoom_in_btn = QAction("🔍➕", self)
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.triggered.connect(self.zoom_in)
        nav_bar.addAction(zoom_in_btn)
        
    def create_status_bar(self):
        self.status_bar = self.statusBar()
        
        # Main status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Add permanent widgets
        self.status_bar.addPermanentWidget(QLabel(" | "))
        
        # Zoom level
        self.zoom_level_label = QLabel("120%")
        self.status_bar.addPermanentWidget(self.zoom_level_label)
        
        self.status_bar.addPermanentWidget(QLabel(" | "))
        
        # Security indicator
        self.security_label = QLabel("🔒 Secure")
        self.status_bar.addPermanentWidget(self.security_label)
        
    def apply_theme(self, theme_name):
        """Apply selected theme"""
        if theme_name in self.theme_manager.themes:
            self.setStyleSheet(self.theme_manager.themes[theme_name])
            self.current_theme = theme_name
            
    def setup_shortcuts(self):
        # Additional shortcuts
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.reload_page)
        
        address_bar_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        address_bar_shortcut.activated.connect(self.focus_address_bar)
        
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.show_find_dialog)
        
        # Navigation shortcuts
        back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        back_shortcut.activated.connect(self.go_back)
        
        forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        forward_shortcut.activated.connect(self.go_forward)
        
        # Tab shortcuts
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))
        
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.add_new_tab)
        
    def add_new_tab(self, url=None):
        try:
            if url is None or not isinstance(url, str):
                url = self.homepage
                
            if not url.strip():
                url = self.homepage
                
            browser_tab = BrowserTab(url, self.private_mode, self)
            
            title = "🆕 New Tab"
            if self.private_mode:
                title = "🔒 Private Tab"
                
            i = self.tabs.addTab(browser_tab, title)
            self.tabs.setCurrentIndex(i)
            
            if hasattr(browser_tab, 'webview') and browser_tab.webview:
                try:
                    browser_tab.webview.urlChanged.connect(
                        lambda qurl: self.update_tab_title(qurl, browser_tab)
                    )
                    
                    browser_tab.webview.titleChanged.connect(
                        lambda title: self.update_tab_title_with_text(title, browser_tab)
                    )
                    
                    browser_tab.webview.loadFinished.connect(
                        lambda ok: self.page_load_finished(ok, browser_tab)
                    )
                    
                    # Connect download signal if available
                    try:
                        if hasattr(browser_tab.webview.page(), 'profile'):
                            browser_tab.webview.page().profile().downloadRequested.connect(self.handle_download)
                    except:
                        pass
                        
                except Exception as signal_error:
                    print(f"Warning: Could not connect signals: {signal_error}")
                    
            return browser_tab
            
        except Exception as e:
            error_msg = f"Failed to create new tab: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return None
        
    def add_private_tab(self):
        old_private_mode = self.private_mode
        self.private_mode = True
        result = self.add_new_tab()
        self.private_mode = old_private_mode
        return result
        
    def close_current_tab(self, index):
        if self.tabs.count() <= 1:
            self.close()
        else:
            self.tabs.removeTab(index)
            
    def zoom_in(self):
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'zoom_in'):
            current_tab.zoom_in()
            zoom_percent = int(current_tab.zoom_factor * 100)
            self.zoom_level_label.setText(f"{zoom_percent}%")
            
    def zoom_out(self):
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'zoom_out'):
            current_tab.zoom_out()
            zoom_percent = int(current_tab.zoom_factor * 100)
            self.zoom_level_label.setText(f"{zoom_percent}%")
            
    def reset_zoom(self):
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'reset_zoom'):
            current_tab.reset_zoom()
            zoom_percent = int(current_tab.zoom_factor * 100)
            self.zoom_level_label.setText(f"{zoom_percent}%")
            
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def save_page(self):
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'webview'):
            url = current_tab.webview.url().toString()
            filename, _ = QFileDialog.getSaveFileName(self, "Save Page As", f"page.html", "HTML files (*.html)")
            if filename:
                self.status_label.setText(f"Saving page to {filename}")
                
    def show_page_source(self):
        current_tab = self.tabs.currentWidget()
        if current_tab and hasattr(current_tab, 'webview'):
            # This would need proper implementation
            source_dialog = QDialog(self)
            source_dialog.setWindowTitle("📄 Page Source")
            source_dialog.setGeometry(300, 300, 800, 600)
            
            layout = QVBoxLayout()
            source_text = QTextBrowser()
            source_text.setPlainText("Page source would be displayed here...")
            layout.addWidget(source_text)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(source_dialog.close)
            layout.addWidget(close_btn)
            
            source_dialog.setLayout(layout)
            source_dialog.exec_()
            
    def show_password_manager(self):
        self.password_manager.show()
        
    def handle_download(self, download):
        try:
            path = os.path.join(self.download_path, download.suggestedFileName())
            download.setPath(path)
            download.accept()
            self.download_manager.add_download(download)
            self.status_label.setText(f"📥 Downloading: {download.suggestedFileName()}")
        except Exception as e:
            print(f"Error handling download: {e}")
            self.status_label.setText("❌ Download error occurred")
    
    def install_extension(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Install Extension", "", "JSON files (*.json)")
        if file_path:
            self.extension_manager.install_extension(file_path)
            
    def show_extension_manager(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("🧩 Extension Manager")
        dialog.setGeometry(300, 300, 600, 500)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Installed Extensions")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        ext_list = QListWidget()
        for ext_id, ext_data in self.extension_manager.extensions.items():
            ext_list.addItem(f"🧩 {ext_data['name']} - v{ext_data.get('version', '1.0')}")
            
        layout.addWidget(ext_list)
        
        button_layout = QHBoxLayout()
        install_btn = QPushButton("📦 Install New Extension")
        install_btn.clicked.connect(self.install_extension)
        button_layout.addWidget(install_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()
        
    def update_tab_title(self, qurl, browser_tab):
        try:
            i = self.tabs.indexOf(browser_tab)
            if i >= 0:
                domain = urlparse(qurl.toString()).netloc or "New Tab"
                if len(domain) > 15:
                    domain = domain[:12] + "..."
                
                # Add security indicator
                is_secure = qurl.scheme() == 'https'
                icon = "🔒" if is_secure else "🔓"
                self.tabs.setTabText(i, f"{icon} {domain}")
                
                # Update security label
                if browser_tab == self.tabs.currentWidget():
                    self.security_label.setText("🔒 Secure" if is_secure else "🔓 Insecure")
                
            if browser_tab == self.tabs.currentWidget():
                self.url_bar.setText(qurl.toString())
        except Exception as e:
            print(f"Error updating tab title: {e}")
            
    def update_tab_title_with_text(self, title, browser_tab):
        try:
            i = self.tabs.indexOf(browser_tab)
            if i >= 0 and title:
                if len(title) > 15:
                    title = title[:12] + "..."
                
                # Keep security indicator
                current_text = self.tabs.tabText(i)
                icon = "🔒" if current_text.startswith("🔒") else "🔓"
                self.tabs.setTabText(i, f"{icon} {title}")
        except Exception as e:
            print(f"Error updating tab title with text: {e}")
            
    def page_load_finished(self, success, browser_tab):
        try:
            if success and browser_tab == self.tabs.currentWidget():
                url = browser_tab.webview.url().toString()
                title = browser_tab.webview.title() or url
                
                # Add to history (if not private mode)
                current_tab_private = "🔒" in self.tabs.tabText(self.tabs.indexOf(browser_tab))
                if not current_tab_private:
                    self.add_to_history(title, url)
                    
                self.status_label.setText("✅ Ready")
            elif not success:
                self.status_label.setText("❌ Failed to load page")
        except Exception as e:
            print(f"Error in page load finished: {e}")
            
    def add_to_history(self, title, url):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_entry = {
                'timestamp': timestamp,
                'title': title,
                'url': url
            }
            
            # Avoid duplicates
            if not any(entry['url'] == url for entry in self.history[-10:]):
                self.history.append(history_entry)
                
            # Keep only last 1000 entries
            if len(self.history) > 1000:
                self.history = self.history[-1000:]
                
            self.save_history()
        except Exception as e:
            print(f"Error adding to history: {e}")
            
    def current_browser(self):
        current_widget = self.tabs.currentWidget()
        return current_widget.webview if current_widget and hasattr(current_widget, 'webview') else None
        
    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return
            
        # Enhanced URL processing
        if " " in url and not url.startswith("http") and "." not in url.split()[0]:
            # Search query
            url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        elif not url.startswith("http"):
            if "." in url:
                url = "https://" + url
            else:
                url = f"https://www.google.com/search?q={url}"
                
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(url))
            self.status_label.setText("🔄 Loading...")
            
    def navigate_to_specific_url(self, url):
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(url))
            
    def update_url_bar(self, index):
        browser = self.current_browser()
        if browser:
            qurl = browser.url()
            self.url_bar.setText(qurl.toString())
            
            # Update zoom level display
            current_tab = self.tabs.currentWidget()
            if current_tab and hasattr(current_tab, 'zoom_factor'):
                zoom_percent = int(current_tab.zoom_factor * 100)
                self.zoom_level_label.setText(f"{zoom_percent}%")
            
    def go_back(self):
        browser = self.current_browser()
        if browser:
            browser.back()
            
    def go_forward(self):
        browser = self.current_browser()
        if browser:
            browser.forward()
            
    def reload_page(self):
        browser = self.current_browser()
        if browser:
            browser.reload()
            self.status_label.setText("🔄 Reloading...")
            
    def go_home(self):
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(self.homepage))
            
    def focus_address_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()
        
    def show_find_dialog(self):
        browser = self.current_browser()
        if browser:
            text, ok = QInputDialog.getText(self, '🔍 Find', 'Find text:')
            if ok and text:
                browser.findText(text)
                
    def add_bookmark(self):
        browser = self.current_browser()
        if browser:
            url = browser.url().toString()
            title = browser.title() or url
            
            bookmark_name, ok = QInputDialog.getText(self, '⭐ Add Bookmark', 
                                                   'Bookmark name:', text=title)
            if ok and bookmark_name:
                self.bookmarks[bookmark_name] = url
                self.save_bookmarks()
                QMessageBox.information(self, "Bookmark", "Bookmark added successfully! ⭐")
                
    def show_bookmark_manager(self):
        bookmark_manager = BookmarkManager(self)
        bookmark_manager.exec_()
        
    def show_history(self):
        history_manager = HistoryManager(self)
        history_manager.exec_()
        
    def show_download_manager(self):
        self.download_manager.show()
        
    def show_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()
        
    def toggle_developer_tools(self):
        browser = self.current_browser()
        if browser:
            QMessageBox.information(self, "Developer Tools", 
                                  "🛠️ Developer tools would be integrated here in a full implementation.")
                
    def save_bookmarks(self):
        try:
            with open('bookmarks.json', 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
            
    def load_bookmarks(self):
        try:
            if os.path.exists('bookmarks.json'):
                with open('bookmarks.json', 'r') as f:
                    self.bookmarks = json.load(f)
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            
    def save_history(self):
        try:
            with open('history.json', 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def load_history(self):
        try:
            if os.path.exists('history.json'):
                with open('history.json', 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            
    def save_settings(self):
        settings = {
            'homepage': self.homepage,
            'download_path': self.download_path,
            'window_geometry': [self.x(), self.y(), self.width(), self.height()],
            'theme': self.current_theme
        }
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.homepage = settings.get('homepage', 'https://www.google.com')
                    self.download_path = settings.get('download_path', 
                                                    os.path.expanduser("~/Downloads"))
                    self.current_theme = settings.get('theme', 'Light')
                    
                    # Restore window geometry (but ensure it's on screen)
                    geometry = settings.get('window_geometry')
                    if geometry:
                        x, y, w, h = geometry
                        screen = QApplication.desktop().screenGeometry()
                        # Ensure window fits on screen
                        x = max(0, min(x, screen.width() - w))
                        y = max(0, min(y, screen.height() - h))
                        self.setGeometry(x, y, w, h)
                        
                    self.apply_theme(self.current_theme)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def closeEvent(self, event):
        self.save_settings()
        self.save_bookmarks()
        self.save_history()
        event.accept()

if __name__ == "__main__":
    # FIXED: Comprehensive scaling setup
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, False)
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Enhanced Secure Browser")
    app.setApplicationVersion("2.0")
    
    # Additional scaling fixes
    try:
        screen = QGuiApplication.primaryScreen()
        screen.setProperty("devicePixelRatio", 1.0)
    except:
        pass
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show browser
    window = WebKitBrowser()
    window.show()
    
    sys.exit(app.exec_())
