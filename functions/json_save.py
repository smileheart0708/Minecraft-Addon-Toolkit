import json
import json5
import os

def format_json_file(file_path, indent=4, ensure_ascii=False):
    """
    使用json5库解析JSON文件，然后使用标准json库规范化保存回原文件
    
    参数:
        file_path (str): 要处理的JSON文件路径
        indent (int): 缩进空格数，默认为4
        ensure_ascii (bool): 是否确保ASCII编码，默认为False
        
    返回:
        tuple: (成功状态, 消息)
            - 如果成功: (True, "文件已成功格式化")
            - 如果失败: (False, 错误信息)
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
            
        # 检查文件是否是JSON文件
        if not file_path.lower().endswith('.json'):
            return False, f"不是JSON文件: {file_path}"
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用json5解析内容
        try:
            data = json5.loads(content)
        except Exception as e:
            return False, f"JSON5解析失败: {str(e)}"
        
        # 使用标准json库保存回原文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
        return True, "文件已成功格式化"
        
    except Exception as e:
        return False, f"处理文件时出错: {str(e)}"
