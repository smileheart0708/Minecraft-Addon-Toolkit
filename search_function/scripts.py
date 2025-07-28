import os
import re
from concurrent.futures import ThreadPoolExecutor
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

def extract_title_from_file(file_path):
    """从JS文件中提取.title(), .button(), .body()和sendMessage括号内的内容
    
    Args:
        file_path: JS文件路径
        
    Returns:
        list: 包含提取结果的列表，每个结果是一个字典
    """
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 定义要查找的模式
        patterns = {
            'script_title': {
                'pattern': r'\.title\(\s*"([^"]*)"\s*\)',
                'skip_condition': lambda value: '_' in value or ':' in value
            },
            'script_button': {
                'pattern': r'\.button\(\s*"([^"]*)"\s*,\s*"[^"]*"\s*\)',
                'skip_condition': lambda value: False
            },
            'script_body': {
                'pattern': r'\.body\s*\(\s*["\']([^"\']*?)["\'\s]*\)',
                'skip_condition': lambda value: False
            },
            'script_sendMessage': {
                # 允许任意对象调用 (.sendMessage) 且支持 ` " ' 三种引号，捕获括号内完整文本
                'pattern': r'\.sendMessage\s*\(\s*[`\'\"]([\s\S]*?)[`\'\"]\s*\)',
                'skip_condition': lambda value: False
            },
            'script_rawtext': {
                # 匹配 titleraw ... {"rawtext":[{"text":"..."}]}
                'pattern': r'titleraw\s+.*?\{\s*"rawtext"\s*:\s*\[\s*\{\s*"text"\s*:\s*"([^"]*)"\s*\}\s*\]\s*\}',
                'skip_condition': lambda value: False
            }
        }
        
        # 处理每种模式
        for type_name, pattern_info in patterns.items():
            matches = re.finditer(pattern_info['pattern'], content)
            skip_condition = pattern_info['skip_condition']
            
            for match in matches:
                value = match.group(1)
                
                # 计算匹配位置的行号
                line_number = content[:match.start()].count('\n') + 1
                
                # 检查是否包含中文字符
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in value)
                
                # 应用跳过条件
                if skip_condition(value):
                    continue
                
                # 跳过只包含特殊符号的值
                if not contains_letters_or_chinese(value):
                    continue
                    
                results.append({
                    'filename': os.path.basename(file_path),
                    'filepath': str(file_path),
                    'type': type_name,
                    'value': value,
                    'has_chinese': has_chinese,
                    'line': line_number
                })
    
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {str(e)}")
    
    return results

def search(pack):
    """在行为包的scripts文件夹中搜索.title(), .button(), .body()和sendMessage内容
    
    Args:
        pack: 包信息对象
        
    Returns:
        tuple: (搜索结果列表, 失败的文件数量)
    """
    if not pack or pack.type != 'behavior':
        return [], 0
    
    scripts_dir = os.path.join(pack.path, 'scripts')
    if not os.path.isdir(scripts_dir):
        return [], 0
    
    js_files = []
    for root, _, files in os.walk(scripts_dir):
        for file in files:
            if file.endswith('.js'):
                js_files.append(os.path.join(root, file))
    
    all_results = []
    failed_count = 0
    
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(extract_title_from_file, f): f for f in js_files}
        for future in future_to_file:
            try:
                file_results = future.result()
                all_results.extend(file_results)
            except Exception as exc:
                print(f'{future_to_file[future]} 生成异常: {exc}')
                failed_count += 1
    
    return all_results, failed_count
