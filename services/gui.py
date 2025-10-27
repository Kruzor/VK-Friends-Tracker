import logging

from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QObject, pyqtSignal

from extensions.logging_ext import log
from extensions.path_ext import get_path


class QTextEditLogger(logging.Handler, QObject):
    append_text = pyqtSignal(str, str)  # текст + цвет

    def __init__(self, text_edit: QTextEdit, font_size: int = 10):
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.widget = text_edit
        self.font_size = font_size
        self.append_text.connect(self.append_html)

    def emit(self, record):
        msg = self.format(record)
        # цвет по уровню лога
        if record.levelno >= logging.ERROR:
            color = "red"
        elif record.levelno >= logging.WARNING:
            color = "orange"
        else:
            color = "white"
        self.append_text.emit(msg, color)

    def append_html(self, msg, color):
        html = f'<span style="color:{color}; font-size:{self.font_size}pt;">{msg}</span>'
        self.widget.append(html)


class LogWindow(QMainWindow):
    """Главное окно"""
    def __init__(self, browser_manager, icon_path=None):
        super().__init__()
        self.browser_manager = browser_manager
        self.setWindowTitle("VK Manager")
        self.setFixedSize(1100, 600)
        self.setWindowFlags(
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        # QTextEdit для логов
        self.log_console = QTextEdit(self)
        self.log_console.setReadOnly(True)
        self.setCentralWidget(self.log_console)

        # Иконка для трея
        self.tray_icon = QSystemTrayIcon(self)
        if icon_path is None:
            icon_path = get_path('static', 'tray.ico')
        self.tray_icon.setIcon(QIcon(icon_path))

        # Меню трея
        tray_menu = QMenu()
        open_action = QAction("Открыть     ", self)
        exit_action = QAction("Выйти     ", self)
        tray_menu.addAction(open_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)

        open_action.triggered.connect(self.show_window)
        exit_action.triggered.connect(self.exit_app)

        self.tray_icon.show()

        # Подключаем логгер GUI к существующему логгеру
        qt_handler = QTextEditLogger(self.log_console, font_size=11)
        formatter = logging.Formatter(
            "[%(levelname)s] [%(filename)s] [%(asctime)s]: %(message)s",
            datefmt="%d-%m-%Y %H:%M:%S"
        )
        qt_handler.setFormatter(formatter)
        log.addHandler(qt_handler)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "VK Manager",
            "Приложение свернуто в трей.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def show_window(self):
        self.showNormal()
        self.activateWindow()

    def exit_app(self):
        self.browser_manager.stop_browser()
        self.tray_icon.hide()
        QApplication.quit()

    def add_log(self, text: str):
        self.log_console.append(text)


def start_gui(browser_manager):
    """Функция ля запуска GUI из main"""
    
    app = QApplication([])
    window = LogWindow(browser_manager)
    window.show()
    return app, window