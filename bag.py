import os
from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QSizePolicy, QListWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from qfluentwidgets import ListWidget, PrimaryPushButton, LineEdit, IndeterminateProgressRing, SubtitleLabel
from functions import show_confirm_dialog, show_message_bar
from found import scan_packs, find_manifest_json, parse_manifest
from config import cfg
from save import PackManager
from import_file import ImportManager

# 添加导入线程类
class ImportThread(QThread):
    """用于后台导入包的线程"""
    finished = pyqtSignal(bool, str)  # 成功/失败, 消息
    
    def __init__(self, file_path, import_manager, find_manifest_json_func, parse_manifest_func):
        super().__init__()
        self.file_path = file_path
        self.import_manager = import_manager
        self.find_manifest_json_func = find_manifest_json_func
        self.parse_manifest_func = parse_manifest_func
        self.is_mcaddon = file_path.lower().endswith('.mcaddon')
    
    def run(self):
        try:
            if self.is_mcaddon:
                # 处理mcaddon文件
                success, message = self.import_manager.import_mcaddon(
                    self.file_path,
                    self.find_manifest_json_func,
                    self.parse_manifest_func
                )
            else:
                # 处理普通包文件
                success, message = self.import_manager.import_pack(
                    self.file_path, 
                    self.find_manifest_json_func, 
                    self.parse_manifest_func
                )
            
            # 发送结果信号
            self.finished.emit(success, message)
        except Exception as e:
            # 发送异常信号
            self.finished.emit(False, f"导入过程中发生错误：{str(e)}")

# 添加自定义合成线程类
class ComposeThread(QThread):
    """用于后台合成Addon的线程"""
    finished = pyqtSignal(bool, str, str)  # 成功/失败, 错误信息, 文件路径
    
    def __init__(self, behavior_pack, resource_pack, save_path, pack_manager):
        super().__init__()
        self.behavior_pack = behavior_pack
        self.resource_pack = resource_pack
        self.save_path = save_path
        self.pack_manager = pack_manager
    
    def run(self):
        try:
            import zipfile
            import shutil
            
            # 创建zip文件
            with zipfile.ZipFile(self.save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加行为包文件
                self._add_folder_to_zip(zipf, self.behavior_pack.path, os.path.basename(self.behavior_pack.path))
                
                # 添加资源包文件
                self._add_folder_to_zip(zipf, self.resource_pack.path, os.path.basename(self.resource_pack.path))
            
            # 发送成功信号
            self.finished.emit(True, "", self.save_path)
        except Exception as e:
            # 发送失败信号
            self.finished.emit(False, str(e), self.save_path)
            # 如果文件创建失败，尝试删除可能部分创建的文件
            if os.path.exists(self.save_path):
                try:
                    os.remove(self.save_path)
                except:
                    pass
    
    def _add_folder_to_zip(self, zipf, folder_path, folder_name):
        """添加文件夹到zip文件"""
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算相对路径，用于在zip中保持正确的文件结构
                rel_path = os.path.join(folder_name, os.path.relpath(file_path, folder_path))
                zipf.write(file_path, rel_path)

class BagInterface(QFrame):
    """ 包管理界面 """
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('BagInterface')

        self.vBoxLayout = QVBoxLayout(self)
        
        # 获取配置的应用文件夹路径
        app_folder = cfg.appFolder.value
        if not app_folder or not os.path.exists(app_folder):
            # 如果配置中没有设置或路径不存在，使用默认路径
            app_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
        
        # 创建包管理器和导入管理器
        self.pack_manager = PackManager(app_folder)
        self.import_manager = ImportManager(app_folder)
        
        # 创建按钮布局
        self.buttonLayout = QHBoxLayout()
        
        # 创建导入按钮和进度环的水平布局
        self.importLayout = QHBoxLayout()
        self.importLayout.setSpacing(5)  # 设置内部间距为5
        
        # 创建导入按钮
        self.importButton = PrimaryPushButton('导入', self)
        self.importButton.clicked.connect(self.import_pack)
        
        # 创建导入进度环
        self.importProgressRing = IndeterminateProgressRing(self)
        self.importProgressRing.setFixedSize(24, 24)  # 设置大小和按钮高度一致
        self.importProgressRing.hide()  # 默认隐藏
        
        # 将按钮和进度环添加到布局
        self.importLayout.addWidget(self.importButton)
        self.importLayout.addWidget(self.importProgressRing)
        
        # 创建删除按钮
        self.deleteButton = PrimaryPushButton('删除', self)
        self.deleteButton.clicked.connect(self.delete_pack)
        self.deleteButton.setEnabled(False)
        
        # 创建取消选择按钮
        self.unselectButton = PrimaryPushButton('取消选择', self)
        self.unselectButton.clicked.connect(self.unselect_items)
        self.unselectButton.setEnabled(False)
        
        # 创建刷新按钮
        self.refreshButton = PrimaryPushButton('刷新', self)
        self.refreshButton.clicked.connect(self.load_packs)
        
        # 创建合成按钮和进度环的水平布局
        self.composeLayout = QHBoxLayout()
        self.composeLayout.setSpacing(5)  # 设置内部间距为5
        
        # 创建合成按钮
        self.composeButton = PrimaryPushButton('合成', self)
        self.composeButton.clicked.connect(self.compose_addon)
        self.composeButton.setEnabled(False)  # 初始状态禁用
        
        # 创建合成进度环
        self.composeProgressRing = IndeterminateProgressRing(self)
        self.composeProgressRing.setFixedSize(24, 24)  # 设置大小和按钮高度一致
        self.composeProgressRing.hide()  # 默认隐藏
        
        # 将按钮和进度环添加到布局
        self.composeLayout.addWidget(self.composeButton)
        self.composeLayout.addWidget(self.composeProgressRing)
        
        # 创建包名称输入框
        self.nameLineEdit = LineEdit(self)
        self.nameLineEdit.setClearButtonEnabled(True)
        self.nameLineEdit.setFixedWidth(250)
        self.nameLineEdit.setText("包名")  # 默认显示"包名"
        self.nameLineEdit.textChanged.connect(self.on_name_text_changed)  # 监听文本变化
        
        # 创建重命名按钮
        self.renameButton = PrimaryPushButton('重命名', self)
        self.renameButton.setFixedWidth(70)  # 设置固定宽度，防止按钮被拉长
        self.renameButton.clicked.connect(self.rename_pack)
        self.renameButton.setEnabled(False)  # 默认禁用
        
        # 添加按钮和输入框到布局，设置统一的间距
        self.buttonLayout.setSpacing(10)  # 设置按钮之间的间距
        self.buttonLayout.addLayout(self.importLayout)
        self.buttonLayout.addWidget(self.deleteButton)
        self.buttonLayout.addWidget(self.unselectButton)
        self.buttonLayout.addWidget(self.refreshButton)
        self.buttonLayout.addLayout(self.composeLayout)
        self.buttonLayout.addSpacing(10)  # 添加一些间距
        self.buttonLayout.addWidget(self.nameLineEdit)
        self.buttonLayout.addWidget(self.renameButton)
        self.buttonLayout.addStretch(1)  # 添加弹性空间，使控件靠左
        
        # 将按钮布局添加到主布局
        self.vBoxLayout.addLayout(self.buttonLayout)
        
        # 创建包列表区域
        self.listAreaLayout = QVBoxLayout()
        
        # 创建左侧行为包列表
        self.behaviorListWidget = ListWidget(self)
        self.behaviorListWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.behaviorListWidget.itemClicked.connect(lambda item: self.on_list_item_clicked(self.behaviorListWidget, item))
        self.behaviorLabel = SubtitleLabel('行为包', self)
        
        # 创建资源包列表
        self.resourceListWidget = ListWidget(self)
        self.resourceListWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.resourceListWidget.itemClicked.connect(lambda item: self.on_list_item_clicked(self.resourceListWidget, item))
        self.resourceLabel = SubtitleLabel('资源包', self)
        
        # 将列表添加到列表区域布局
        self.listAreaLayout.addWidget(self.behaviorLabel)
        self.listAreaLayout.addWidget(self.behaviorListWidget)
        self.listAreaLayout.addWidget(self.resourceLabel)
        self.listAreaLayout.addWidget(self.resourceListWidget)
        
        # 将列表区域布局添加到主布局
        self.vBoxLayout.addLayout(self.listAreaLayout)
        
        # 设置布局属性
        self.vBoxLayout.setSpacing(16)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        
        # 初始状态下没有选中的包
        self.current_selected_pack = None
        self.selected_behavior_pack = None
        self.selected_resource_pack = None
        
        # 加载包信息
        self.load_packs()
        
        # 创建图片标签用于显示包图标
        self.imageLabel = QLabel(self)
        self.imageLabel.setFixedSize(64, 64)
        self.imageLabel.setVisible(False)
        
        # 压缩线程
        self.compress_thread = None
    
    def load_packs(self):
        """加载行为包和资源包信息"""
        # 清空列表
        self.behaviorListWidget.clear()
        self.resourceListWidget.clear()
        
        # 获取包信息
        behavior_packs, resource_packs = scan_packs()
        
        # 添加行为包到列表
        if behavior_packs:
            for pack in behavior_packs:
                item = QListWidgetItem(pack.name)
                # 查找并设置图标
                icon_path = os.path.join(pack.path, 'pack_icon.png')
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    item.setIcon(icon)
                self.behaviorListWidget.addItem(item)
        else:
            self.behaviorListWidget.addItem('空')
        
        # 添加资源包到列表
        if resource_packs:
            for pack in resource_packs:
                item = QListWidgetItem(pack.name)
                # 查找并设置图标
                icon_path = os.path.join(pack.path, 'pack_icon.png')
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    item.setIcon(icon)
                self.resourceListWidget.addItem(item)
        else:
            self.resourceListWidget.addItem('空')
        
        # 清除选择状态
        self.selected_behavior_pack = None
        self.selected_resource_pack = None
        self.current_selected_pack = None
        self.update_delete_button_state()
        self.update_compose_button_state()
    
    def list_mouse_press_event(self, list_widget, event):
        """处理列表的鼠标点击事件，现已弃用"""
        pass
    
    def on_list_item_clicked(self, list_widget, item):
        """处理列表项点击事件，更新输入框和重命名按钮状态"""
        if item.text() == '空':
            # 如果点击的是"空"项，当前列表不选择任何项
            if list_widget == self.behaviorListWidget:
                self.selected_behavior_pack = None
            else:
                self.selected_resource_pack = None
            
            # 更新合成按钮状态
            self.update_compose_button_state()
            return
        
        # 确定是哪个列表被点击
        if list_widget == self.behaviorListWidget:
            behavior_packs, _ = scan_packs()
            pack = next((p for p in behavior_packs if p.name == item.text()), None)
            if pack:
                self.selected_behavior_pack = pack
        else:  # resourceListWidget
            _, resource_packs = scan_packs()
            pack = next((p for p in resource_packs if p.name == item.text()), None)
            if pack:
                self.selected_resource_pack = pack
        
        # 更新包管理相关UI
        if pack and os.path.exists(pack.path):
            # 更新输入框显示选中包的名称
            self.nameLineEdit.setText(pack.name)
            # 初始状态下重命名按钮是禁用的
            self.renameButton.setEnabled(False)
            # 保存当前选中的包信息，用于重命名功能
            self.current_selected_pack = pack
        else:
            # 如果没有找到包，恢复默认状态
            self.nameLineEdit.setText("包名")
            self.renameButton.setEnabled(False)
            self.current_selected_pack = None
        
        # 更新删除按钮和取消选择按钮状态
        self.update_delete_button_state()
        
        # 更新合成按钮状态
        self.update_compose_button_state()
    
    def update_delete_button_state(self):
        """根据列表选择状态更新删除按钮状态"""
        # 检查是否有选中的包（且非"空"项）
        has_selection = (self.selected_behavior_pack is not None or 
                        self.selected_resource_pack is not None)
        
        # 如果有选中项，则启用删除按钮和取消选择按钮
        self.deleteButton.setEnabled(has_selection)
        self.unselectButton.setEnabled(has_selection)
    
    def update_compose_button_state(self):
        """根据选择状态更新合成按钮状态"""
        # 只有当同时选择了行为包和资源包时，才启用合成按钮
        self.composeButton.setEnabled(
            self.selected_behavior_pack is not None and 
            self.selected_resource_pack is not None
        )
    
    def unselect_items(self):
        """取消所有列表项的选中状态"""
        self.behaviorListWidget.clearSelection()
        self.resourceListWidget.clearSelection()
        
        # 清除选中的包
        self.selected_behavior_pack = None
        self.selected_resource_pack = None
        self.current_selected_pack = None
        
        # 更新按钮状态
        self.update_delete_button_state()
        self.update_compose_button_state()
        
        # 恢复默认状态
        self.nameLineEdit.setText("包名")
        self.renameButton.setEnabled(False)
        
        # 隐藏图片标签
        self.imageLabel.setVisible(False)
    
    def import_pack(self):
        """导入包文件（支持多文件）"""
        # 禁用导入按钮并显示进度环
        self.importButton.setEnabled(False)
        self.importProgressRing.show()
        
        try:
            file_names, _ = QFileDialog.getOpenFileNames(
                self,
                "选择要导入的包文件（可多选）",
                "",
                "Minecraft包文件 (*.zip *.mcpack *.mcaddon)"
            )
            
            if file_names:
                self._import_files_queue = list(file_names)
                self._import_next_file()
            else:
                # 用户取消了文件选择，恢复UI状态
                self.importButton.setEnabled(True)
                self.importProgressRing.hide()
        
        except Exception as e:
            # 发生异常时显示错误消息并恢复UI状态
            show_message_bar(
                title='错误',
                content=f'导入过程中发生错误：{str(e)}',
                bar_type='error',
                parent=self
            )
            self.importButton.setEnabled(True)
            self.importProgressRing.hide()
    
    def _import_next_file(self):
        """依次导入队列中的下一个文件"""
        if not hasattr(self, '_import_files_queue') or not self._import_files_queue:
            self.importButton.setEnabled(True)
            self.importProgressRing.hide()
            self.load_packs()
            return
        file_name = self._import_files_queue.pop(0)
        self.import_thread = ImportThread(
            file_name,
            self.import_manager,
            find_manifest_json,
            parse_manifest
        )
        self.import_thread.finished.connect(self._on_import_finished_multi)
        self.import_thread.start()

    def _on_import_finished_multi(self, success, message):
        show_message_bar(
            title='成功' if success else '错误',
            content=message,
            bar_type='success' if success else 'error',
            parent=self
        )
        # 继续导入下一个文件
        self._import_next_file()
    
    def on_name_text_changed(self):
        """监听输入框文本变化，当文本变化且有选中的包时启用重命名按钮"""
        if self.current_selected_pack:
            # 如果文本与当前包名不同，启用重命名按钮
            self.renameButton.setEnabled(self.nameLineEdit.text() != self.current_selected_pack.name)
    
    def rename_pack(self):
        """重命名包"""
        if not self.current_selected_pack:
            show_message_bar(
                title='错误',
                content='未选择包',
                bar_type='error',
                parent=self
            )
            return
        
        new_name = self.nameLineEdit.text().strip()
        if not new_name:
            show_message_bar(
                title='错误',
                content='包名不能为空',
                bar_type='error',
                parent=self
            )
            return
        
        # 使用PackManager重命名包
        success, message = self.pack_manager.rename_pack(self.current_selected_pack.path, new_name)
        
        # 显示结果消息
        show_message_bar(
            title='成功' if success else '错误',
            content=message,
            bar_type='success' if success else 'error',
            parent=self
        )
        
        # 如果重命名成功，刷新列表
        if success:
            # 更新当前选中的包名
            self.current_selected_pack.name = new_name
            self.load_packs()
            # 重命名成功后禁用重命名按钮
            self.renameButton.setEnabled(False)
    
    def delete_pack(self):
        """删除选中的包"""
        # 获取选中的包
        selected_pack = None
        pack_type = ""
        
        if self.selected_behavior_pack:
            selected_pack = self.selected_behavior_pack
            pack_type = "行为包"
        elif self.selected_resource_pack:
            selected_pack = self.selected_resource_pack
            pack_type = "资源包"
            
        if not selected_pack:
            return
        
        # 创建确认删除对话框
        title = '确认删除'
        content = f'确定要删除{pack_type} "{selected_pack.name}" 吗？'
        if show_confirm_dialog(title, content, self, confirm_text='确认', cancel_text='取消'):
            # 用户点击了"确认"按钮
            # 使用PackManager删除包
            success, message = self.pack_manager.delete_pack(selected_pack.path, selected_pack.name)
            
            # 显示结果消息
            show_message_bar(
                title='成功' if success else '错误',
                content=message,
                bar_type='success' if success else 'error',
                parent=self
            )
            
            # 如果删除成功，刷新列表
            if success:
                self.load_packs()
                # 隐藏图片标签
                self.imageLabel.setVisible(False)
    
    def compose_addon(self):
        """合成行为包和资源包为mcaddon文件"""
        # 检查是否同时选择了行为包和资源包
        if not self.selected_behavior_pack or not self.selected_resource_pack:
            show_message_bar(
                title='错误',
                content='请同时选择一个行为包和一个资源包',
                bar_type='error',
                parent=self
            )
            return
        
        # 自动生成保存路径：AppFolder/Addon/行为包名_资源包名.mcaddon
        app_folder = cfg.appFolder.value
        if not app_folder or not os.path.exists(app_folder):
            app_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
        addon_folder = os.path.join(app_folder, 'Addon')
        if not os.path.exists(addon_folder):
            os.makedirs(addon_folder, exist_ok=True)
        default_name = f"{self.selected_behavior_pack.name}_{self.selected_resource_pack.name}.mcaddon"
        save_path = os.path.join(addon_folder, default_name)
        
        # 检查是否已存在同名文件，若存在则自动覆盖
        # 禁用合成按钮并显示进度环
        self.composeButton.setEnabled(False)
        self.composeProgressRing.show()
        
        try:
            # 创建并启动合成线程
            self.compose_thread = ComposeThread(
                self.selected_behavior_pack, 
                self.selected_resource_pack, 
                save_path, 
                self.pack_manager
            )
            
            # 连接信号
            self.compose_thread.finished.connect(self.on_compose_finished)
            
            # 启动线程
            self.compose_thread.start()
            
        except Exception as e:
            # 启用合成按钮并隐藏进度环
            self.composeButton.setEnabled(True)
            self.composeProgressRing.hide()
            
            show_message_bar(
                title='错误',
                content=f'创建Addon时出错：{str(e)}',
                bar_type='error',
                parent=self
            )
    
    def on_compose_finished(self, success, error_msg, save_path):
        """合成完成回调"""
        # 启用合成按钮并隐藏进度环
        self.composeButton.setEnabled(True)
        self.composeProgressRing.hide()
        
        # 显示结果消息
        show_message_bar(
            title='成功' if success else '错误',
            content=f'已成功创建Addon：{os.path.basename(save_path)}' if success else f'创建Addon时出错：{error_msg}',
            bar_type='success' if success else 'error',
            parent=self
        )