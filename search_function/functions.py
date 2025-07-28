import os
import re
import traceback
from concurrent.futures import ThreadPoolExecutor

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

def extract_rawtext_from_file(file_path):
    """从mcfunction文件中提取rawtext内的text字段内容
    
    Args:
        file_path: mcfunction文件路径
        
    Returns:
        list: 包含提取结果的列表，每个结果是一个字典
    """
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
            
        # 定义要查找的模式 - 匹配 "rawtext": [ { "text": "内容" } ]
        pattern = r'"rawtext"\s*:\s*\[\s*{\s*"text"\s*:\s*"([^"]*)"'
        
        for line_number, line in enumerate(content, 1):
            matches = re.finditer(pattern, line)
            
            for match in matches:
                text_value = match.group(1)
                
                # 跳过只包含特殊符号的值
                if not contains_letters_or_chinese(text_value):
                    continue
                
                # 检查是否包含中文字符
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text_value)
                
                results.append({
                    'filename': os.path.basename(file_path),
                    'filepath': str(file_path),
                    'type': 'mcfunction_text',
                    'value': text_value,
                    'has_chinese': has_chinese,
                    'line': line_number,
                    'original_line': line.strip()  # 保存原始行用于后续精确替换
                })
    
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {str(e)}")
        print(traceback.format_exc())
    
    return results

def search(pack):
    """在行为包的functions文件夹中搜索mcfunction文件中的rawtext内的text内容
    
    Args:
        pack: 包信息对象
        
    Returns:
        tuple: (搜索结果列表, 失败的文件数量)
    """
    if not pack or pack.type != 'behavior':
        return [], 0
    
    functions_dir = os.path.join(pack.path, 'functions')
    if not os.path.isdir(functions_dir):
        return [], 0
    
    mcfunction_files = []
    for root, _, files in os.walk(functions_dir):
        for file in files:
            if file.endswith('.mcfunction'):
                mcfunction_files.append(os.path.join(root, file))
    
    all_results = []
    failed_count = 0
    
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(extract_rawtext_from_file, f): f for f in mcfunction_files}
        for future in future_to_file:
            try:
                file_results = future.result()
                all_results.extend(file_results)
            except Exception as exc:
                print(f'{future_to_file[future]} 生成异常: {exc}')
                failed_count += 1
    
    return all_results, failed_count
