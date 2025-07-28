import os
import json5
from dataclasses import dataclass
from config import cfg  # 导入配置系统
import shared  # 导入共享变量模块


def find_manifest_json(folder_path, max_depth=5):
    """查找manifest.json文件
    
    Args:
        folder_path: 要搜索的文件夹路径
        max_depth: 最大搜索深度
        
    Returns:
        找到的manifest.json文件路径，如果未找到则返回None
    """
    for root, dirs, files in os.walk(folder_path):
        # 计算当前深度
        relative_path = os.path.relpath(root, folder_path)
        current_level = 0 if relative_path == '.' else relative_path.count(os.sep) + 1
        
        # 检查是否超过最大深度
        if current_level > max_depth:
            # 如果已经超过最大深度，不再遍历其子目录
            dirs.clear()
            continue
            
        # 检查当前目录中是否有manifest.json
        if 'manifest.json' in files:
            return os.path.join(root, 'manifest.json')
            
    return None


@dataclass
class PackInfo:
    """包信息类"""
    name: str
    path: str
    type: str  # "behavior" 或 "resources"


def scan_pack_folder(folder_path, pack_type=None, check_single_file=False):
    """扫描指定文件夹中的包
    
    Args:
        folder_path: 要扫描的文件夹路径
        pack_type: 包类型，如果为None则根据manifest自动判断
        check_single_file: 是否检查单个manifest文件(不遍历子目录)
        
    Returns:
        包含PackInfo对象的列表
    """
    packs = []
    if not folder_path or not os.path.exists(folder_path):
        return packs
    
    # 处理单文件检查模式
    if check_single_file:
        manifest_path = find_manifest_json(folder_path, max_depth=0)
        if manifest_path:
            pack_info = parse_manifest(manifest_path)
            if pack_info and (not pack_type or pack_info.type == pack_type):
                packs.append(pack_info)
        return packs
        
    # 常规目录扫描模式    
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            manifest_path = find_manifest_json(item_path, max_depth=0)
            if manifest_path:
                pack_info = parse_manifest(manifest_path)
                if pack_info:
                    # 如果指定了包类型，则覆盖解析出的类型
                    if pack_type:
                        pack_info.type = pack_type
                    packs.append(pack_info)
    
    return packs


def scan_packs():
    """扫描app文件夹和用户选择的文件夹中的行为包和资源包
    
    Returns:
        tuple: (behavior_packs, resource_packs) 两个列表，分别包含行为包和资源包的PackInfo对象
    """
    behavior_packs = []
    resource_packs = []
    
    # 用于跟踪已添加的包路径，避免重复
    behavior_paths = set()
    resource_paths = set()
    
    # 从配置中获取应用文件夹路径
    app_folder = cfg.appFolder.value
    
    # 如果配置的路径无效，使用默认路径
    if not app_folder or not os.path.exists(app_folder):
        app_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
    
    # 扫描行为包和资源包文件夹
    # scan_pack_folder会自动检查路径是否有效
    behavior_folder = os.path.join(app_folder, 'Behavior_Packs')
    resource_folder = os.path.join(app_folder, 'Resource_Packs')
    
    # 添加行为包，避免重复
    for pack in scan_pack_folder(behavior_folder, 'behavior'):
        if pack.path not in behavior_paths:
            behavior_packs.append(pack)
            behavior_paths.add(pack.path)
    
    # 添加资源包，避免重复
    for pack in scan_pack_folder(resource_folder, 'resources'):
        if pack.path not in resource_paths:
            resource_packs.append(pack)
            resource_paths.add(pack.path)
    
    # 扫描用户选择的文件夹
    # 与translate.py中保持一致，分别扫描行为包和资源包，并使用check_single_file=True
    if shared.user_folder:
        # 添加用户文件夹中的行为包，避免重复
        for pack in scan_pack_folder(shared.user_folder, 'behavior', check_single_file=True):
            if pack.path not in behavior_paths:
                behavior_packs.append(pack)
                behavior_paths.add(pack.path)
        
        # 添加用户文件夹中的资源包，避免重复
        for pack in scan_pack_folder(shared.user_folder, 'resources', check_single_file=True):
            if pack.path not in resource_paths:
                resource_packs.append(pack)
                resource_paths.add(pack.path)
    
    return behavior_packs, resource_packs


def parse_manifest(manifest_path):
    """解析manifest.json文件，提取包信息
    
    Args:
        manifest_path: manifest.json文件路径
        
    Returns:
        PackInfo对象，如果解析失败则返回None
    """
    try:
        # 获取包的目录路径
        pack_dir = os.path.dirname(manifest_path)
        
        # 使用json5解析
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json5.load(f)
        
        # 获取包名称
        name = "未知包"
        if 'header' in manifest and 'name' in manifest['header']:
            name = manifest['header']['name']
        
        # 获取包类型
        pack_type = None
        if 'modules' in manifest and manifest['modules'] and 'type' in manifest['modules'][0]:
            module_type = manifest['modules'][0]['type']
            if module_type in ('data', 'script'):
                pack_type = 'behavior'
            elif module_type == 'resources':
                pack_type = 'resources'
        
        if pack_type:
            return PackInfo(name, pack_dir, pack_type)
            
        return None
    except (OSError, json5.JSONDecodeError) as e:
        print(f"Manifest解析错误: {manifest_path} - {e}")
        return None