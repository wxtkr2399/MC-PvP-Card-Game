import logging
import os
from logging.handlers import RotatingFileHandler

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 日志文件路径
log_file = os.path.join(log_dir, 'game.log')

# 创建日志器
logger = logging.getLogger('MP2Game')
logger.setLevel(logging.DEBUG)

# 定义日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARN)
console_handler.setFormatter(formatter)

# 文件处理器 (支持日志轮转)
file_handler = RotatingFileHandler(
    log_file,
    mode='w',
    maxBytes=1024 * 1024 * 5,  # 5MB
    backupCount=0,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 添加处理器到日志器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def log_clear():
    """
    清空日志文件
    """
    with open(log_file, 'w') as f:
        f.truncate()

# 导出供其他模块使用
__all__ = ['logger', 'log_clear']
