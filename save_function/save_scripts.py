import os
import re
import traceback

def save_script_entries(pack_info, script_entries):
    """保存脚本条目 - 改进版本
    
    Args:
        pack_info: 包信息对象
        script_entries: 脚本条目列表
    
    Returns:
        tuple: (成功状态, 保存数量, 消息)
    """
    success_count = 0
    errors = []
    
    try:
        # 按文件分组处理，避免重复读写同一文件
        files_to_process = {}
        for entry in script_entries:
            filepath = entry.get('filepath')
            if filepath not in files_to_process:
                files_to_process[filepath] = []
            files_to_process[filepath].append(entry)
        
        # 逐个文件处理
        for filepath, entries in files_to_process.items():
            file_success, file_errors = _process_file_entries(filepath, entries)
            success_count += file_success
            errors.extend(file_errors)
                
        if errors:
            # 将详细错误格式化为多行字符串，以便日志记录
            error_details = f"共 {len(errors)} 个错误:\n- " + "\n- ".join(errors)
            return False, success_count, error_details
        else:
            return True, success_count, f"成功保存了 {success_count} 个脚本条目"
            
    except Exception as e:
        return False, 0, f"保存脚本条目时出错: {str(e)}\n{traceback.format_exc()}"

def _process_file_entries(filepath, entries):
    """处理单个文件的所有条目"""
    success_count = 0
    errors = []
    
    try:
        if not os.path.exists(filepath):
            errors.append(f"找不到文件: {filepath}")
            return 0, errors
            
        # 读取整个文件内容作为字符串
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            errors.append(f"读取文件 {filepath} 时出错: {str(e)}")
            return 0, errors
            
        original_content = content
        lines_for_context = content.splitlines() # 用于在日志中提供上下文
        
        # 按行号排序，从后往前处理，避免行号偏移
        entries_sorted = sorted(entries, key=lambda x: x.get('line', 0), reverse=True)
        
        for entry in entries_sorted:
            try:
                new_content = _replace_content_by_position(content, entry)
                if new_content != content:
                    content = new_content
                    success_count += 1
                else:
                    line_num = entry.get('line', 0)
                    error_line_content = ""
                    if 0 < line_num <= len(lines_for_context):
                        error_line_content = lines_for_context[line_num - 1].strip()
                    
                    errors.append(
                        f"文件 '{os.path.basename(filepath)}' (行 {line_num}): "
                        f"无法匹配 '{entry.get('type')}' 模式。 "
                        f"问题行内容: '{error_line_content}'"
                    )
            except Exception as e:
                errors.append(f"处理条目时出错 (行 {entry.get('line')}): {str(e)}")
        
        # 只有在内容发生变化时才写入文件
        if content != original_content:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                errors.append(f"保存文件 {filepath} 时出错: {str(e)}")
                # 如果写入失败，重置成功计数，因为实际上没有成功保存
                return 0, errors
                
    except Exception as e:
        errors.append(f"处理文件 {filepath} 时出错: {str(e)}")
        
    return success_count, errors

def _replace_content_by_position(content, entry):
    """基于位置和类型替换内容"""
    line_number = int(entry.get('line', 0))
    new_value = entry.get('value', '')
    entry_type = entry.get('type', 'script_title')
    
    if line_number <= 0:
        return content
        
    lines = content.splitlines(keepends=True)
    
    if not (0 < line_number <= len(lines)):
        return content
        
    target_line = lines[line_number - 1]
    
    # 改进的模式匹配 - 使用更精确的模式
    patterns = {
        'script_title': {
            'pattern': r'(\.title\s*\(\s*["\'])([^"\']*?)(["\'\s]*\))',
            'replacement': lambda m, val: f'{m.group(1)}{val}{m.group(3)}'
        },
        'script_button': {
            'pattern': r'(\.button\s*\(\s*["\'])([^"\']*?)(["\'\s,]+["\'][^"\']*["\'\s]*\))',
            'replacement': lambda m, val: f'{m.group(1)}{val}{m.group(3)}'
        },
        'script_body': {
            'pattern': r'(\.body\s*\(\s*["\'])([^"\']*?)(["\'\s]*\))',
            'replacement': lambda m, val: f'{m.group(1)}{val}{m.group(3)}'
        },
        'script_sendMessage': {
            # 支持任意对象 .sendMessage 且兼容 ` " ' 三种引号
            'pattern': r'(\.sendMessage\s*\(\s*[`\'\"])([\s\S]*?)([`\'\"]\s*\))',
            'replacement': lambda m, val: f'{m.group(1)}{val}{m.group(3)}'
        },
        'script_rawtext': {
            # 匹配 titleraw 中的 rawtext
            'pattern': r'(titleraw\s+.*?\{\s*"rawtext"\s*:\s*\[\s*\{\s*"text"\s*:\s*")([^"]*)("\s*\}\s*\]\s*\})',
            'replacement': lambda m, val: f'{m.group(1)}{val}{m.group(3)}'
        }
    }
    
    pattern_info = patterns.get(entry_type)
    if not pattern_info:
        return content
        
    # 尝试在目标行进行替换
    new_line = re.sub(
        pattern_info['pattern'], 
        lambda m: pattern_info['replacement'](m, new_value), 
        target_line,
        flags=re.DOTALL
    )
    
    if new_line != target_line:
        lines[line_number - 1] = new_line
        return ''.join(lines)
    
    return content
