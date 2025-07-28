from qfluentwidgets import MessageBox


def show_confirm_dialog(title: str, content: str, parent=None, closable_on_mask: bool = True, confirm_text: str = '确认', cancel_text: str = '取消') -> bool:
    """
    显示一个带遮罩的确认对话框。

    :param title: 对话框标题
    :param content: 对话框内容
    :param parent: 父组件
    :param closable_on_mask: 点击遮罩是否关闭对话框
    :param confirm_text: 确认按钮文本
    :param cancel_text: 取消按钮文本
    :return: 用户是否点击了"确认"按钮（True为确认，False为取消）
    """
    dialog = MessageBox(title, content, parent)
    dialog.setClosableOnMaskClicked(closable_on_mask)
    dialog.yesButton.setText(confirm_text)
    dialog.cancelButton.setText(cancel_text)
    return bool(dialog.exec())
