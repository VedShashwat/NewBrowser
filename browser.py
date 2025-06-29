import sys
import json
import os
from datetime import datetime

# Handle scaling issues before importing PyQt5
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QMenu, QMenuBar,
    QProgressBar, QLabel, QSplitter, QListWidget, QTextEdit, QPushButton,
    QDialog, QFormLayout, QSpinBox, QCheckBox, QComboBox, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QShortcut, QInputDialog, QFileDialog,
    QTabBar, QToolButton
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings, QWebEnginePage
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, Qt, QThread, pyqtSlot, QPropertyAnimation, QRect, QSize
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QPixmap, QPainter, QColor, QGuiApplication, QContextMenuEvent
from urllib.parse import urlparse
from math import ceil

# Circular Loading Indicator
class CircularLoader(QWidget):
    def __init__(self, parent=None, color=QColor(70, 130, 180), penWidth=3, animationDuration=1000):
        super().__init__(parent)
        self.color = color
        self.penWidth = penWidth
        self.animationDuration = animationDuration
        self.numberOfLines = 12
        self.lineLength = 8
        self.innerRadius = 15
        self.currentCounter = 0
        self.isSpinning = False
        
        self.setFixedSize(60, 60)
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

# FIXED: Properly working Tab Widget with moveable new tab button
class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_browser = parent
        
        # Create the new tab button
        self.new_tab_button = QToolButton(self)
        self.new_tab_button.setText("➕")
        self.new_tab_button.setFixedSize(45, 45)
        self.new_tab_button.setToolTip("New Tab")
        self.new_tab_button.setStyleSheet("""
            QToolButton {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # Connect the button to add new tab
        self.new_tab_button.clicked.connect(self.on_new_tab_clicked)
        
        # Connect signals to update button position
        self.tabBar().tabMoved.connect(self.update_new_tab_button_position)
        self.currentChanged.connect(self.update_new_tab_button_position)
        
        # Set initial properties
        self.setTabsClosable(True)
        self.setMovable(True)
        
        # Update button position initially
        self.update_new_tab_button_position()
        
    def on_new_tab_clicked(self):
        """Handle new tab button click"""
        if self.parent_browser and hasattr(self.parent_browser, 'add_new_tab'):
            self.parent_browser.add_new_tab()
        
    def update_new_tab_button_position(self):
        """Update the position of the new tab button"""
        try:
            # Calculate total width of all tabs
            total_width = 0
            tab_count = self.tabBar().count()
            
            for i in range(tab_count):
                total_width += self.tabBar().tabRect(i).width()
            
            # Position the button right after the last tab
            button_x = total_width + 2  # Small gap
            button_y = 2  # Small vertical offset
            
            # Make sure button doesn't go beyond the widget width
            max_x = self.width() - self.new_tab_button.width() - 5
            if button_x > max_x:
                button_x = max_x
                
            self.new_tab_button.move(button_x, button_y)
            self.new_tab_button.show()
            
        except Exception as e:
            print(f"Error updating new tab button position: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.update_new_tab_button_position()
        
    def tabInserted(self, index):
        """Handle tab insertion"""
        super().tabInserted(index)
        self.update_new_tab_button_position()
        
    def tabRemoved(self, index):
        """Handle tab removal"""
        super().tabRemoved(index)
        self.update_new_tab_button_position()

# Custom WebEngine classes with proper context menu
class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def createWindow(self, window_type):
        """Handle requests to open new windows/tabs"""
        if hasattr(self.view(), 'browser_window'):
            browser = self.view().browser_window
            if window_type == QWebEnginePage.WebBrowserTab:
                new_tab = browser.add_new_tab()
                return new_tab.webview.page() if new_tab else None
            elif window_type == QWebEnginePage.WebBrowserWindow:
                new_tab = browser.add_new_tab()
                return new_tab.webview.page() if new_tab else None
        return super().createWindow(window_type)

class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser_window = None
        
    def createWindow(self, window_type):
        """Handle requests to open new windows/tabs"""
        if self.browser_window:
            if window_type == QWebEnginePage.WebBrowserTab:
                new_tab = self.browser_window.add_new_tab()
                return new_tab.webview if new_tab else None
            elif window_type == QWebEnginePage.WebBrowserWindow:
                new_tab = self.browser_window.add_new_tab()
                return new_tab.webview if new_tab else None
        return super().createWindow(window_type)
        
    def contextMenuEvent(self, event):
        """Handle right-click context menu with proper options"""
        try:
            # Create standard context menu
            menu = self.page().createStandardContextMenu()
            
            if menu is None:
                return
                
            # Get the hit test result to check if we're over a link
            hit_test = self.page().hitTestContent(event.pos())
            
            actions = menu.actions()
            
            # Find existing actions and modify them
            for action in actions:
                if action.text() == "Open link in new window":
                    action.setText("Open Link in New Window")
                    # Connect to our custom handler
                    action.triggered.disconnect()
                    action.triggered.connect(lambda: self.open_link_in_new_window(hit_test))
                elif action.text() == "Open link in new tab":
                    action.setText("Open Link in New Tab")
                    # Connect to our custom handler
                    action.triggered.disconnect()
                    action.triggered.connect(lambda: self.open_link_in_new_tab(hit_test))
                elif "Open link" in action.text():
                    action.setText("Open Link in This Tab")
                    
            # If we're over a link, ensure new tab/window options are available
            if hasattr(hit_test, 'linkUrl') and not hit_test.linkUrl().isEmpty():
                link_url = hit_test.linkUrl().toString()
                
                # Check if new tab/window actions exist, if not add them
                has_new_tab = any("New Tab" in action.text() for action in actions)
                has_new_window = any("New Window" in action.text() for action in actions)
                
                if not has_new_tab:
                    new_tab_action = QAction("Open Link in New Tab", menu)
                    new_tab_action.triggered.connect(lambda: self.open_url_in_new_tab(link_url))
                    menu.addAction(new_tab_action)
                    
                if not has_new_window:
                    new_window_action = QAction("Open Link in New Window", menu)
                    new_window_action.triggered.connect(lambda: self.open_url_in_new_tab(link_url))
                    menu.addAction(new_window_action)
                    
                # Add separator and additional options
                menu.addSeparator()
                copy_link_action = QAction("Copy Link Address", menu)
                copy_link_action.triggered.connect(lambda: self.copy_link_to_clipboard(link_url))
                menu.addAction(copy_link_action)
                
            menu.popup(event.globalPos())
            
        except Exception as e:
            print(f"Error in context menu: {e}")
            # Fallback to default context menu
            super().contextMenuEvent(event)
            
    def open_link_in_new_tab(self, hit_test):
        """Open link in new tab"""
        try:
            if hasattr(hit_test, 'linkUrl') and not hit_test.linkUrl().isEmpty():
                url = hit_test.linkUrl().toString()
                self.open_url_in_new_tab(url)
        except:
            pass
            
    def open_link_in_new_window(self, hit_test):
        """Open link in new window (for now, opens in new tab)"""
        try:
            if hasattr(hit_test, 'linkUrl') and not hit_test.linkUrl().isEmpty():
                url = hit_test.linkUrl().toString()
                self.open_url_in_new_tab(url)
        except:
            pass
            
    def open_url_in_new_tab(self, url):
        """Open URL in new tab"""
        if self.browser_window:
            self.browser_window.add_new_tab(url)
            
    def copy_link_to_clipboard(self, url):
        """Copy link to clipboard"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(url)
        except Exception as e:
            print(f"Error copying to clipboard: {e}")

# Extension Manager
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
        self.setWindowTitle("Download Manager")
        self.setGeometry(300, 300, 600, 400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.scroll_area = QScrollArea()
        self.download_widget = QWidget()
        self.download_layout = QVBoxLayout(self.download_widget)
        self.scroll_area.setWidget(self.download_widget)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(QLabel("Downloads:"))
        layout.addWidget(self.scroll_area)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
    def add_download(self, download_item):
        download_widget = DownloadItem(download_item)
        self.download_layout.addWidget(download_widget)

class BookmarkManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmark Manager")
        self.setGeometry(300, 300, 500, 400)
        self.parent_browser = parent
        self.init_ui()
        self.load_bookmarks()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.bookmark_list = QListWidget()
        self.bookmark_list.itemDoubleClicked.connect(self.open_bookmark)
        
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected_bookmark)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_bookmark)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(QLabel("Bookmarks:"))
        layout.addWidget(self.bookmark_list)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def load_bookmarks(self):
        if hasattr(self.parent_browser, 'bookmarks'):
            self.bookmark_list.clear()
            for title, url in self.parent_browser.bookmarks.items():
                self.bookmark_list.addItem(f"{title} - {url}")
                
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
            title = current_item.text().split(" - ")[0]
            if title in self.parent_browser.bookmarks:
                del self.parent_browser.bookmarks[title]
                self.parent_browser.save_bookmarks()
                self.load_bookmarks()

class HistoryManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.setGeometry(300, 300, 600, 500)
        self.parent_browser = parent
        self.init_ui()
        self.load_history()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.open_history_item)
        
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected_item)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(QLabel("History:"))
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
                self.history_list.addItem(f"[{timestamp}] {title} - {url}")
                
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
        self.setWindowTitle("Settings")
        self.setGeometry(300, 300, 400, 300)
        self.parent_browser = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # General Settings
        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        
        self.homepage_edit = QLineEdit(self.parent_browser.homepage)
        general_layout.addRow("Homepage:", self.homepage_edit)
        
        self.download_path_edit = QLineEdit(self.parent_browser.download_path)
        general_layout.addRow("Download Path:", self.download_path_edit)
        
        general_group.setLayout(general_layout)
        
        # Privacy Settings
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QFormLayout()
        
        self.private_browsing = QCheckBox("Enable Private Browsing by Default")
        self.javascript_enabled = QCheckBox("Enable JavaScript")
        self.javascript_enabled.setChecked(True)
        
        privacy_layout.addRow(self.private_browsing)
        privacy_layout.addRow(self.javascript_enabled)
        
        privacy_group.setLayout(privacy_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addWidget(general_group)
        layout.addWidget(privacy_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def save_settings(self):
        self.parent_browser.homepage = self.homepage_edit.text()
        self.parent_browser.download_path = self.download_path_edit.text()
        
        # Apply JavaScript setting to all tabs
        for i in range(self.parent_browser.tabs.count()):
            tab = self.parent_browser.tabs.widget(i)
            if hasattr(tab, 'webview'):
                settings = tab.webview.settings()
                settings.setAttribute(QWebEngineSettings.JavascriptEnabled, 
                                    self.javascript_enabled.isChecked())
        
        self.parent_browser.save_settings()
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.close()

class BrowserTab(QWidget):
    def __init__(self, url="https://www.google.com", private_mode=False, browser_window=None):
        super().__init__()
        self.is_loading = False
        self.private_mode = private_mode
        self.browser_window = browser_window
        
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
        
        # Circular loader container
        self.loader_container = QWidget()
        self.loader_container.setFixedHeight(80)
        loader_layout = QHBoxLayout(self.loader_container)
        loader_layout.setAlignment(Qt.AlignCenter)
        
        self.circular_loader = CircularLoader(color=QColor(70, 130, 180))
        loader_layout.addWidget(self.circular_loader)
        
        try:
            if not url or not isinstance(url, str):
                url = "https://www.google.com"
                
            if not url.startswith(('http://', 'https://')):
                if '.' in url:
                    url = 'https://' + url
                else:
                    url = "https://www.google.com"
            
            # Use custom WebEngine classes
            if private_mode:
                profile = QWebEngineProfile()
                self.webview = CustomWebEngineView()
                page = CustomWebEnginePage()
                page.setProfile(profile)
                self.webview.setPage(page)
            else:
                self.webview = CustomWebEngineView()
                page = CustomWebEnginePage()
                self.webview.setPage(page)
                
            # Set browser window reference for new tab/window functionality
            self.webview.browser_window = self.browser_window
            
            self.webview.setUrl(QUrl(url))
            
            # Connect signals
            self.webview.loadStarted.connect(self.load_started)
            self.webview.loadProgress.connect(self.load_progress)
            self.webview.loadFinished.connect(self.load_finished)
            
            main_layout.addWidget(self.loader_container)
            main_layout.addWidget(self.webview)
            
        except Exception as e:
            print(f"Error creating browser tab: {e}")
            self.webview = CustomWebEngineView()
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
        
    def load_progress(self, progress):
        pass  # Circular loader handles its own animation
        
    def load_finished(self, success):
        self.is_loading = False
        self.circular_loader.stop()
        self.loader_container.hide()

class WebKitBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.homepage = "https://www.google.com"
        self.download_path = os.path.expanduser("~/Downloads")
        self.bookmarks = {}
        self.history = []
        self.private_mode = False
        
        self.init_ui()
        self.apply_styles()
        self.load_settings()
        self.load_bookmarks()
        self.load_history()
        self.setup_shortcuts()
        
        # Extension manager
        self.extension_manager = ExtensionManager(self)
        
        # Download manager
        self.download_manager = DownloadManager(self)
        
    def init_ui(self):
        self.setWindowTitle("Enhanced WebKit Browser")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # FIXED: Use custom tab widget with properly working new tab button
        self.tabs = CustomTabWidget(self)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        
        # Create toolbar
        self.create_toolbar()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Start with one tab
        self.add_new_tab()
        
    def apply_styles(self):
        """Apply modern styling to the browser"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        
        QTabWidget::tab-bar {
            alignment: left;
        }
        
        QTabBar::tab {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #f0f0f0, stop: 1 #e0e0e0);
            border: 1px solid #c0c0c0;
            border-bottom-color: #c0c0c0;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 120px;
            padding: 8px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background: white;
            border-bottom-color: white;
        }
        
        QTabBar::tab:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #fafafa, stop: 1 #f0f0f0);
        }
        
        QToolBar {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #ffffff, stop: 1 #f0f0f0);
            border: none;
            spacing: 3px;
            padding: 4px;
        }
        
        QLineEdit {
            border: 2px solid #ddd;
            border-radius: 20px;
            padding: 8px 15px;
            font-size: 14px;
            background-color: white;
        }
        
        QLineEdit:focus {
            border-color: #4CAF50;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QStatusBar {
            background-color: #f0f0f0;
            border-top: 1px solid #ddd;
        }
        """
        self.setStyleSheet(style)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_tab_action = QAction('New Tab', self)
        new_tab_action.setShortcut('Ctrl+T')
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)
        
        new_private_tab_action = QAction('New Private Tab', self)
        new_private_tab_action.setShortcut('Ctrl+Shift+P')
        new_private_tab_action.triggered.connect(self.add_private_tab)
        file_menu.addAction(new_private_tab_action)
        
        file_menu.addSeparator()
        
        close_tab_action = QAction('Close Tab', self)
        close_tab_action.setShortcut('Ctrl+W')
        close_tab_action.triggered.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))
        file_menu.addAction(close_tab_action)
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Bookmarks menu
        bookmarks_menu = menubar.addMenu('Bookmarks')
        
        add_bookmark_action = QAction('Add Bookmark', self)
        add_bookmark_action.setShortcut('Ctrl+D')
        add_bookmark_action.triggered.connect(self.add_bookmark)
        bookmarks_menu.addAction(add_bookmark_action)
        
        manage_bookmarks_action = QAction('Manage Bookmarks', self)
        manage_bookmarks_action.triggered.connect(self.show_bookmark_manager)
        bookmarks_menu.addAction(manage_bookmarks_action)
        
        # History menu
        history_menu = menubar.addMenu('History')
        
        show_history_action = QAction('Show History', self)
        show_history_action.setShortcut('Ctrl+H')
        show_history_action.triggered.connect(self.show_history)
        history_menu.addAction(show_history_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        downloads_action = QAction('Downloads', self)
        downloads_action.setShortcut('Ctrl+J')
        downloads_action.triggered.connect(self.show_download_manager)
        tools_menu.addAction(downloads_action)
        
        developer_tools_action = QAction('Developer Tools', self)
        developer_tools_action.setShortcut('F12')
        developer_tools_action.triggered.connect(self.toggle_developer_tools)
        tools_menu.addAction(developer_tools_action)
        
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Extensions menu
        extensions_menu = menubar.addMenu('Extensions')
        
        install_extension_action = QAction('Install Extension', self)
        install_extension_action.triggered.connect(self.install_extension)
        extensions_menu.addAction(install_extension_action)
        
        manage_extensions_action = QAction('Manage Extensions', self)
        manage_extensions_action.triggered.connect(self.show_extension_manager)
        extensions_menu.addAction(manage_extensions_action)
        
    def create_toolbar(self):
        nav_bar = QToolBar()
        nav_bar.setMovable(False)
        self.addToolBar(nav_bar)
        
        # Navigation buttons with better icons
        back_btn = QAction("◀", self)
        back_btn.setToolTip("Go Back")
        back_btn.triggered.connect(self.go_back)
        nav_bar.addAction(back_btn)
        
        forward_btn = QAction("▶", self)
        forward_btn.setToolTip("Go Forward")
        forward_btn.triggered.connect(self.go_forward)
        nav_bar.addAction(forward_btn)
        
        reload_btn = QAction("⟳", self)
        reload_btn.setToolTip("Reload")
        reload_btn.triggered.connect(self.reload_page)
        nav_bar.addAction(reload_btn)
        
        home_btn = QAction("🏠", self)
        home_btn.setToolTip("Home")
        home_btn.triggered.connect(self.go_home)
        nav_bar.addAction(home_btn)
        
        # URL bar with improved styling
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)
        
        # Bookmark button
        bookmark_btn = QAction("⭐", self)
        bookmark_btn.setToolTip("Add Bookmark")
        bookmark_btn.triggered.connect(self.add_bookmark)
        nav_bar.addAction(bookmark_btn)
        
    def setup_shortcuts(self):
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.reload_page)
        
        address_bar_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        address_bar_shortcut.activated.connect(self.focus_address_bar)
        
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.show_find_dialog)
        
    def add_new_tab(self, url=None):
        try:
            if url is None or not isinstance(url, str):
                url = self.homepage
                
            if not url.strip():
                url = self.homepage
                
            # Pass browser window reference to tab
            browser_tab = BrowserTab(url, self.private_mode, self)
            
            title = "New Tab"
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
                    
                    if hasattr(browser_tab.webview.page(), 'profile'):
                        browser_tab.webview.page().profile().downloadRequested.connect(self.handle_download)
                        
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
        # Close browser when all tabs are closed
        if self.tabs.count() <= 1:
            self.close()  # Close the entire browser
        else:
            self.tabs.removeTab(index)
            
    def handle_download(self, download):
        try:
            path = os.path.join(self.download_path, download.suggestedFileName())
            download.setPath(path)
            download.accept()
            self.download_manager.add_download(download)
            self.status_label.setText(f"Downloading: {download.suggestedFileName()}")
        except Exception as e:
            print(f"Error handling download: {e}")
            self.status_label.setText("Download error occurred")
    
    def install_extension(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Install Extension", "", "JSON files (*.json)")
        if file_path:
            self.extension_manager.install_extension(file_path)
            
    def show_extension_manager(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Extension Manager")
        dialog.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        ext_list = QListWidget()
        for ext_id, ext_data in self.extension_manager.extensions.items():
            ext_list.addItem(f"{ext_data['name']} - {ext_data.get('version', '1.0')}")
            
        layout.addWidget(QLabel("Installed Extensions:"))
        layout.addWidget(ext_list)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
    def update_tab_title(self, qurl, browser_tab):
        try:
            i = self.tabs.indexOf(browser_tab)
            if i >= 0:
                domain = urlparse(qurl.toString()).netloc or "New Tab"
                if len(domain) > 20:
                    domain = domain[:17] + "..."
                self.tabs.setTabText(i, domain)
                
            if browser_tab == self.tabs.currentWidget():
                self.url_bar.setText(qurl.toString())
        except Exception as e:
            print(f"Error updating tab title: {e}")
            
    def update_tab_title_with_text(self, title, browser_tab):
        try:
            i = self.tabs.indexOf(browser_tab)
            if i >= 0 and title:
                if len(title) > 20:
                    title = title[:17] + "..."
                self.tabs.setTabText(i, title)
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
                    
                self.status_label.setText("Ready")
            elif not success:
                self.status_label.setText("Failed to load page")
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
            
        if " " in url and not url.startswith("http") and "." not in url.split()[0]:
            url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        elif not url.startswith("http"):
            if "." in url:
                url = "https://" + url
            else:
                url = f"https://www.google.com/search?q={url}"
                
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(url))
            self.status_label.setText("Loading...")
            
    def navigate_to_specific_url(self, url):
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(url))
            
    def update_url_bar(self, index):
        browser = self.current_browser()
        if browser:
            qurl = browser.url()
            self.url_bar.setText(qurl.toString())
            
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
            self.status_label.setText("Reloading...")
            
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
            text, ok = QInputDialog.getText(self, 'Find', 'Find text:')
            if ok and text:
                browser.findText(text)
                
    def add_bookmark(self):
        browser = self.current_browser()
        if browser:
            url = browser.url().toString()
            title = browser.title() or url
            
            bookmark_name, ok = QInputDialog.getText(self, 'Add Bookmark', 
                                                   'Bookmark name:', text=title)
            if ok and bookmark_name:
                self.bookmarks[bookmark_name] = url
                self.save_bookmarks()
                QMessageBox.information(self, "Bookmark", "Bookmark added successfully!")
                
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
                                  "Developer tools feature requires additional setup.")
                
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
            'window_geometry': [self.x(), self.y(), self.width(), self.height()]
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
                    
                    # Restore window geometry
                    geometry = settings.get('window_geometry')
                    if geometry:
                        self.setGeometry(geometry[0], geometry[1], geometry[2], geometry[3])
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def closeEvent(self, event):
        self.save_settings()
        self.save_bookmarks()
        self.save_history()
        event.accept()

if __name__ == "__main__":
    # Set scaling attributes before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, False)
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)
    
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Enhanced WebKit Browser")
    
    # Additional scaling fixes
    try:
        screen = QGuiApplication.primaryScreen()
        screen.setProperty("devicePixelRatio", 1.0)
    except:
        pass
    
    # Set application style
    app.setStyle('Fusion')
    
    window = WebKitBrowser()
    window.show()
    
    sys.exit(app.exec_())
