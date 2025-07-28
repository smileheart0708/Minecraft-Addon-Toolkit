import os
import datetime

# 确定项目根目录，以便将logs目录创建在根目录下
# __file__ -> services/log_service.py
# os.path.dirname(__file__) -> services
# os.path.dirname(os.path.dirname(__file__)) -> project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')

def log_error(message: str):
    """
    将错误信息记录到当天的日志文件中。

    日志文件将保存在项目根目录下的 'logs' 文件夹中。
    文件名格式为 YYYY-MM-DD.log。
    每条日志记录都会带有 HH-MM-SS 格式的时间戳。

    Args:
        message (str): 需要记录的错误信息。
    """
    try:
        # 确保日志目录存在
        os.makedirs(LOG_DIR, exist_ok=True)

        # 获取当前日期和时间
        now = datetime.datetime.now()
        log_filename = now.strftime('%Y-%m-%d') + '.log'
        log_filepath = os.path.join(LOG_DIR, log_filename)

        # 格式化日志消息
        timestamp = now.strftime('[%H-%M-%S]')
        formatted_message = f"{timestamp} {message}\n"

        # 以追加模式写入文件
        with open(log_filepath, 'a', encoding='utf-8') as f:
            f.write(formatted_message)
    except Exception as e:
        # 如果日志记录本身失败，则在控制台打印错误，以防信息丢失
        print(f"写入日志文件失败: {e}")
        print(f"原始错误信息: {message}")
