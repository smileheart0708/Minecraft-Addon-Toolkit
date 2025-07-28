import os
import subprocess
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtWidgets import QTableWidgetItem, QStyledItemDelegate, QAbstractItemView
from PyQt6.QtGui import QGuiApplication
from qfluentwidgets import TableWidget
from save import translation_store

class ReadOnlyDelegate(QStyledItemDelegate):
    """只读单元格代理"""
    def createEditor(self, parent, option, index):
        return None

class CustomTableWidget(TableWidget):
    """自定义表格控件，控制双击行为和可编辑性"""
    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return super().mouseDoubleClickEvent(event)
        row = index.row()
        col = index.column()
        if col == 0:
            # 文件名列, 双击在资源管理器中打开文件
            item = self.item(row, col)
            if item:
                filepath = item.data(Qt.ItemDataRole.UserRole + 1)
                if filepath and os.path.exists(filepath):
                    # 使用 subprocess 在资源管理器中打开并选中文件
                    normalized_path = os.path.normpath(filepath)
                    subprocess.Popen(f'explorer /select,"{normalized_path}"')
                else:
                    # 如果没有filepath或文件不存在, 作为后备可以复制单元格内容
                    QGuiApplication.clipboard().setText(item.text())
            return
        elif col == 1:
            # 类型列，双击无反应
            return
        else:
            # 其他列（值列）正常编辑
            return super().mouseDoubleClickEvent(event)
    
    def edit(self, index, trigger, event):
        # 只允许第2列可编辑
        if index.column() == 2:
            return super().edit(index, trigger, event)
        return False

class TableDataManager(QObject):
    """表格数据管理器，负责表格数据的管理和操作"""
    
    # 定义信号
    data_changed = pyqtSignal()
    
    def __init__(self, table_widget):
        super().__init__()
        self.table_widget = table_widget
        self.current_pack_info = None
        
        # 用于存储原始值，以便检测更改
        self.original_values = {}
        # 用于跟踪表格单元格的原始键和语言文件名（针对资源包）
        self.cell_metadata = {} 
        # 用于存储包含中文的行号
        self.chinese_rows = set()
        
        # 连接单元格更改信号
        self.table_widget.itemChanged.connect(self.on_item_changed)
    
    def set_current_pack(self, pack_info):
        """设置当前处理的包信息"""
        self.current_pack_info = pack_info
    
    def on_item_changed(self, item):
        """当表格单元格内容改变时调用"""
        # 仅当值列（第2列）更改时更新状态
        if item.column() == 2:
            row = item.row()
            current_text = item.text()  # 表格中的文本，包含 '\\n'
            
            # 将表格中的文本转换为实际值（把 \\n 转为 \n）
            actual_value = current_text.replace('\\n', '\n')
            
            # 获取原始值进行比较
            original_value = self.original_values.get((row, 2))
            
            # 获取数据源中的索引
            index_item = self.table_widget.item(row, 0)
            if not index_item:
                return
                
            data_index = index_item.data(Qt.ItemDataRole.UserRole)
            if data_index is None:
                return
                
            # 如果值发生改变，更新数据源并标记为未保存
            if original_value is not None and actual_value != original_value:
                # 更新数据源
                success = translation_store.update_item(self.current_pack_info, data_index, actual_value)
                if success:
                    # 发出数据变更信号
                    self.data_changed.emit()
    
    def populate_table(self, results, pack_type):
        """用搜索结果填充表格"""
        self.table_widget.blockSignals(True)
        try:
            self.clear_table()
            
            if not results:
                return
                
            filename_counts = {} # 用于生成唯一的文件名

            if pack_type == 'resources':
                self.table_widget.setHorizontalHeaderLabels(['键值', '类型', '值'])
                for i in range(3):
                    self.table_widget.setColumnHidden(i, False)
                self.table_widget.setColumnHidden(1, True)  # 隐藏类型列
                for index, result in enumerate(results):
                    self.add_row_to_table(result, index, is_resource_pack=True, filename_counts=filename_counts)
            elif pack_type == 'behavior':
                self.table_widget.setHorizontalHeaderLabels(['文件名', '类型', '值'])
                for i in range(3):
                    self.table_widget.setColumnHidden(i, False)
                for index, result in enumerate(results):
                    self.add_row_to_table(result, index, is_resource_pack=False, filename_counts=filename_counts)
        finally:
            self.table_widget.blockSignals(False)
    
    def add_row_to_table(self, result, index, is_resource_pack=True, filename_counts=None):
        """将单行结果添加到表格中"""
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)

        # 存储项目在数据源中的索引
        identifier_key = 'key' if is_resource_pack else 'filename'
        
        display_identifier = result[identifier_key]
        if not is_resource_pack and filename_counts is not None:
            original_filename = result[identifier_key]
            count = filename_counts.get(original_filename, 0) + 1
            filename_counts[original_filename] = count
            if count > 1:
                display_identifier = f"{original_filename}_{count - 1}"

        identifier_widget = QTableWidgetItem(display_identifier)
        identifier_widget.setData(Qt.ItemDataRole.UserRole, index)  # 存储索引
        
        # 存储完整文件路径，用于双击打开功能
        if not is_resource_pack and 'filepath' in result:
            identifier_widget.setData(Qt.ItemDataRole.UserRole + 1, result['filepath'])

        type_widget = QTableWidgetItem(result['type'])
        # 转义换行符以便在表格中显示
        value_widget = QTableWidgetItem(result['value'].replace('\n', '\\n'))

        self.table_widget.setItem(row, 0, identifier_widget)
        self.table_widget.setItem(row, 1, type_widget)
        self.table_widget.setItem(row, 2, value_widget)

        # 存储原始值用于比较
        self.original_values[(row, 2)] = result['value']

        # 构建元数据
        metadata = {
            'has_chinese': result.get('has_chinese', False),
            'data_index': index  # 存储数据源索引
        }

        if is_resource_pack:
            metadata.update({
                'key': result['key'],
                'lang_file_name': result.get('lang_file_name', 'unknown.lang')
            })
        else:
            metadata.update({
                'filename': result['filename'],
                'type': result['type']
            })
            
            # 特别处理 script_title 类型，确保保存 filepath 和 line
            if result['type'] == 'script_title':
                if 'filepath' in result:
                    metadata['filepath'] = result['filepath']
                if 'line' in result:
                    metadata['line'] = result['line']
            # 保存其他类型的特殊字段
            if 'json_path' in result:
                metadata['json_path'] = result['json_path']
            if 'line' in result:
                metadata['line'] = result['line']

        self.cell_metadata[row] = metadata

        # 如果包含中文，添加到中文行集合
        if result.get('has_chinese', False):
            self.chinese_rows.add(row)
    
    def clear_table(self):
        """清空表格并重置状态"""
        self.table_widget.setRowCount(0)
        self.table_widget.setHorizontalHeaderLabels(['', '', ''])
        for i in range(3):
            self.table_widget.setColumnHidden(i, True)
        self.original_values.clear()
        self.cell_metadata.clear()
        self.chinese_rows.clear()
    
    def update_row_visibility(self, hide_chinese):
        """更新行的可见性"""
        # 遍历所有行
        for row in range(self.table_widget.rowCount()):
            # 检查行是否包含中文
            is_chinese_row = row in self.chinese_rows
            should_hide = is_chinese_row and hide_chinese
            
            # 设置行的可见性
            self.table_widget.setRowHidden(row, should_hide)
    
    def copy_rows(self, copy_number):
        """复制表格前几行的内容"""
        # 准备复制的内容
        copy_content = []
        copied_count = 0
        row = 0
        # 继续遍历直到达到所需的复制数量或表格结束
        while copied_count < copy_number and row < self.table_widget.rowCount():
            # 检查行是否被隐藏
            if not self.table_widget.isRowHidden(row):
                identifier_item = self.table_widget.item(row, 0)  # 键值或文件名
                value_item = self.table_widget.item(row, 2)      # 值

                if identifier_item and value_item:
                    identifier = identifier_item.text()
                    # 不转换 \n，保持原样
                    value = value_item.text()
                    copy_content.append(f"{identifier}={value}")
                    copied_count += 1
            row += 1
        
        if copy_content:
            # 将内容复制到剪贴板
            clipboard = QGuiApplication.clipboard()
            clipboard.setText('\n'.join(copy_content))
            return True, len(copy_content)
        
        return False, 0
    
    def paste_from_clipboard(self):
        """从剪贴板粘贴内容并更新表格"""
        clipboard = QGuiApplication.clipboard()
        clipboard_text = clipboard.text()

        if not clipboard_text:
            return False, "剪贴板为空"

        if not self.current_pack_info:
            return False, "未选择任何包，无法粘贴"

        # 创建键到行号的映射字典，加速查找
        key_to_row = {}
        for row in range(self.table_widget.rowCount()):
            identifier_item = self.table_widget.item(row, 0)  # 键值或文件名
            if identifier_item:
                key_to_row[identifier_item.text()] = row

        lines = clipboard_text.strip().split('\n')
        updated_count = 0
        not_found_keys = []

        for line in lines:
            if '=' not in line:
                continue
            
            parts = line.split('=', 1)
            key_from_clipboard = parts[0].strip()
            value_from_clipboard = parts[1].strip()

            # 使用字典直接查找，而不是遍历整个表格
            if key_from_clipboard in key_to_row:
                row = key_to_row[key_from_clipboard]
                # 检查值列是否存在
                value_item = self.table_widget.item(row, 2)
                # 获取原始值（表格中显示的文本，需转回\n为\n）
                if value_item:
                    current_value = value_item.text().replace('\\n', '\n')
                    if current_value == value_from_clipboard:
                        continue  # 跳过相同内容
                    value_item.setText(value_from_clipboard.replace('\n', '\\n'))
                else:
                    self.table_widget.setItem(row, 2, QTableWidgetItem(value_from_clipboard.replace('\n', '\\n')))
                updated_count += 1
            else:
                not_found_keys.append(key_from_clipboard)

        if updated_count > 0:
            return True, f"成功更新了 {updated_count} 个条目"
        else:
            return False, "剪贴板中的内容未在表格中找到匹配的键"
    
    def is_data_modified(self):
        """检查数据是否已修改"""
        if not self.current_pack_info:
            return False
        return translation_store.is_modified(self.current_pack_info)
    
    def save_changes(self):
        """保存更改"""
        if not self.current_pack_info:
            return False, "未选择任何包，无法保存"
        
        # 检查是否有修改
        if not self.is_data_modified():
            return False, "没有检测到任何更改"

        # **修复点**: 找出真正被修改的条目
        items_to_save = []
        all_data = translation_store.get_data(self.current_pack_info)
        
        for row in range(self.table_widget.rowCount()):
            # 获取原始值
            original_value = self.original_values.get((row, 2))
            
            # 获取当前值
            current_item = self.table_widget.item(row, 2)
            if not current_item:
                continue
            current_value = current_item.text().replace('\\n', '\n')
            
            # 比较值是否发生变化
            if original_value is not None and original_value != current_value:
                # 获取该行对应的完整数据项
                index_item = self.table_widget.item(row, 0)
                if index_item:
                    data_index = index_item.data(Qt.ItemDataRole.UserRole)
                    if data_index is not None and 0 <= data_index < len(all_data):
                        items_to_save.append(all_data[data_index])

        if not items_to_save:
            # 虽然标记为已修改，但可能改回了原样，实际上没有需要保存的
            return False, "没有检测到任何需要保存的更改"
            
        # 导入保存逻辑
        from save import main_save_logic
        
        # 调用主保存逻辑，并传入真正需要保存的条目
        success, message = main_save_logic(self.current_pack_info, items_to_save)
        
        return success, message
    
    def get_visible_rows_count(self):
        """获取可见行数"""
        visible_rows = sum(1 for row in range(self.table_widget.rowCount()) 
                          if not self.table_widget.isRowHidden(row))
        total_rows = self.table_widget.rowCount()
        return visible_rows, total_rows
