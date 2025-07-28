import os
import zipfile
import shutil

class ImportManager:
    """包导入管理类，负责包的导入操作"""
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        
    def get_temp_dir(self):
        """获取临时目录路径"""
        temp_dir = os.path.join(self.base_dir, 'Temp')
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
        
    def clean_temp_dir(self):
        """清理临时目录"""
        temp_dir = self.get_temp_dir()
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
    
    def import_pack(self, file_name, find_manifest_json_func, parse_manifest_func):
        """导入包文件"""
        # 创建临时目录用于解压文件
        temp_dir = self.get_temp_dir()
        
        # 解压文件到临时目录
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 查找manifest.json文件
        manifest_path = find_manifest_json_func(temp_dir)
        
        # 检查是否需要创建父文件夹来包装文件
        if manifest_path:
            # 解析manifest.json获取包名
            pack_info = parse_manifest_func(manifest_path)
            if pack_info and pack_info.name:
                # 创建以包名命名的新文件夹
                pack_folder = os.path.join(temp_dir, pack_info.name)
                os.makedirs(pack_folder, exist_ok=True)
                
                # 将所有文件移动到新文件夹中
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isfile(item_path):
                        shutil.move(item_path, os.path.join(pack_folder, item))
                    elif os.path.isdir(item_path) and item != pack_info.name:
                        shutil.move(item_path, os.path.join(pack_folder, item))
                
                # 更新manifest路径
                manifest_path = os.path.join(pack_folder, 'manifest.json')
        
        # 重新查找manifest.json文件（以防之前的移动操作）
        if not manifest_path:
            manifest_path = find_manifest_json_func(temp_dir)
        if not manifest_path:
            return False, "无效的包文件：未找到manifest.json文件"
        
        # 解析manifest.json文件
        pack_info = parse_manifest_func(manifest_path)
        if not pack_info:
            return False, "无效的包文件：manifest.json文件格式错误"
        
        # 确定目标目录
        if pack_info.type == 'behavior':
            target_dir = os.path.join(self.base_dir, 'Behavior_Packs')
        else:  # resources
            target_dir = os.path.join(self.base_dir, 'Resource_Packs')
        
        # 创建目标目录（如果不存在）
        os.makedirs(target_dir, exist_ok=True)
        
        # 将文件从临时目录移动到目标目录
        pack_dir = os.path.dirname(manifest_path)
        target_pack_dir = os.path.join(target_dir, os.path.basename(pack_dir))
        
        # 移动文件（先删除目标路径如果存在）
        shutil.rmtree(target_pack_dir, ignore_errors=True)
        shutil.move(pack_dir, target_pack_dir)
        
        # 清理临时目录
        self.clean_temp_dir()
        
        return True, f"已导入{'行为包' if pack_info.type == 'behavior' else '资源包'}: {pack_info.name}"
    
    def import_mcaddon(self, file_name, find_manifest_json_func, parse_manifest_func):
        """导入mcaddon文件，解压并处理其中的多个包"""
        # 从基础目录获取应用文件夹路径
        app_folder = self.base_dir
        
        # 定义行为包、资源包和临时文件夹的目标路径
        behavior_folder = os.path.join(app_folder, 'Behavior_Packs')
        resource_folder = os.path.join(app_folder, 'Resource_Packs')
        temp_dir = os.path.join(app_folder, 'Temp')
        
        # 确保目标目录存在
        os.makedirs(behavior_folder, exist_ok=True)
        os.makedirs(resource_folder, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        
        # 清理临时目录
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        
        # 解压mcaddon到临时目录
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 处理临时目录中的所有文件夹，查找行为包和资源包
        imported_behavior = 0
        imported_resource = 0
        
        # 获取临时目录中的所有项目
        items = [os.path.join(temp_dir, item) for item in os.listdir(temp_dir)]
        
        # 分别处理文件夹和mcpack文件
        directories = [item for item in items if os.path.isdir(item)]
        mcpack_files = [item for item in items if item.lower().endswith('.mcpack')]
        
        # 处理mcpack文件
        for mcpack_file in mcpack_files:
            # 为每个mcpack文件创建一个子临时目录
            mcpack_name = os.path.basename(mcpack_file).replace('.mcpack', '')
            mcpack_temp_dir = os.path.join(temp_dir, f"mcpack_temp_{mcpack_name}")
            os.makedirs(mcpack_temp_dir, exist_ok=True)
            
            # 解压mcpack文件到子临时目录
            with zipfile.ZipFile(mcpack_file, 'r') as zip_ref:
                zip_ref.extractall(mcpack_temp_dir)
            
            # 查找manifest.json
            manifest_path = find_manifest_json_func(mcpack_temp_dir, max_depth=3)
            if manifest_path:
                # 解析manifest以确定包类型
                pack_info = parse_manifest_func(manifest_path)
                if pack_info:
                    # 确定源目录（manifest.json所在的目录）
                    source_dir = os.path.dirname(manifest_path)
                    
                    # 确定目标目录
                    if pack_info.type == 'behavior':
                        target_dir = os.path.join(behavior_folder, os.path.basename(source_dir))
                        imported_behavior += 1
                    else:  # resources
                        target_dir = os.path.join(resource_folder, os.path.basename(source_dir))
                        imported_resource += 1
                    
                    # 如果目标目录已存在，先删除它
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                    
                    # 复制到目标目录
                    shutil.copytree(source_dir, target_dir)
        
        # 处理文件夹
        # 如果只有一个文件夹，可能需要进一步检查里面的内容
        if len(directories) == 1 and not find_manifest_json_func(directories[0], max_depth=1):
            # 如果第一层只有一个文件夹且没有manifest.json，进入该文件夹查找子文件夹
            first_level_dir = directories[0]
            sub_items = [os.path.join(first_level_dir, item) for item in os.listdir(first_level_dir)]
            sub_directories = [item for item in sub_items if os.path.isdir(item)]
            sub_mcpack_files = [item for item in sub_items if item.lower().endswith('.mcpack')]
            
            # 更新处理列表
            directories = sub_directories
            
            # 处理嵌套的mcpack文件
            for mcpack_file in sub_mcpack_files:
                self._process_mcpack_file(mcpack_file, find_manifest_json_func, parse_manifest_func, 
                                         behavior_folder, resource_folder, temp_dir, imported_behavior, imported_resource)
        
        # 处理每个目录
        for directory in directories:
            # 查找manifest.json
            manifest_path = find_manifest_json_func(directory, max_depth=3)
            if manifest_path:
                # 解析manifest以确定包类型
                pack_info = parse_manifest_func(manifest_path)
                if pack_info:
                    # 确定源目录（manifest.json所在的目录）
                    source_dir = os.path.dirname(manifest_path)
                    
                    # 确定目标目录
                    if pack_info.type == 'behavior':
                        target_dir = os.path.join(behavior_folder, os.path.basename(source_dir))
                        imported_behavior += 1
                    else:  # resources
                        target_dir = os.path.join(resource_folder, os.path.basename(source_dir))
                        imported_resource += 1
                    
                    # 如果目标目录已存在，先删除它
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                    
                    # 复制到目标目录
                    shutil.copytree(source_dir, target_dir)
        
        # 清理临时目录
        self.clean_temp_dir()
        
        # 构建结果消息
        if imported_behavior > 0 or imported_resource > 0:
            message_parts = []
            if imported_behavior > 0:
                message_parts.append(f"导入了 {imported_behavior} 个行为包")
            if imported_resource > 0:
                message_parts.append(f"导入了 {imported_resource} 个资源包")
            message = "，".join(message_parts)
            return True, message
        else:
            return False, "在mcaddon文件中未找到有效的包"
    
    def _process_mcpack_file(self, mcpack_file, find_manifest_json_func, parse_manifest_func, 
                            behavior_folder, resource_folder, temp_dir, imported_behavior, imported_resource):
        """处理单个mcpack文件"""
        # 为mcpack文件创建子临时目录
        mcpack_name = os.path.basename(mcpack_file).replace('.mcpack', '')
        mcpack_temp_dir = os.path.join(temp_dir, f"mcpack_temp_{mcpack_name}")
        os.makedirs(mcpack_temp_dir, exist_ok=True)
        
        # 解压mcpack文件到子临时目录
        with zipfile.ZipFile(mcpack_file, 'r') as zip_ref:
            zip_ref.extractall(mcpack_temp_dir)
        
        # 查找manifest.json
        manifest_path = find_manifest_json_func(mcpack_temp_dir, max_depth=3)
        if manifest_path:
            # 解析manifest以确定包类型
            pack_info = parse_manifest_func(manifest_path)
            if pack_info:
                # 确定源目录（manifest.json所在的目录）
                source_dir = os.path.dirname(manifest_path)
                
                # 确定目标目录
                if pack_info.type == 'behavior':
                    target_dir = os.path.join(behavior_folder, os.path.basename(source_dir))
                    imported_behavior += 1
                else:  # resources
                    target_dir = os.path.join(resource_folder, os.path.basename(source_dir))
                    imported_resource += 1
                
                # 如果目标目录已存在，先删除它
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                
                # 复制到目标目录
                shutil.copytree(source_dir, target_dir)
