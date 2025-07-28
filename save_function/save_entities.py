import os
import json
import traceback

def save_entity_entries(pack_info, entity_entries):
    """保存实体条目，如say命令等
    
    Args:
        pack_info: 包信息对象
        entity_entries: 实体条目列表
    
    Returns:
        tuple: (成功状态, 保存数量, 消息)
    """
    success_count = 0
    errors = []
    
    try:
        # 按文件路径分组，使用filepath而不是filename
        entries_by_filepath = {}
        for entry in entity_entries:
            if entry['type'] != 'say':
                continue
                
            filepath = entry.get('filepath')
            if not filepath:
                errors.append(f"条目缺少文件路径: {entry.get('filename', '未知')}")
                continue
                
            if filepath not in entries_by_filepath:
                entries_by_filepath[filepath] = []
            entries_by_filepath[filepath].append(entry)
        
        # 处理每个文件
        for filepath, file_entries in entries_by_filepath.items():
            # 使用第一个条目的完整数据
            if not file_entries:
                continue
                
            # 获取完整数据
            full_data = file_entries[0].get('full_data')
            if not full_data:
                errors.append(f"缺少完整数据: {file_entries[0].get('filename', '未知')}")
                continue
                
            # 标记文件是否被修改
            file_modified = False
            
            # 应用每个条目的修改
            for entry in file_entries:
                try:
                    # 获取JSON路径
                    json_path = entry.get('json_path')
                    if not json_path:
                        errors.append(f"缺少JSON路径: {entry.get('filename', '未知')}")
                        continue
                        
                    # 应用修改
                    current_data = full_data
                    for i, key in enumerate(json_path):
                        if i == len(json_path) - 1:
                            # 最后一个路径元素是命令在数组中的索引
                            # 修改为 "say " + 新值
                            current_data[key] = f"say {entry['value']}"
                            file_modified = True
                            success_count += 1
                        else:
                            current_data = current_data[key]
                            
                except Exception as e:
                    errors.append(f"修改条目时出错: {str(e)}")
                    continue
                    
            # 如果文件被修改，保存回文件
            if file_modified:
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(full_data, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    errors.append(f"保存文件时出错: {str(e)}")
                    success_count = 0  # 如果保存失败，重置成功计数
        
        if errors:
            return len(errors) < len(entity_entries), success_count, "、".join(errors[:3])
        else:
            return True, success_count, f"成功保存了 {success_count} 个实体命令"
            
    except Exception as e:
        return False, 0, f"保存实体条目时出错: {str(e)}\n{traceback.format_exc()}"
