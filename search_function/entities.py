import orjson
import os
import traceback
import re
from pathlib import Path

def contains_letters_or_chinese(text):
    """
    检查文本是否包含英文字母或中文字符
    
    Args:
        text: 要检查的文本
        
    Returns:
        bool: 如果包含英文字母或中文则返回True，否则返回False
    """
    # 检查英文字母
    has_letters = bool(re.search('[a-zA-Z]', text))
    # 检查中文字符
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    
    return has_letters or has_chinese

def search(pack_info):
    """
    在行为包中搜索实体定义文件
    
    Args:
        pack_info: 包信息对象
    
    Returns:
        tuple: (实体列表, 解析失败的JSON文件数)
    """
    results = []
    failed_json_count = 0
    
    # 检查是否为行为包
    if pack_info.type != 'behavior':
        return results, failed_json_count
    
    entities_dir = os.path.join(pack_info.path, 'entities')
    
    # 如果没有实体目录，返回空结果
    if not os.path.exists(entities_dir):
        return results, failed_json_count
    
    # 递归搜索所有JSON文件
    for root, _, files in os.walk(entities_dir):
        for file in files:
            if not file.endswith('.json'):
                continue
            
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'rb') as f:
                    content = f.read()
                    data = orjson.loads(content)
                    
                # 检查是否为实体定义文件
                if isinstance(data, dict) and "minecraft:entity" in data:
                    entity_data = data["minecraft:entity"]
                    components = entity_data.get("components", {})
                    
                    # 处理名称组件
                    if "minecraft:nameable" in components:
                        nameable = components["minecraft:nameable"]
                        name_value = nameable.get("name", "")
                        
                        # 如果name值为空，跳过
                        if not name_value:
                            continue
                            
                        # 过滤掉以"entity."开头且以".name"结尾的实体名称
                        if name_value.startswith("entity.") and name_value.endswith(".name"):
                            continue
                            
                        # 新增：过滤掉只包含特殊符号（没有英文字母或中文）的值
                        if not contains_letters_or_chinese(name_value):
                            continue
                        
                        # 检查是否包含中文字符
                        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in name_value)
                        
                        # 保存结果
                        results.append({
                            'type': 'entity_name',
                            'key': os.path.basename(file).replace('.json', ''),
                            'value': name_value,
                            'filename': os.path.basename(file),
                            'filepath': filepath,
                            'full_data': data,
                            'json_path': ['minecraft:entity', 'components', 'minecraft:nameable', 'name'],
                            'has_chinese': has_chinese
                        })
            
            except Exception as e:
                failed_json_count += 1
                print(f"解析实体JSON文件失败: {filepath}")
                print(traceback.format_exc())
    
    return results, failed_json_count

def _find_say_commands(data, filename, filepath, results, path=None):
    """递归查找JSON对象中的say指令"""
    if path is None:
        path = []
        
    if isinstance(data, dict):
        if 'queue_command' in data and 'command' in data['queue_command']:
            commands = data['queue_command']['command']
            if isinstance(commands, list):
                current_path = path + ['queue_command', 'command']
                for i, cmd in enumerate(commands):
                    if isinstance(cmd, str) and cmd.strip().startswith('say '):
                        say_text = cmd.strip()[4:]  # 移除'say '
                        # 检查是否包含中文字符
                        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in say_text)
                        
                        # 保存结果，包含完整数据和路径
                        results.append({
                            'type': 'say',
                            'filename': filename,
                            'value': say_text,
                            'has_chinese': has_chinese,
                            'filepath': filepath,
                            'full_data': data,  # 保存完整的JSON数据
                            'json_path': current_path + [i],  # 保存JSON路径
                            'cmd_index': i  # 保存命令在数组中的索引
                        })
        
        # 继续递归搜索
        for key, value in data.items():
            _find_say_commands(value, filename, filepath, results, path + [key])
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _find_say_commands(item, filename, filepath, results, path + [i])