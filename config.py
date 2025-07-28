import os
from qfluentwidgets import qconfig, QConfig, OptionsConfigItem, OptionsValidator, Theme, RangeConfigItem, RangeValidator, setThemeColor, ColorValidator

class ThemeSerializer:
    """ Theme 序列化器 """
    
    @staticmethod
    def serialize(theme):
        return theme.value.lower()

    @staticmethod
    def deserialize(value: str):
        value = value.upper()
        return Theme[value]


class ColorSerializer:
    """ QColor 序列化器 """
    
    @staticmethod
    def serialize(color):
        return color.name()

    @staticmethod
    def deserialize(value: str):
        from PyQt6.QtGui import QColor
        return QColor(value)


class Config(QConfig):
    """ 应用配置 """
    
    # 主题模式配置项
    themeMode = OptionsConfigItem(
        "Appearance",
        "ThemeMode",
        Theme.AUTO,
        OptionsValidator([Theme.LIGHT, Theme.DARK, Theme.AUTO]),
        ThemeSerializer
    )

    # 主题色配置项
    themeColor = OptionsConfigItem(
        "Appearance",
        "ThemeColor",
        "#4ea654",
        ColorValidator("#4ea654"),
        ColorSerializer
    )

    # 复制数量配置项
    copyNumber = RangeConfigItem(
        "Config",
        "CopyNumber",
        10,  # 默认值为10
        RangeValidator(1, 100)
    )
    
    # App文件夹路径配置项
    appFolder = OptionsConfigItem(
        "Config",
        "AppFolder",
        "",  # 默认为空字符串
        None  # 不需要验证器
    )

def check_app_folder(cfg):
    """检查并创建app文件夹及其子文件夹"""
    config_changed = False
    
    # 获取app文件夹路径，如果配置中没有设置，则使用默认路径
    app_folder = cfg.appFolder.value
    
    # 如果路径为空，使用默认路径
    if not app_folder:
        # 默认在程序同目录下创建app文件夹
        app_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
        cfg.appFolder.value = app_folder
        config_changed = True
    
    # 尝试创建主文件夹（如果不存在）
    try:
        os.makedirs(app_folder, exist_ok=True)
    except Exception as e:
        print(f"创建主文件夹失败: {str(e)}")
        # 如果创建失败，尝试使用默认路径
        default_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
        
        # 如果当前路径已经是默认路径或默认路径也创建失败，则返回空路径
        if app_folder == default_folder:
            print("默认路径创建也失败，无法创建应用文件夹")
            return ""
        
        app_folder = default_folder
        cfg.appFolder.value = app_folder
        config_changed = True
        
        try:
            os.makedirs(app_folder, exist_ok=True)
        except Exception as e:
            print(f"创建默认文件夹也失败: {str(e)}")
            return ""  # 如果默认路径也创建失败，直接返回空字符串
    
    # 检查并创建必要的子文件夹
    sub_folders = ['Behavior_Packs', 'Resource_Packs', 'Addon', 'Temp']
    for folder in sub_folders:
        sub_folder_path = os.path.join(app_folder, folder)
        try:
            os.makedirs(sub_folder_path, exist_ok=True)
        except Exception as e:
            print(f"创建子文件夹 {folder} 失败: {str(e)}")
    
    # 如果配置有变化，保存到文件
    if config_changed:
        qconfig.save()
    
    return app_folder

# 创建配置实例
cfg = Config()

# 加载配置
qconfig.load('config.json', cfg)

# 检查并创建app文件夹
app_folder = check_app_folder(cfg)

# 设置主题色
setThemeColor(cfg.themeColor.value)
cfg.themeColor.valueChanged.connect(setThemeColor)