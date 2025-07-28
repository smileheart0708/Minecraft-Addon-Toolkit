import os
import re

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
    """搜索资源包中的语言文件
    
    Args:
        pack_info: PackInfo对象，包含包的信息
        
    Returns:
        list: 包含搜索结果的列表，每个结果是一个字典，包含文件名、行号、类型和值
    """
    # 如果不是资源包，直接返回空列表
    if pack_info.type != 'resources':
        return []
    
    # 构建texts文件夹路径
    texts_path = os.path.join(pack_info.path, 'texts')
    if not os.path.exists(texts_path):
        return []
    
    # 获取所有lang文件
    lang_files = [f for f in os.listdir(texts_path) if f.endswith('.lang')]
    if not lang_files:
        return []
    
    # 选择合适的lang文件
    if 'en_US.lang' in lang_files:
        lang_file = 'en_US.lang'
    elif len(lang_files) > 1:
        # 排除zh_CN.lang，其他文件按字母排序
        other_files = [f for f in lang_files if f != 'zh_CN.lang']
        if other_files:
            lang_file = sorted(other_files)[0]
        else:
            lang_file = 'zh_CN.lang'
    else:
        lang_file = lang_files[0]
    
    results = []
    lang_path = os.path.join(texts_path, lang_file)
    
    try:
        with open(lang_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        value = value.strip()
                        
                        # 跳过只包含特殊符号的值
                        if not contains_letters_or_chinese(value):
                            continue
                            
                        # 检查是否包含中文字符
                        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in value)
                        results.append({
                            'file': os.path.relpath(lang_path, pack_info.path),
                            'line': line_num,
                            'type': 'language_entry',
                            'key': key.strip(),
                            'value': value,
                            'has_chinese': has_chinese,  # 添加中文标记
                            'lang_file_name': lang_file  # 添加语言文件名
                        })
                    except ValueError:
                        continue
    except Exception as e:
        print(f"读取语言文件出错: {e}")
    
    return results