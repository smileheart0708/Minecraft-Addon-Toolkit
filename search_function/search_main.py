from PyQt6.QtCore import QObject, QThread, pyqtSignal
from found import PackInfo
from save import translation_store  # 导入翻译数据存储
from .lang import search as search_lang
from .entities import search as search_entities
from .items import search as search_items
from .scripts import search as search_scripts
from .functions import search as search_functions  # 导入functions模块

class SearchWorker(QThread):
    results_ready = pyqtSignal(list, str, int)  # (results, pack_type, failed_json_count)
    search_error = pyqtSignal(str)

    def __init__(self, pack_info: PackInfo, search_text: str, parent=None):
        super().__init__(parent)
        self.pack_info = pack_info
        self.search_text = search_text.lower() # Normalize search text to lower case here
        self._is_running = True

    def run(self):
        try:
            results = []
            if not self._is_running: return

            if self.pack_info.type == 'resources':
                pack_results = search_lang(self.pack_info)
                for result in pack_results:
                    if not self._is_running: return
                    # Ensure 'key' and 'value' exist and are strings before calling .lower()
                    key_match = self.search_text in result.get('key', '').lower() if isinstance(result.get('key'), str) else False
                    value_match = self.search_text in result.get('value', '').lower() if isinstance(result.get('value'), str) else False
                    if self.search_text and not (key_match or value_match):
                        continue
                    results.append(result)
                
                # 存储结果到翻译存储
                translation_store.store_search_results(self.pack_info, results)
                if self._is_running: self.results_ready.emit(results, 'resources', 0) # Assuming lang search doesn't have json parsing errors for now

            elif self.pack_info.type == 'behavior':
                all_pack_results = []
                total_failed_json_count = 0
                # Entities search
                if not self._is_running: return
                entity_results, entity_failed_count = search_entities(self.pack_info)
                all_pack_results.extend(entity_results)
                total_failed_json_count += entity_failed_count

                # Items search
                if not self._is_running: return
                item_results, item_failed_count = search_items(self.pack_info)
                all_pack_results.extend(item_results)
                total_failed_json_count += item_failed_count
                
                # Scripts search - 脚本搜索
                if not self._is_running: return
                script_results, script_failed_count = search_scripts(self.pack_info)
                all_pack_results.extend(script_results)
                total_failed_json_count += script_failed_count
                
                # Functions search - 新添加的函数搜索
                if not self._is_running: return
                function_results, function_failed_count = search_functions(self.pack_info)
                all_pack_results.extend(function_results)
                total_failed_json_count += function_failed_count
                
                filtered_results = []
                for result in all_pack_results:
                    if not self._is_running: return
                    # Ensure 'filename' and 'value' exist and are strings
                    filename_match = self.search_text in result.get('filename', '').lower() if isinstance(result.get('filename'), str) else False
                    value_match = self.search_text in result.get('value', '').lower() if isinstance(result.get('value'), str) else False
                    if self.search_text and not (filename_match or value_match):
                        continue
                    filtered_results.append(result)
                
                # 存储结果到翻译存储
                translation_store.store_search_results(self.pack_info, filtered_results)
                if self._is_running: self.results_ready.emit(filtered_results, 'behavior', total_failed_json_count)
            else:
                if self._is_running: self.search_error.emit(f"未知的包类型: {self.pack_info.type}")

        except Exception as e:
            import traceback
            print(f"Error in SearchWorker: {e}\n{traceback.format_exc()}")
            if self._is_running: self.search_error.emit(str(e))

    def stop(self):
        self._is_running = False

class SearchController(QObject):
    results_ready = pyqtSignal(list, str, int)  # (results, pack_type, failed_json_count)
    search_error = pyqtSignal(str)
    search_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_worker = None
        self.current_pack_info = None

    def start_search(self, pack_info: PackInfo, search_text: str):
        self.current_pack_info = pack_info
        
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            # Optionally wait for it to finish or handle overlap if necessary
            # For now, we assume stop() is effective quickly or a new worker replaces the old one's relevance

        self.search_worker = SearchWorker(pack_info, search_text)
        self.search_worker.results_ready.connect(self.results_ready)
        self.search_worker.search_error.connect(self.search_error)
        self.search_worker.finished.connect(self._on_worker_finished)
        self.search_worker.start()

    def _on_worker_finished(self):
        # Check if the worker that finished is the current one, 
        # in case a new search was started before the old one fully stopped and emitted finished.
        # For simplicity, we assume the finished signal corresponds to the last worker started by this controller.
        if self.search_worker and not self.search_worker.isRunning(): # Ensure it's truly finished
             self.search_worker = None # Clear reference only if it's the one that finished
        self.search_finished.emit()

    def stop_search(self):
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            # self.search_worker = None # Don't nullify here, let _on_worker_finished handle it.

    def is_running(self):
        return self.search_worker is not None and self.search_worker.isRunning()
        
    def get_current_results(self):
        """获取当前包的搜索结果"""
        if self.current_pack_info:
            return translation_store.get_data(self.current_pack_info)
        return []
        
    def update_item(self, item_index, new_value):
        """更新特定条目的值"""
        if self.current_pack_info:
            return translation_store.update_item(self.current_pack_info, item_index, new_value)
        return False
        
    def is_data_modified(self):
        """检查当前数据是否已修改"""
        if self.current_pack_info:
            return translation_store.is_modified(self.current_pack_info)
        return False
        
    def reset_modified_status(self):
        """重置修改状态"""
        if self.current_pack_info:
            translation_store.reset_modified_status(self.current_pack_info)