import os
import orjson
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
    在行为包中搜索物品定义文件
    
    Args:
        pack_info: 包信息对象
    
    Returns:
        tuple: (物品列表, 解析失败的JSON文件数)
    """
    results = []
    failed_json_count = 0
    
    # 检查是否为行为包
    if pack_info.type != 'behavior':
        return results, failed_json_count
    
    items_dir = os.path.join(pack_info.path, 'items')
    
    # 如果没有物品目录，返回空结果
    if not os.path.exists(items_dir):
        return results, failed_json_count
    
    # 递归搜索所有JSON文件
    for root, _, files in os.walk(items_dir):
        for file in files:
            if not file.endswith('.json'):
                continue
            
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, pack_info.path)
            
            try:
                with open(filepath, 'rb') as f:
                    content = f.read()
                    data = orjson.loads(content)
                    
                # 标准化数据路径
                if isinstance(data, dict) and "minecraft:item" in data:
                    item_data = data["minecraft:item"]
                    components = item_data.get("components", {})
                    
                    if "minecraft:display_name" in components:
                        display_name = components["minecraft:display_name"]
                        name_value = display_name.get("value", "")
                        
                        # 新增：如果value为空，跳过该条目
                        if not name_value:
                            continue
                        
                        # 新增：过滤掉以"item."开头且以".name"结尾的物品名称
                        if name_value.startswith("item.") and name_value.endswith(".name"):
                            continue
                        
                        # 新增：过滤掉只包含特殊符号（没有英文字母或中文）的值
                        if not contains_letters_or_chinese(name_value):
                            continue
                        
                        # 检查是否包含中文字符
                        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in name_value)
                        
                        # 保存结果，只使用文件名作为显示名
                        results.append({
                            'type': 'item_name',
                            'key': file.replace('.json', ''),
                            'value': name_value,
                            'filename': os.path.basename(file),  # 只使用文件名，不包含路径
                            'filepath': filepath,
                            'full_data': data,  # 保存完整的JSON数据以便后续修改
                            'json_path': ['minecraft:item', 'components', 'minecraft:display_name', 'value'],
                            'has_chinese': has_chinese  # 添加中文标记
                        })
            
            except Exception as e:
                failed_json_count += 1
                print(f"解析物品JSON文件失败: {filepath}")
                print(traceback.format_exc())
    
    return results, failed_json_count

