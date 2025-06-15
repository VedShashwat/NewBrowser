import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class BrowserTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl("https://www.google.com"))
        self.layout.addWidget(self.webview)
        self.setLayout(self.layout)

class WebKitBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom WebKit Browser")
        self.setGeometry(100, 100, 1200, 800)

        # Tab widget setup
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.setCentralWidget(self.tabs)

        # Toolbar
        nav_bar = QToolBar()
        self.addToolBar(nav_bar)

        back_btn = QAction("Back", self)
        back_btn.triggered.connect(self.go_back)
        nav_bar.addAction(back_btn)

        forward_btn = QAction("Forward", self)
        forward_btn.triggered.connect(self.go_forward)
        nav_bar.addAction(forward_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.triggered.connect(self.reload_page)
        nav_bar.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.triggered.connect(self.go_home)
        nav_bar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        new_tab_btn = QAction("New Tab", self)
        new_tab_btn.triggered.connect(self.add_new_tab)
        nav_bar.addAction(new_tab_btn)

        # Start with one tab
        self.add_new_tab()

    def add_new_tab(self, url="https://www.google.com"):
        browser_tab = BrowserTab()
        i = self.tabs.addTab(browser_tab, "New Tab")
        self.tabs.setCurrentIndex(i)
        browser_tab.webview.urlChanged.connect(lambda qurl, browser_tab=browser_tab: self.update_tab_title(qurl, browser_tab))

    def update_tab_title(self, qurl, browser_tab):
        i = self.tabs.indexOf(browser_tab)
        self.tabs.setTabText(i, qurl.toString().split("//")[-1][:20])
        self.url_bar.setText(qurl.toString())

    def close_current_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            QMessageBox.warning(self, "Warning", "At least one tab must remain open.")

    def current_browser(self):
        return self.tabs.currentWidget().webview

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "http://" + url
        self.current_browser().setUrl(QUrl(url))

    def update_url_bar(self, index):
        qurl = self.current_browser().url()
        self.url_bar.setText(qurl.toString())

    def go_back(self):
        self.current_browser().back()

    def go_forward(self):
        self.current_browser().forward()

    def reload_page(self):
        self.current_browser().reload()

    def go_home(self):
        self.current_browser().setUrl(QUrl("https://www.google.com"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Tabbed WebKit Browser")
    window = WebKitBrowser()
    window.show()
    sys.exit(app.exec_())
