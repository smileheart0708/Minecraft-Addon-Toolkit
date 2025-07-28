import os
import json5
import json
import shutil
import threading
from functions import format_json_file
from services.log_service import log_error

class PackManager:
    """包管理类，负责包的重命名和删除等操作"""
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
    
    def rename_pack(self, pack_path, new_name):
        """重命名包"""
        try:
            # 获取manifest.json文件路径
            manifest_path = os.path.join(pack_path, 'manifest.json')
            if not os.path.exists(manifest_path):
                return False, f"找不到manifest.json文件: {manifest_path}"
            
            # 读取manifest.json文件（使用json5）
            with open(manifest_path, 'r', encoding='utf-8') as f:
                try:
                    manifest_data = json5.load(f)
                except Exception:
                    return False, "无法解析manifest.json文件，请检查文件格式"
            
            # 修改name字段
            if 'header' in manifest_data and 'name' in manifest_data['header']:
                manifest_data['header']['name'] = new_name
                
                # 写入修改后的manifest.json文件
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest_data, f, ensure_ascii=False, indent=4)
                
                # 格式化JSON文件（可选）
                format_json_file(manifest_path)
                
                return True, f"已重命名包为: {new_name}"
            else:
                return False, "manifest.json文件格式错误: 缺少header.name字段"
        
        except Exception as e:
            error_msg = f"重命名包时出错: {str(e)}"
            log_error(error_msg)
            return False, error_msg
    
    def delete_pack(self, pack_path, pack_name):
        """删除包"""
        try:
            if os.path.exists(pack_path):
                # 删除包目录
                shutil.rmtree(pack_path)
                return True, f"已删除: {pack_name}"
            else:
                return False, f"找不到: {pack_name}"
        except Exception as e:
            error_msg = f"删除时出错：{str(e)}"
            log_error(error_msg)
            return False, error_msg

class TranslationDataStore:
    """集中存储所有类型的翻译数据"""
    
    def __init__(self):
        self._data = {}  # 按包ID存储数据
        self._modified = {}  # 跟踪修改状态
        self._lock = threading.Lock()
    
    def store_search_results(self, pack_info, results):
        """存储搜索结果"""
        pack_id = f"{pack_info.type}:{pack_info.path}"
        with self._lock:
            self._data[pack_id] = results
            self._modified[pack_id] = False
    
    def get_data(self, pack_info):
        """获取指定包的数据"""
        pack_id = f"{pack_info.type}:{pack_info.path}"
        with self._lock:
            return self._data.get(pack_id, [])
    
    def update_item(self, pack_info, item_index, new_value):
        """更新特定项的值"""
        pack_id = f"{pack_info.type}:{pack_info.path}"
        with self._lock:
            if pack_id in self._data and 0 <= item_index < len(self._data[pack_id]):
                self._data[pack_id][item_index]['value'] = new_value
                self._modified[pack_id] = True
                return True
            return False
    
    def is_modified(self, pack_info):
        """检查指定包的数据是否已修改"""
        pack_id = f"{pack_info.type}:{pack_info.path}"
        with self._lock:
            return self._modified.get(pack_id, False)
    
    def reset_modified_status(self, pack_info):
        """重置修改状态"""
        pack_id = f"{pack_info.type}:{pack_info.path}"
        with self._lock:
            self._modified[pack_id] = False
    
    def get_modified_items(self, pack_info):
        """获取已修改的项目"""
        pack_id = f"{pack_info.type}:{pack_info.path}"
        
        with self._lock:
            if pack_id not in self._data:
                return []
            
            # 返回所有项目，保存函数将决定哪些需要保存
            return self._data[pack_id]

# 创建全局实例
translation_store = TranslationDataStore()

def main_save_logic(pack_info, items_to_save):
    """主保存逻辑，根据不同类型的项目选择不同的保存方法"""
    try:
        # **修复点**: 优先使用传入的 items_to_save 列表
        # 如果 items_to_save 为 None (旧的调用方式)，则从 store 获取数据以保持兼容
        if items_to_save is not None:
            all_items = items_to_save
        else:
            # 旧逻辑：获取所有标记为已修改的包的项目（可能包含未修改项）
            all_items = translation_store.get_modified_items(pack_info)
        
        if not all_items:
            return True, "没有需要保存的更改"
            
        # 导入各种保存函数
        from save_function.save_lang import save_lang_entries
        from save_function.save_items import save_item_entries
        from save_function.save_scripts import save_script_entries
        from save_function.save_entities import save_entity_entries
        from save_function.save_functions import save_mcfunction_entries  # 导入新的保存函数
        
        # 根据类型分组
        items_by_type = {}
        for item in all_items:
            item_type = item.get('type', 'unknown')
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append(item)
        
        # 调用不同的保存函数
        success_count = 0
        error_messages = []
        
        # 处理资源包语言文件
        if pack_info.type == 'resources' and 'language_entry' in items_by_type:
            success, count, message = save_lang_entries(pack_info, items_by_type['language_entry'])
            if success:
                success_count += count
            else:
                log_error(f"保存语言文件失败: {message}")
                error_messages.append(message)
        
        # 处理行为包物品名称
        if pack_info.type == 'behavior' and 'item_name' in items_by_type:
            success, count, message = save_item_entries(pack_info, items_by_type['item_name'])
            if success:
                success_count += count
            else:
                log_error(f"保存物品名称失败: {message}")
                error_messages.append(message)
        
        # 处理所有类型的脚本条目 - 改进版本
        script_types = ['script_title', 'script_button', 'script_body', 'script_sendMessage', 'script_rawtext']
        script_entries = []
        
        for script_type in script_types:
            if script_type in items_by_type:
                script_entries.extend(items_by_type[script_type])
        
        if script_entries:
            success, count, message = save_script_entries(pack_info, script_entries)
            if success:
                success_count += count
            else:
                log_error(f"保存脚本失败: {message}")
                error_messages.append(message)
                
        # 处理实体say命令
        if pack_info.type == 'behavior' and 'say' in items_by_type:
            success, count, message = save_entity_entries(pack_info, items_by_type['say'])
            if success:
                success_count += count
            else:
                log_error(f"保存实体say命令失败: {message}")
                error_messages.append(message)
        
        # 处理mcfunction文件中的rawtext文本
        if pack_info.type == 'behavior' and 'mcfunction_text' in items_by_type:
            success, count, message = save_mcfunction_entries(pack_info, items_by_type['mcfunction_text'])
            if success:
                success_count += count
            else:
                log_error(f"保存mcfunction失败: {message}")
                error_messages.append(message)
        
        # 组合结果消息
        if error_messages:
            error_msg = "、".join(error_messages[:3])
            if len(error_messages) > 3:
                error_msg += f"...等{len(error_messages)}个错误"
            return success_count > 0, f"保存了{success_count}个项目，但有错误: {error_msg}"
        else:
            # 保存成功后重置修改状态
            translation_store.reset_modified_status(pack_info)
            if pack_info.type == 'resources':
                return True, "成功保存语言文件"
            elif pack_info.type == 'behavior':
                return True, f"成功保存了{success_count}个项目"
            else:
                return True, "保存成功"
    
    except Exception as e:
        import traceback
        error_msg = f"保存过程中出错: {str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        return False, error_msg