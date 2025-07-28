from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QFileDialog, QHeaderView, QAbstractItemView
from qfluentwidgets import SubtitleLabel, setFont, SearchLineEdit, PrimaryPushButton, PushButton, ComboBox, IndeterminateProgressRing
from functions.infobar import show_message_bar
import shared
from found import scan_packs, find_manifest_json
from search_function.search_main import SearchController
from table import CustomTableWidget, TableDataManager
from config import cfg

class LangInterface(QFrame):
    """ 汉化界面 """
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('LangInterface')

        self._init_ui()
        self._setup_connections()
        
    def _init_ui(self):
        self.vBoxLayout = QVBoxLayout(self)
        
        # 创建标题
        self.label = SubtitleLabel('基岩版Addon汉化', self)
        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建搜索框
        self.searchLayout = QHBoxLayout()
        self.searchLineEdit = SearchLineEdit(self)
        self.searchLineEdit.setPlaceholderText('查找文件名或值')
        self.searchLineEdit.setClearButtonEnabled(True)
        self.searchLayout.addWidget(self.searchLineEdit)
        
        # 创建按钮布局
        self.hBoxLayout = QHBoxLayout()
        
        # 创建包选择下拉框
        self.packComboBox = ComboBox(self)
        self.packComboBox.setPlaceholderText('还没有添加任何包')
        
        # 创建刷新按钮
        self.refreshPacksButton = PushButton('刷新', self)
        
        # 创建文件夹选择按钮
        self.folderButton = PrimaryPushButton('选择文件夹', self)
        
        # 创建查找按钮
        self.searchButton = PrimaryPushButton('查找', self)
        
        # 创建进度指示器
        self.searchSpinner = IndeterminateProgressRing(self)
        self.searchSpinner.setFixedSize(24, 24)
        self.searchSpinner.hide()
        
        # 创建中文显示切换按钮
        self.toggleChineseButton = PrimaryPushButton('隐藏中文值', self)
        
        # 创建保存按钮
        self.saveButton = PrimaryPushButton('保存', self)
        
        # 创建复制按钮
        self.copyButton = PrimaryPushButton('复制', self)
        
        # 创建粘贴按钮
        self.pasteButton = PrimaryPushButton('粘贴', self)
        
        # 添加按钮到布局
        self.hBoxLayout.addWidget(self.packComboBox)
        self.hBoxLayout.addWidget(self.refreshPacksButton)
        self.hBoxLayout.addStretch()
        self.hBoxLayout.addWidget(self.folderButton)
        self.hBoxLayout.addWidget(self.searchButton)
        self.hBoxLayout.addWidget(self.searchSpinner)
        self.hBoxLayout.addWidget(self.toggleChineseButton)
        self.hBoxLayout.addWidget(self.saveButton)
        self.hBoxLayout.addWidget(self.copyButton)
        self.hBoxLayout.addWidget(self.pasteButton)
        
        # 创建表格
        self.tableView = CustomTableWidget(self)
        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)
        self.tableView.setWordWrap(False)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.tableView.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        # 设置表格列数
        self.tableView.setColumnCount(3)
        self.tableView.setHorizontalHeaderLabels(['', '', ''])
        for i in range(3):
            self.tableView.setColumnHidden(i, True)
        vertical_header = self.tableView.verticalHeader()
        if vertical_header:
            vertical_header.hide()
        
        # 添加组件到主布局
        self.vBoxLayout.addWidget(self.label)
        self.vBoxLayout.addLayout(self.searchLayout)
        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.vBoxLayout.addWidget(self.tableView)
        self.vBoxLayout.setSpacing(16)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        
        # 初始化包列表
        self.updatePackList()
        
    def _setup_connections(self):
        # 创建表格数据管理器
        self.table_manager = TableDataManager(self.tableView)
        self.table_manager.data_changed.connect(self._on_data_changed)

        # 初始化搜索控制器
        self.search_controller = SearchController(self)
        self.search_controller.results_ready.connect(self._handle_search_results)
        self.search_controller.search_error.connect(self._handle_search_error)
        self.search_controller.search_finished.connect(self._on_search_finished)
        
        # 连接按钮信号
        self.searchLineEdit.returnPressed.connect(self.searchContent)
        self.folderButton.clicked.connect(self.selectFolder)
        self.searchButton.clicked.connect(self.searchContent)
        self.refreshPacksButton.clicked.connect(self.updatePackList)
        self.toggleChineseButton.clicked.connect(self.toggle_chinese_visibility)
        self.saveButton.clicked.connect(self.saveChanges)
        self.copyButton.clicked.connect(self.copyRows)
        self.pasteButton.clicked.connect(self.paste_from_clipboard)
        self.packComboBox.currentIndexChanged.connect(self.on_pack_selected)

    def _on_data_changed(self):
        shared.file_save = 'no'

    def paste_from_clipboard(self):
        selected_pack_info = self._get_selected_pack_info()
        if not selected_pack_info:
            show_message_bar(title='错误', content="未选择任何包，无法粘贴。", bar_type='error', duration=3000, parent=self)
            return
            
        self.table_manager.set_current_pack(selected_pack_info)
        success, message = self.table_manager.paste_from_clipboard()
        
        if success:
            show_message_bar(title='粘贴成功', content=message, bar_type='success', duration=5000, parent=self)
        else:
            show_message_bar(title='提示', content=message, bar_type='info' if "未找到匹配的键" in message else 'warning', duration=5000, parent=self)

    def _get_selected_pack_info(self):
        current_text = self.packComboBox.currentText()
        if not current_text:
            return None

        behavior_packs, resource_packs = scan_packs()
        
        selected_pack = None
        if current_text.startswith('[行为包]'):
            for pack in behavior_packs:
                if current_text == f'[行为包] {pack.name}':
                    selected_pack = pack
                    break
        elif current_text.startswith('[资源包]'):
            for pack in resource_packs:
                if current_text == f'[资源包] {pack.name}':
                    selected_pack = pack
                    break
        return selected_pack

    def saveChanges(self):
        selected_pack_info = self._get_selected_pack_info()
        if not selected_pack_info:
            show_message_bar(title='错误', content="未选择任何包，无法保存。", bar_type='error', duration=3000, parent=self)
            return
        
        self.table_manager.set_current_pack(selected_pack_info)
        success, message = self.table_manager.save_changes()

        if success:
            if "但有错误" in message:
                show_message_bar(title='警告', content=message, bar_type='warning', duration=7000, parent=self)
            else:
                show_message_bar(title='成功', content=message, bar_type='success', duration=5000, parent=self)
            shared.file_save = 'yes'
            self.searchContent()
        else:
            show_message_bar(title='保存失败', content=message, bar_type='error', duration=5000, parent=self)
            shared.file_save = 'no'

    def searchContent(self):
        self.searchSpinner.show()
        selected_pack = self._get_selected_pack_info()
        if not selected_pack:
            self.table_manager.clear_table()
            self.searchSpinner.hide()
            return

        self.table_manager.set_current_pack(selected_pack)
        search_text = self.searchLineEdit.text().lower()

        if self.search_controller.is_running():
            show_message_bar(title='提示', content='上一个搜索仍在进行中，请稍后再试或等待其完成。', bar_type='info', duration=3000, parent=self)
            return

        self.search_controller.start_search(selected_pack, search_text)

    def _handle_search_results(self, results, pack_type, failed_json_count):
        current_results = self.search_controller.get_current_results()
        self.table_manager.populate_table(current_results, pack_type)
        self.setupTableColumns()
        self.update_row_visibility()

        shared.file_save = None

        visible_rows, total_rows = self.table_manager.get_visible_rows_count()
        message_content = f"共找到 {total_rows} 条结果，当前显示 {visible_rows} 条。"
        if failed_json_count > 0:
            message_content += f" {failed_json_count} 个JSON文件解析失败。"
            selected_pack = self._get_selected_pack_info()
            if selected_pack and selected_pack.type == 'behavior':
                shared.error_json_pack_path = selected_pack.path

        show_message_bar(
            title='查找完成',
            content=message_content,
            bar_type='success' if failed_json_count == 0 else 'warning',
            duration=5000,
            parent=self
        )

    def _handle_search_error(self, error_message):
        show_message_bar(title='查找错误', content=error_message, bar_type='error', duration=5000, parent=self)
        self.searchSpinner.hide()

    def _on_search_finished(self):
        self.searchSpinner.hide()

    def updatePackList(self):
        current_text = self.packComboBox.currentText()
        self.packComboBox.clear()
        
        behavior_packs, resource_packs = scan_packs()
        
        for pack in behavior_packs:
            self.packComboBox.addItem(f"[行为包] {pack.name}")
            
        for pack in resource_packs:
            self.packComboBox.addItem(f"[资源包] {pack.name}")
            
        if not (behavior_packs or resource_packs):
            self.packComboBox.setCurrentIndex(-1)
        else:
            index = self.packComboBox.findText(current_text)
            if index >= 0:
                self.packComboBox.setCurrentIndex(index)

    def toggle_chinese_visibility(self):
        current_text = self.toggleChineseButton.text()

        if current_text == '隐藏中文值':
            new_button = PushButton('显示中文值', self)
            hide_chinese = True
        else:
            new_button = PrimaryPushButton('隐藏中文值', self)
            hide_chinese = False

        new_button.clicked.connect(self.toggle_chinese_visibility)

        self.hBoxLayout.replaceWidget(self.toggleChineseButton, new_button)
        self.toggleChineseButton.deleteLater()

        self.toggleChineseButton = new_button
        self.table_manager.update_row_visibility(hide_chinese)
        self.setupTableColumns()

    def update_row_visibility(self):
        button_text = self.toggleChineseButton.text()
        hide_chinese = button_text == '显示中文值'
        self.table_manager.update_row_visibility(hide_chinese)

    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder:
            manifest_path = find_manifest_json(folder)
            
            if manifest_path:
                shared.user_folder = folder
                self.updatePackList()
            else:
                show_message_bar(title='错误', content="在所选文件夹及其子文件夹中未找到manifest.json文件，请选择有效的Addon文件夹。", bar_type='error', duration=5000, parent=self)

    def copyRows(self):
        copy_number = cfg.copyNumber.value
        
        selected_pack = self._get_selected_pack_info()
        if not selected_pack:
            show_message_bar(title='错误', content="未选择任何包，无法复制。", bar_type='error', duration=3000, parent=self)
            return

        self.table_manager.set_current_pack(selected_pack)
        success, copied_count = self.table_manager.copy_rows(copy_number)

        if success:
            show_message_bar(title='成功', content=f"已复制 {copied_count} 行内容到剪贴板", bar_type='success', duration=3000, parent=self)
        else:
            show_message_bar(title='警告', content="没有可复制的内容", bar_type='warning', duration=3000, parent=self)

    def setupTableColumns(self):
        if self.tableView.rowCount() == 0:
            return
        header = self.tableView.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def on_pack_selected(self, index):
        """当用户从下拉框选择包时调用"""
        if index >= 0:
            selected_pack = self._get_selected_pack_info()
            if selected_pack:
                pack_type = "行为包" if selected_pack.type == "behavior" else "资源包"
                show_message_bar(
                    title='已选择包', 
                    content=f'已选择{pack_type}：{selected_pack.name}', 
                    bar_type='success', 
                    duration=3000, 
                    parent=self
                )
