from PyQt6.QtWidgets import QFrame, QVBoxLayout, QFileDialog
from qfluentwidgets import setFont, OptionsSettingCard, FluentIcon, SettingCardGroup, RangeSettingCard, qconfig, PrimaryPushSettingCard
from config import cfg, check_app_folder
import os
from functions import show_message_bar

class SettingInterface(QFrame):
    """ 设置 """
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.setObjectName('SettingInterface')
        
        # 创建设置组
        self.settingGroup = SettingCardGroup('设置', self)
        setFont(self.settingGroup.titleLabel, 32)
        
        # 创建主题切换卡片
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FluentIcon.BRUSH,
            "应用主题",
            "调整你的应用外观",
            texts=["浅色", "深色", "跟随系统"],
            parent=self.settingGroup
        )

        # 创建复制数量设置卡片
        self.copyNumberCard = RangeSettingCard(
            cfg.copyNumber,
            FluentIcon.COPY,
            "复制数量",
            "设置复制的数量",
            parent=self.settingGroup
        )
        
        # 创建应用文件存储目录设置卡片（改为主题色按钮）
        self.storagePathCard = PrimaryPushSettingCard(
            "选择目录",
            FluentIcon.FOLDER,
            "应用文件存储目录",
            cfg.get(cfg.appFolder),
            self.settingGroup
        )
        
        # 创建关于设置卡片（改为主题色按钮）
        self.aboutCard = PrimaryPushSettingCard(
            "检查更新",
            FluentIcon.INFO,
            "关于软件",
            f"© 版权所有 2025, smileheart. 当前版本 1.0.1",
            self.settingGroup
        )
        
        # 添加卡片到设置组
        self.settingGroup.addSettingCard(self.themeCard)
        self.settingGroup.addSettingCard(self.copyNumberCard)
        self.settingGroup.addSettingCard(self.storagePathCard)
        self.settingGroup.addSettingCard(self.aboutCard)
        
        # 添加组件到布局
        self.vBoxLayout.addWidget(self.settingGroup)
        self.vBoxLayout.setSpacing(28)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 0)
        
        # 连接信号
        self._connectSignalToSlot()
        
        # 添加主题变化时的连接
        cfg.themeMode.valueChanged.connect(self._onThemeChanged)
        
    def _connectSignalToSlot(self):
        """ 连接信号到槽函数 """
        self.storagePathCard.clicked.connect(self._showFolderDialog)
        self.aboutCard.clicked.connect(self._checkUpdate)
        
    def _showFolderDialog(self):
        """ 显示文件夹选择对话框 """
        folder = QFileDialog.getExistingDirectory(
            self, 
            "选择应用文件存储目录", 
            cfg.get(cfg.appFolder)
        )
        
        if folder:
            # 使用os.access检查文件夹的写入权限，更高效且无需创建临时文件
            if not os.access(folder, os.W_OK):
                show_message_bar(title='错误', content="无法写入所选文件夹，请选择其他文件夹或检查权限。", 
                                bar_type='error', duration=5000, parent=self)
                return
            
            # 保存新的文件夹路径到配置
            cfg.set(cfg.appFolder, folder)
            self.storagePathCard.setContent(folder)
            
            # 检查并创建必要的子文件夹
            result_folder = check_app_folder(cfg)
            
            # 检查是否成功创建文件夹
            if not result_folder:
                show_message_bar(title='错误', content="无法创建应用文件夹，请检查系统权限。", 
                                bar_type='error', duration=5000, parent=self)
                return
            
            # 保存配置到文件（修复：使用正确的保存方法）
            qconfig.save()
            
            # 显示成功消息
            show_message_bar(title='成功', content="应用文件存储目录已更改，并已创建必要的子文件夹。", bar_type='success', duration=3000, parent=self)
            
    def _checkUpdate(self):
        """ 检查更新 """
        show_message_bar(title='检查更新', content="正在检查新版本...", bar_type='info', duration=3000, parent=self)
        # 这里可以添加实际的检查更新逻辑

    def _onThemeChanged(self, theme):
        """当主题变化时，仅更新配置并提示重启"""
        from config import cfg
        #cfg.set(cfg.themeMode, theme)
        show_message_bar(title='提示', content='主题切换将在重启软件后生效', bar_type='info', parent=self)