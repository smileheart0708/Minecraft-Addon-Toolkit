import os
import threading

def save_lang_entries(pack_info, lang_entries):
    """保存语言文件条目
    
    Args:
        pack_info: 包信息对象
        lang_entries: 语言条目列表
    
    Returns:
        tuple: (成功状态, 保存数量, 消息)
    """
    success_count = 0
    errors = []
    
    try:
        # 按语言文件名分组
        entries_by_lang_file = {}
        for entry in lang_entries:
            lang_file_name = entry.get('lang_file_name')
            if not lang_file_name:
                errors.append(f"条目缺少语言文件名: {entry}")
                continue
                
            if lang_file_name not in entries_by_lang_file:
                entries_by_lang_file[lang_file_name] = []
            entries_by_lang_file[lang_file_name].append(entry)
        
        # 处理每个语言文件
        for lang_file_name, file_entries in entries_by_lang_file.items():
            file_count, file_errors = _process_lang_file(pack_info.path, lang_file_name, file_entries)
            success_count += file_count
            errors.extend(file_errors)
            
        if errors:
            return False, success_count, "; ".join(errors[:3])
        else:
            return True, success_count, f"成功保存了 {success_count} 个语言条目"
            
    except Exception as e:
        import traceback
        return False, 0, f"保存语言条目时出错: {str(e)}\n{traceback.format_exc()}"

def _process_lang_file(base_path, lang_file_name, entries):
    """处理单个语言文件，优化为严格按key替换value，保留注释和空行，支持value中有等号"""
    success_count = 0
    errors = []

    lang_file_path = os.path.join(base_path, 'texts', lang_file_name)
    texts_dir = os.path.dirname(lang_file_path)

    # 确保目录存在
    if not os.path.exists(texts_dir):
        try:
            os.makedirs(texts_dir, exist_ok=True)
        except Exception as e:
            return 0, [f"创建目录失败: {texts_dir}, 错误: {e}"]

    # 读取现有文件
    lines = []
    if os.path.exists(lang_file_path):
        try:
            with open(lang_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return 0, [f"读取文件失败: {lang_file_path}, 错误: {e}"]

    # 创建键值映射
    modified_keys = {entry['key']: entry['value'] for entry in entries}
    existing_keys = set()
    new_lines = []

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            new_lines.append(line)
            continue
        parts = stripped_line.split('=', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            existing_keys.add(key)
            if key in modified_keys:
                new_value = modified_keys[key].replace('\n', '\\n')
                new_lines.append(f"{key}={new_value}\n")
                success_count += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # 添加新键
    for key, value in modified_keys.items():
        if key not in existing_keys:
            new_value = value.replace('\n', '\\n')
            new_lines.append(f"{key}={new_value}\n")
            success_count += 1

    # 保存文件
    try:
        with open(lang_file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception as e:
        return 0, [f"保存文件失败: {lang_file_path}, 错误: {e}"]

    return success_count, errors
