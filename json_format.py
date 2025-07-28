from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import SubtitleLabel, setFont, ComboBox, PushButton, ProgressBar, PrimaryPushButton, IndeterminateProgressBar
from PyQt6.QtCore import QThread, pyqtSignal
import os
import orjson
from functions import format_json_file, show_message_bar
from config import cfg
from found import scan_packs
import shared  # 正确导入shared模块

class JsonFormatInterface(QFrame):
    """ JSON 文件规范化界面 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('JsonFormatInterface')
        
        self.vBoxLayout = QVBoxLayout(self)
        
        self.behavior_packs = []  # 存储行为包信息
        self.selected_pack_path = None # 存储选中的包路径

        # 创建标题
        self.titleLabel = SubtitleLabel('JSON 文件规范化', self)
        setFont(self.titleLabel, 24)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 创建下拉框、按钮和进度条的水平布局
        self.controlLayout = QHBoxLayout()
        self.packComboBox = ComboBox(self)
        self.packComboBox.setPlaceholderText('没有行为包')
        self.refreshButton = PushButton('刷新', self)
        self.refreshButton.clicked.connect(self.load_behavior_packs)
        self.packComboBox.currentIndexChanged.connect(self.on_pack_selected)
        
        # 创建开始按钮
        self.startButton = PrimaryPushButton('开始', self)
        self.startButton.setEnabled(False) # 初始禁用
        self.startButton.clicked.connect(self.start_json_formatting)
        
        # 创建全部规范化按钮
        self.formatAllButton = PrimaryPushButton('全部规范化', self)
        self.formatAllButton.setEnabled(False) # 初始禁用
        self.formatAllButton.clicked.connect(self.start_format_all_json)

        # 创建不确定进度条
        self.indeterminateProgressBar = IndeterminateProgressBar(self)
        self.indeterminateProgressBar.setFixedWidth(200)
        self.indeterminateProgressBar.hide()  # 默认隐藏

        # 创建确定进度条
        self.progressBar = ProgressBar(self)
        self.progressBar.setValue(0)  # 默认为空
        self.progressBar.setFixedWidth(200)
        self.progressBar.hide()  # 默认隐藏
        
        # 添加控件到水平布局
        self.controlLayout.addWidget(self.packComboBox)
        self.controlLayout.addWidget(self.refreshButton)
        self.controlLayout.addWidget(self.startButton)
        self.controlLayout.addWidget(self.formatAllButton)
        self.controlLayout.addWidget(self.indeterminateProgressBar)
        self.controlLayout.addWidget(self.progressBar)
        self.controlLayout.addStretch()

        # 添加处理文件标签
        self.processingLabel = QLabel(self)
        self.processingLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processingLabel.setVisible(False)  # 默认隐藏

        # 添加组件到主布局
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.controlLayout)
        self.vBoxLayout.addWidget(self.processingLabel, 0, Qt.AlignmentFlag.AlignCenter)  # 添加标签到布局
        self.vBoxLayout.addStretch()

        self.vBoxLayout.setContentsMargins(36, 10, 36, 36)
        self.vBoxLayout.setSpacing(20)

        self.load_behavior_packs() # 初始化时加载行为包

    def load_behavior_packs(self):
        self.packComboBox.clear()
        self.behavior_packs = []
        app_folder = cfg.appFolder.value
        if not app_folder or not os.path.exists(app_folder):
            show_message_bar(title='错误', content='未配置AppFolder路径或路径不存在', bar_type='error', duration=5000, parent=self)
            self.packComboBox.setPlaceholderText('没有行为包')
            self.startButton.setEnabled(False)
            self.formatAllButton.setEnabled(False)
            return

        # 使用scan_packs函数获取行为包和资源包
        behavior_packs, _ = scan_packs()
        self.behavior_packs = behavior_packs

        if self.behavior_packs:
            default_index = -1  # 默认不选中
            error_json_pack_index = -1  # 存储包含错误JSON文件的包的索引
            
            # 添加包到下拉框
            for i, pack in enumerate(self.behavior_packs):
                self.packComboBox.addItem(pack.name, userData=pack.path)
                # 检查是否是包含错误JSON文件的包
                if shared.error_json_pack_path and shared.error_json_pack_path == pack.path:
                    error_json_pack_index = i
            
            # 优先选择包含错误JSON文件的包，如果没有则选择第一个包
            if error_json_pack_index >= 0:
                self.packComboBox.setCurrentIndex(error_json_pack_index)
                self.startButton.setEnabled(True)
                self.formatAllButton.setEnabled(True)
            elif len(self.behavior_packs) > 0:
                self.packComboBox.setCurrentIndex(0)  # 选择第一个包
                self.startButton.setEnabled(True)
                self.formatAllButton.setEnabled(True)
            else:
                self.packComboBox.setCurrentIndex(-1)  # 不选中任何包
                self.packComboBox.setPlaceholderText('选择一个行为包')
                self.startButton.setEnabled(False)
                self.formatAllButton.setEnabled(False)
        else:
            self.packComboBox.setPlaceholderText('没有行为包')
            self.startButton.setEnabled(False)
            self.formatAllButton.setEnabled(False)

    def on_pack_selected(self, index):
        if index >= 0:
            self.selected_pack_path = self.packComboBox.itemData(index)
            self.startButton.setEnabled(True)
            self.formatAllButton.setEnabled(True)
            self.progressBar.setValue(0) # 重置进度条
        else:
            self.selected_pack_path = None
            self.startButton.setEnabled(False)
            self.formatAllButton.setEnabled(False)

    def start_json_formatting(self):
        if not self.selected_pack_path:
            show_message_bar(title='提示', content='请先选择一个行为包', bar_type='warning', duration=5000, parent=self)
            return

        # 禁用UI元素
        self.startButton.setEnabled(False)
        self.formatAllButton.setEnabled(False)
        self.refreshButton.setEnabled(False)
        self.packComboBox.setEnabled(False)
        
        # 显示不确定进度条
        self.indeterminateProgressBar.show()
        self.processingLabel.setText("正在扫描JSON文件...")
        self.processingLabel.setVisible(True)

        # 找到对应的 PackInfo 对象
        selected_pack_name = self.packComboBox.currentText()
        current_pack_info = next((pack for pack in self.behavior_packs if pack.name == selected_pack_name and pack.path == self.selected_pack_path), None)

        if not current_pack_info:
            show_message_bar(title='错误', content='无法找到选定包的信息。', bar_type='error', duration=5000, parent=self)
            self.reset_ui_state()
            return

        # 创建并启动扫描线程
        self.scanning_thread = JsonScanningThread(current_pack_info.path)
        self.scanning_thread.scanning_completed.connect(self.on_scanning_completed)
        self.scanning_thread.start()
        
    def start_format_all_json(self):
        """启动全部JSON文件规范化流程"""
        if not self.selected_pack_path:
            show_message_bar(title='提示', content='请先选择一个行为包', bar_type='warning', duration=5000, parent=self)
            return
            
        # 禁用UI元素
        self.startButton.setEnabled(False)
        self.formatAllButton.setEnabled(False)
        self.refreshButton.setEnabled(False)
        self.packComboBox.setEnabled(False)
        
        # 显示不确定进度条
        self.indeterminateProgressBar.show()
        self.processingLabel.setText("正在扫描所有JSON文件，准备进行规范化...")
        self.processingLabel.setVisible(True)
        
        # 找到对应的 PackInfo 对象
        selected_pack_name = self.packComboBox.currentText()
        current_pack_info = next((pack for pack in self.behavior_packs if pack.name == selected_pack_name and pack.path == self.selected_pack_path), None)

        if not current_pack_info:
            show_message_bar(title='错误', content='无法找到选定包的信息。', bar_type='error', duration=5000, parent=self)
            self.reset_ui_state()
            return
            
        # 创建并启动全部JSON扫描线程
        self.all_json_scanning_thread = AllJsonScanningThread(current_pack_info.path)
        self.all_json_scanning_thread.json_files_found.connect(self.on_all_json_files_found)
        self.all_json_scanning_thread.start()

    def on_scanning_completed(self, failed_json_files):
        # 隐藏不确定进度条
        self.indeterminateProgressBar.hide()
        
        if not failed_json_files:
            show_message_bar(title='成功', content='所有行为包内的JSON文件均可被解析！', bar_type='success', duration=5000, parent=self)
            self.reset_ui_state()
            return
        
        # 显示确定进度条
        self.progressBar.show()
        self.progressBar.setValue(0)
        
        # 创建并启动格式化线程
        self.formatting_thread = JsonFormattingThread(self.selected_pack_path, failed_json_files)
        self.formatting_thread.progress_updated.connect(self.update_progress)
        self.formatting_thread.file_processing.connect(self.update_processing_file)
        self.formatting_thread.formatting_completed.connect(self.on_formatting_completed)
        self.formatting_thread.start()
        
    def on_all_json_files_found(self, json_files):
        """处理找到的所有JSON文件"""
        # 隐藏不确定进度条
        self.indeterminateProgressBar.hide()
        
        if not json_files:
            show_message_bar(title='提示', content='未找到任何JSON文件', bar_type='info', duration=5000, parent=self)
            self.reset_ui_state()
            return
            
        # 显示确定进度条
        self.progressBar.show()
        self.progressBar.setValue(0)
        
        # 更新处理标签，说明优化的解析策略
        self.processingLabel.setText(f"正在规范化 {len(json_files)} 个JSON文件 (优先使用高效orjson解析)")
        
        # 创建并启动格式化所有JSON线程
        self.format_all_thread = FormatAllJsonThread(json_files)
        self.format_all_thread.progress_updated.connect(self.update_progress)
        self.format_all_thread.file_processing.connect(self.update_processing_file)
        self.format_all_thread.formatting_completed.connect(self.on_all_formatting_completed)
        self.format_all_thread.start()

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def update_processing_file(self, file_name):
        """更新正在处理的文件标签"""
        self.processingLabel.setText(f"正在处理: {file_name}")
        self.processingLabel.setVisible(True)

    def on_formatting_completed(self, failed_files):
        """格式化完成的处理"""
        self.progressBar.setValue(100)
        self.reset_ui_state()
        
        # 清除全局变量中的错误包路径
        shared.error_json_pack_path = None
        
        if failed_files:
            failed_files_str = "\n".join([f"{os.path.basename(path)}: {error}" for path, error in failed_files])
            show_message_bar(
                title='JSON格式化完成', 
                content=f'有 {len(failed_files)} 个文件无法使用json5解析，已跳过。\n{failed_files_str}', 
                bar_type='warning', 
                duration=10000, 
                parent=self
            )
        else:
            show_message_bar(
                title='成功', 
                content='所有不规范的JSON文件已成功格式化！', 
                bar_type='success', 
                duration=5000, 
                parent=self
            )
            
    def on_all_formatting_completed(self, failed_files):
        """全部格式化完成的处理"""
        self.progressBar.setValue(100)
        self.reset_ui_state()
        
        # 清除全局变量中的错误包路径
        shared.error_json_pack_path = None
        
        if failed_files:
            failed_files_str = "\n".join([f"{os.path.basename(path)}: {error}" for path, error in failed_files[:10]])
            if len(failed_files) > 10:
                failed_files_str += f"\n... 以及其他 {len(failed_files) - 10} 个文件"
                
            show_message_bar(
                title='全部JSON格式化完成', 
                content=f'有 {len(failed_files)} 个文件无法使用json5解析，已跳过。\n{failed_files_str}', 
                bar_type='warning', 
                duration=10000, 
                parent=self
            )
        else:
            show_message_bar(
                title='成功', 
                content='所有JSON文件已成功规范化！', 
                bar_type='success', 
                duration=5000, 
                parent=self
            )

    def reset_ui_state(self):
        """重置UI状态"""
        self.processingLabel.setVisible(False)
        self.startButton.setEnabled(True)
        self.formatAllButton.setEnabled(True)
        self.refreshButton.setEnabled(True)
        self.packComboBox.setEnabled(True)
        self.indeterminateProgressBar.hide()
        self.progressBar.hide()
        self.progressBar.setValue(0)


class JsonScanningThread(QThread):
    scanning_completed = pyqtSignal(list)  # 扫描完成信号，传递解析失败的文件列表
    
    def __init__(self, pack_path):
        super().__init__()
        self.pack_path = pack_path
        
    def run(self):
        try:
            failed_json_files = []
            
            # 检查items文件夹
            items_dir = os.path.join(self.pack_path, 'items')
            if os.path.isdir(items_dir):
                for root, _, files in os.walk(items_dir):
                    for file in files:
                        if file.endswith('.json'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                orjson.loads(content)
                            except Exception:
                                failed_json_files.append(file_path)
            
            # 检查entities文件夹
            entities_dir = os.path.join(self.pack_path, 'entities')
            if os.path.isdir(entities_dir):
                for root, _, files in os.walk(entities_dir):
                    for file in files:
                        if file.endswith('.json'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                orjson.loads(content)
                            except Exception:
                                failed_json_files.append(file_path)
            
            # 发送扫描结果
            self.scanning_completed.emit(failed_json_files)
        except Exception as e:
            import traceback
            print(f"Error in JsonScanningThread: {e}\n{traceback.format_exc()}")
            self.scanning_completed.emit([])
            
class AllJsonScanningThread(QThread):
    json_files_found = pyqtSignal(list)  # 找到所有JSON文件的信号
    
    def __init__(self, pack_path):
        super().__init__()
        self.pack_path = pack_path
        
    def run(self):
        try:
            all_json_files = []
            
            # 遍历整个包文件夹查找所有JSON文件
            for root, _, files in os.walk(self.pack_path):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        all_json_files.append(file_path)
            
            # 发送找到的所有JSON文件
            self.json_files_found.emit(all_json_files)
        except Exception as e:
            import traceback
            print(f"Error in AllJsonScanningThread: {e}\n{traceback.format_exc()}")
            self.json_files_found.emit([])


class JsonFormattingThread(QThread):
    progress_updated = pyqtSignal(int)  # 进度更新信号
    file_processing = pyqtSignal(str)   # 正在处理的文件信号
    formatting_completed = pyqtSignal(list)  # 格式化完成信号，传递失败文件列表
    
    def __init__(self, pack_path, failed_json_files):
        super().__init__()
        self.pack_path = pack_path
        self.failed_json_files = failed_json_files
        self.is_running = True
        
    def run(self):
        try:
            if not self.failed_json_files:
                self.formatting_completed.emit([])
                return
                
            total_files = len(self.failed_json_files)
            processed_files = 0
            failed_files = []
            
            for file_path in self.failed_json_files:
                if not self.is_running:
                    break
                    
                # 发送正在处理的文件名
                file_name = os.path.basename(file_path)
                self.file_processing.emit(file_name)
                
                # 使用format_json_file函数处理文件
                success, message = format_json_file(file_path)
                if not success:
                    failed_files.append((file_path, message))
                
                # 更新进度
                processed_files += 1
                progress = int((processed_files / total_files) * 100)  # 0%到100%的范围
                self.progress_updated.emit(progress)
            
            # 完成
            self.formatting_completed.emit(failed_files)
        except Exception as e:
            import traceback
            print(f"Error in JsonFormattingThread: {e}\n{traceback.format_exc()}")
            self.formatting_completed.emit([("Unknown error", str(e))])
    
    def stop(self):
        self.is_running = False
        
class FormatAllJsonThread(QThread):
    progress_updated = pyqtSignal(int)  # 进度更新信号
    file_processing = pyqtSignal(str)   # 正在处理的文件信号
    formatting_completed = pyqtSignal(list)  # 格式化完成信号，传递失败文件列表
    
    def __init__(self, json_files):
        super().__init__()
        self.json_files = json_files
        self.is_running = True
        
    def run(self):
        try:
            if not self.json_files:
                self.formatting_completed.emit([])
                return
                
            total_files = len(self.json_files)
            processed_files = 0
            failed_files = []
            
            for file_path in self.json_files:
                if not self.is_running:
                    break
                    
                # 发送正在处理的文件名
                file_name = os.path.basename(file_path)
                self.file_processing.emit(file_name)
                
                # 先尝试使用orjson解析（效率高）
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    orjson.loads(content)
                    # orjson解析成功，使用format_json_file规范化
                    success, message = format_json_file(file_path)
                    if not success:
                        failed_files.append((file_path, message))
                except Exception:
                    # orjson解析失败，尝试使用json5库解析（性能较低但更宽松）
                    success, message = format_json_file(file_path)
                    if not success:
                        failed_files.append((file_path, message))
                
                # 更新进度
                processed_files += 1
                progress = int((processed_files / total_files) * 100)  # 0%到100%的范围
                self.progress_updated.emit(progress)
            
            # 完成
            self.formatting_completed.emit(failed_files)
        except Exception as e:
            import traceback
            print(f"Error in FormatAllJsonThread: {e}\n{traceback.format_exc()}")
            self.formatting_completed.emit([("Unknown error", str(e))])
    
    def stop(self):
        self.is_running = False