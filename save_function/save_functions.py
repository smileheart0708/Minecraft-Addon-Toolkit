import os
import re
import traceback

def save_mcfunction_entries(pack_info, mcfunction_entries):
    """保存mcfunction文件中的rawtext文本条目
    
    Args:
        pack_info: 包信息对象
        mcfunction_entries: mcfunction条目列表
    
    Returns:
        tuple: (成功状态, 保存数量, 消息)
    """
    success_count = 0
    errors = []
    
    try:
        # 按文件路径分组
        entries_by_filepath = {}
        for entry in mcfunction_entries:
            if entry['type'] != 'mcfunction_text':
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
            if not os.path.exists(filepath):
                errors.append(f"找不到文件: {filepath}")
                continue
                
            try:
                # 读取文件内容
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.readlines()
                
                # 标记文件是否被修改
                file_modified = False
                
                # 按行号排序，从后往前处理，避免行号偏移
                sorted_entries = sorted(file_entries, key=lambda x: x.get('line', 0), reverse=True)
                
                for entry in sorted_entries:
                    line_number = entry.get('line', 0)
                    new_value = entry.get('value', '')
                    original_line = entry.get('original_line', '')
                    
                    if line_number <= 0 or line_number > len(content):
                        errors.append(f"行号无效: {line_number}")
                        continue
                    
                    current_line = content[line_number - 1].strip()
                    
                    # 检查当前行是否与记录的原始行匹配
                    if original_line and original_line in current_line:
                        # 构建替换模式，精确替换text字段的值
                        pattern = r'("text"\s*:\s*")([^"]*)(")'
                        
                        # 使用正则表达式替换text值
                        new_line = re.sub(
                            pattern,
                            lambda m: f'{m.group(1)}{new_value}{m.group(3)}',
                            content[line_number - 1]
                        )
                        
                        # 如果替换后的行与原行不同，则更新内容
                        if new_line != content[line_number - 1]:
                            content[line_number - 1] = new_line
                            file_modified = True
                            success_count += 1
                
                # 如果文件被修改，保存回文件
                if file_modified:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.writelines(content)
            
            except Exception as e:
                errors.append(f"处理文件 {filepath} 时出错: {str(e)}")
                print(traceback.format_exc())
        
        if errors:
            return len(errors) < len(mcfunction_entries), success_count, "、".join(errors[:3])
        else:
            return True, success_count, f"成功保存了 {success_count} 个mcfunction文本"
            
    except Exception as e:
        return False, 0, f"保存mcfunction条目时出错: {str(e)}\n{traceback.format_exc()}"
