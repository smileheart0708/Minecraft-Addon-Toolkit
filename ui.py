from enum import Enum
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from qfluentwidgets import MSFluentWindow, NavigationItemPosition, SplashScreen
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import StyleSheetBase, Theme, qconfig, SystemThemeListener
from setting import SettingInterface
from translate_ui import LangInterface
from bag import BagInterface
from json_format import JsonFormatInterface
from resource.resource import LOGO_PATH, BASE_DIR
from functions import show_confirm_dialog
import shared
class StyleSheet(StyleSheetBase, Enum):
    FLUENT_WINDOW = "fluent_window"
    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f"{BASE_DIR}/{theme.value.lower()}/{self.value}.qss"
class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Addon翻译器')
        self.setWindowIcon(QIcon(LOGO_PATH))
        self.setMinimumSize(1000, 600)
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
        self.show()
        self.settingInterface = SettingInterface(self)
        self.langInterface = LangInterface(self)
        self.bagInterface = BagInterface(self)
        self.jsonFormatInterface = JsonFormatInterface(self)
        self.initNavigation()
        StyleSheet.FLUENT_WINDOW.apply(self)
        self.themeListener = SystemThemeListener()
        self.themeListener.start()
        self.splashScreen.finish()
    def initNavigation(self):
        self.addSubInterface(self.langInterface, FIF.LANGUAGE, '基岩版汉化', FIF.LANGUAGE)
        self.addSubInterface(self.bagInterface, FIF.FOLDER, '包管理', FIF.FOLDER)
        self.addSubInterface(self.jsonFormatInterface, FIF.CODE, 'JSON规范化', FIF.CODE)
        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置', FIF.SETTING, NavigationItemPosition.BOTTOM)
    def closeEvent(self, e):
        if shared.file_save == 'no':
            if not show_confirm_dialog('确认关闭', '当前有未保存的更改，确定要关闭吗？', self, confirm_text='确认关闭', cancel_text='取消'):
                e.ignore()
                return
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        super().closeEvent(e)