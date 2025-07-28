import os
import json
import traceback

def save_item_entries(pack_info, items):
    """
    保存物品名称的修改
    
    Args:
        pack_info: 包信息对象
        items: 要保存的物品列表
    
    Returns:
        tuple: (是否成功, 保存成功的数量, 错误消息)
    """
    success_count = 0
    errors = []
    
    for item in items:
        try:
            # 只处理物品名称类型的条目
            if item['type'] != 'item_name':
                continue
                
            # 获取文件路径和完整数据
            filepath = item.get('filepath')
            if not filepath or not os.path.exists(filepath):
                errors.append(f"找不到物品文件: {item.get('filename', '未知')}")
                continue
                
            # 获取完整的JSON数据和修改路径
            full_data = item.get('full_data')
            json_path = item.get('json_path')
            
            if not full_data or not json_path:
                errors.append(f"缺少完整数据或JSON路径: {item.get('filename', '未知')}")
                continue
            
            # 应用修改
            current_data = full_data
            for i, key in enumerate(json_path):
                if i == len(json_path) - 1:
                    current_data[key] = item['value']
                else:
                    current_data = current_data[key]
            
            # 保存回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=4)
            
            success_count += 1
            
        except Exception as e:
            error_message = f"保存物品 {item.get('key', '未知')} 时出错: {str(e)}"
            errors.append(error_message)
            print(error_message)
            print(traceback.format_exc())
    
    if errors:
        return len(errors) < len(items), success_count, "、".join(errors[:3])
    
    return True, success_count, "成功保存物品名称"

