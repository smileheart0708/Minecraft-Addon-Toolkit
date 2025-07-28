from PyQt6.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition

DEFAULT_DURATION = 5000 # 默认显示时间为5秒，符合项目要求

def show_message_bar(title: str, content: str, bar_type: str = 'info', duration: int = DEFAULT_DURATION, parent=None, position: InfoBarPosition = InfoBarPosition.TOP):
    """
    显示一个消息条。

    :param title: 消息条标题
    :param content: 消息条内容
    :param bar_type: 消息条类型 ('info', 'success', 'warning', 'error')
    :param duration: 显示时长 (毫秒)
    :param parent: 父组件
    :param position: 消息条位置
    """
    if bar_type == 'success':
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=position,
            duration=duration,
            parent=parent
        )
    elif bar_type == 'warning':
        InfoBar.warning(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=position,
            duration=duration,
            parent=parent
        )
    elif bar_type == 'error':
        InfoBar.error(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=position,
            duration=duration,
            parent=parent
        )
    else: # 默认为 'info'
        InfoBar.info(
            title=title,
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=position,
            duration=duration,
            parent=parent
        )