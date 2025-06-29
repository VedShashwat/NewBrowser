import sys
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QMenu, QMenuBar,
    QProgressBar, QLabel, QSplitter, QListWidget, QTextEdit, QPushButton,
    QDialog, QFormLayout, QSpinBox, QCheckBox, QComboBox, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QShortcut, QInputDialog
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, Qt, QThread, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QPixmap
from urllib.parse import urlparse

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
        
        self.private_browsing = QCheckBox("Enable Private Browsing")
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
    def __init__(self, url="https://www.google.com", private_mode=False):
        super().__init__()
        self.is_loading = False
        self.private_mode = private_mode
        
        # FIXED: Validate URL parameter type
        if not isinstance(url, str):
            print(f"Warning: Invalid URL type {type(url)}, using default")
            url = "https://www.google.com"
            
        self.init_ui(url, private_mode)
        
    def init_ui(self, url, private_mode):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        try:
            # FIXED: Additional URL validation before QUrl creation
            if not url or not isinstance(url, str):
                url = "https://www.google.com"
                
            # Ensure URL is properly formatted
            if not url.startswith(('http://', 'https://')):
                if '.' in url:
                    url = 'https://' + url
                else:
                    url = "https://www.google.com"
            
            # FIXED: Proper private profile creation
            if private_mode:
                # Create an off-the-record profile for private browsing
                profile = QWebEngineProfile()
                self.webview = QWebEngineView()
                # FIXED: Create web page without passing webview as parameter
                page = profile.createWebPage()
                self.webview.setPage(page)
            else:
                self.webview = QWebEngineView()
                
            # FIXED: Safe QUrl creation with validation
            self.webview.setUrl(QUrl(url))
            
            # Connect signals for loading progress
            self.webview.loadStarted.connect(self.load_started)
            self.webview.loadProgress.connect(self.load_progress)
            self.webview.loadFinished.connect(self.load_finished)
            
            layout.addWidget(self.webview)
            
        except Exception as e:
            print(f"Error creating browser tab: {e}")
            # Fallback to regular webview with default URL
            self.webview = QWebEngineView()
            self.webview.setUrl(QUrl("https://www.google.com"))
            layout.addWidget(self.webview)
            
        self.setLayout(layout)
        
    def load_started(self):
        self.is_loading = True
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
    def load_progress(self, progress):
        self.progress_bar.setValue(progress)
        
    def load_finished(self, success):
        self.is_loading = False
        self.progress_bar.hide()

class WebKitBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.homepage = "https://www.google.com"
        self.download_path = os.path.expanduser("~/Downloads")
        self.bookmarks = {}
        self.history = []
        self.private_mode = False
        
        self.init_ui()
        self.load_settings()
        self.load_bookmarks()
        self.load_history()
        self.setup_shortcuts()
        
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
        
        # Tab widget setup
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
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
        
    def create_toolbar(self):
        # Navigation toolbar
        nav_bar = QToolBar()
        nav_bar.setMovable(False)
        self.addToolBar(nav_bar)
        
        # Navigation buttons
        back_btn = QAction("←", self)
        back_btn.setToolTip("Go Back")
        back_btn.triggered.connect(self.go_back)
        nav_bar.addAction(back_btn)
        
        forward_btn = QAction("→", self)
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
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)
        
        # Bookmark button
        bookmark_btn = QAction("⭐", self)
        bookmark_btn.setToolTip("Add Bookmark")
        bookmark_btn.triggered.connect(self.add_bookmark)
        nav_bar.addAction(bookmark_btn)
        
        # New tab button
        new_tab_btn = QAction("+", self)
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.triggered.connect(self.add_new_tab)
        nav_bar.addAction(new_tab_btn)
        
    def setup_shortcuts(self):
        # Additional shortcuts
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.reload_page)
        
        address_bar_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        address_bar_shortcut.activated.connect(self.focus_address_bar)
        
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.show_find_dialog)
        
    # FIXED: Enhanced add_new_tab method with proper error handling
    def add_new_tab(self, url=None):
        try:
            # FIXED: Ensure URL is always a string
            if url is None or not isinstance(url, str):
                url = self.homepage
                
            # Additional URL validation
            if not url.strip():
                url = self.homepage
                
            print(f"Creating new tab with URL: {url}, Private mode: {self.private_mode}")
            
            # Create browser tab with validated parameters
            browser_tab = BrowserTab(url, self.private_mode)
            
            # Set tab title
            title = "New Tab"
            if self.private_mode:
                title = "🔒 Private Tab"
                
            # Add tab to widget
            i = self.tabs.addTab(browser_tab, title)
            self.tabs.setCurrentIndex(i)
            
            # FIXED: Improved signal connections with proper error handling
            if hasattr(browser_tab, 'webview') and browser_tab.webview:
                try:
                    # URL changed signal
                    browser_tab.webview.urlChanged.connect(
                        lambda qurl: self.update_tab_title(qurl, browser_tab)
                    )
                    
                    # Title changed signal
                    browser_tab.webview.titleChanged.connect(
                        lambda title: self.update_tab_title_with_text(title, browser_tab)
                    )
                    
                    # Load finished signal
                    browser_tab.webview.loadFinished.connect(
                        lambda ok: self.page_load_finished(ok, browser_tab)
                    )
                    
                    # Set up download handling
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
        
    def update_tab_title(self, qurl, browser_tab):
        try:
            i = self.tabs.indexOf(browser_tab)
            if i >= 0:
                domain = urlparse(qurl.toString()).netloc or "New Tab"
                if len(domain) > 20:
                    domain = domain[:17] + "..."
                self.tabs.setTabText(i, domain)
                
            # Update URL bar if this is the current tab
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
        
    def close_current_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            QMessageBox.warning(self, "Warning", "At least one tab must remain open.")
            
    def current_browser(self):
        current_widget = self.tabs.currentWidget()
        return current_widget.webview if current_widget and hasattr(current_widget, 'webview') else None
        
    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return
            
        # Simple search detection
        if " " in url and not url.startswith("http") and "." not in url.split()[0]:
            # Treat as search query
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
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Enhanced WebKit Browser")
    
    # Set application style
    app.setStyle('Fusion')
    
    window = WebKitBrowser()
    window.show()
    
    sys.exit(app.exec_())
