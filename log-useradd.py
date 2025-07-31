# -*- coding: utf-8 -*-
# @Time    : 2025/7/31 15:42
# @Author  : zhangdawei
# @Version : Python 3.13
# @File    : log-useradd.py
# @Software: PyCharm

import os
import json
import hashlib
import logging
from logging.handlers import RotatingFileHandler

# --- 日志配置 ---
LOG_FILE = 'dangan.log'  # 日志文件名
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5  # 保留5个备份

def setup_logging():
    """
    配置日志系统
    """
    # 创建一个logger
    logger = logging.getLogger('UserManagementSystem')
    logger.setLevel(logging.DEBUG)  # 记录所有级别的日志

    # 防止重复添加处理器（在模块被多次导入时很重要）
    if logger.handlers:
        return logger

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )

    # 1. 控制台处理器 (输出 INFO 及以上级别)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 文件处理器 (带轮转，输出所有级别到文件)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'  # 确保能记录中文
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"日志文件处理器已初始化，日志将保存到: {LOG_FILE}")
    except Exception as e:
        # 如果文件创建失败，至少确保控制台能输出错误
        console_handler.setLevel(logging.ERROR)
        logger.error(f"无法创建日志文件 '{LOG_FILE}': {e}")

    return logger

# 全局日志记录器
logger = setup_logging()

# --- 常量 ---
DATA_FILE = 'data.json'
SALT = 'a zhangdaweiok!!!'  # 加盐字符串

# --- 密码加密 (加盐 MD5) ---
def user_md5_password(password):
    """
    对密码进行加盐 MD5 哈希
    Args:
        password (str): 明文密码
    Returns:
        str: MD5 哈希值 (十六进制字符串)
    """
    try:
        md5_obj = hashlib.md5()
        # 将密码和盐拼接后进行哈希
        md5_obj.update((password + SALT).encode('utf-8'))
        return md5_obj.hexdigest()
    except Exception as e:
        logger.error(f"密码哈希计算失败: {e}")
        raise  # 重新抛出异常，让调用者知道出了问题

# --- 文件哈希计算 (用于完整性校验 - 采样法) ---
def get_file_md5(filepath):
    """
    计算文件的 MD5 哈希值 (使用采样法)
    Args:
        filepath (str): 文件路径
    Returns:
        str or None: MD5 哈希值 (十六进制字符串) 或 None (如果文件不存在或出错)
    """
    # 1. 检查文件是否存在
    if not os.path.exists(filepath):
        logger.warning(f"文件 '{filepath}' 不存在，无法计算哈希。")
        return None

    try:
        file_size = os.path.getsize(filepath)
        # 定义四个采样点的偏移量
        offset1 = 0
        offset2 = file_size // 3
        offset3 = (file_size // 3) * 2
        offset4 = max(0, file_size - 10)  # 确保非负

        offsets = [offset1, offset2, offset3, offset4]
        md5_obj = hashlib.md5()

        with open(filepath, 'rb') as f:
            for offset in offsets:
                f.seek(offset)
                bytes_to_read = min(10, file_size - offset)
                chunk = f.read(bytes_to_read)
                md5_obj.update(chunk)

        hash_value = md5_obj.hexdigest()
        logger.debug(f"文件 '{filepath}' 的 MD5 哈希值计算完成: {hash_value}")
        return hash_value

    except Exception as e:
        logger.error(f"计算文件 '{filepath}' 的 MD5 哈希值时发生错误: {e}")
        return None

# --- 数据读取 ---
def load_json_file(filename):
    """
    从 JSON 文件加载用户数据
    Args:
        filename (str): JSON 文件名
    Returns:
        dict: 用户数据字典 或 空字典 (如果失败)
    """
    logger.info(f"尝试加载用户数据文件: {filename}")

    # 1. 检查文件是否存在
    if not os.path.exists(filename):
        logger.warning(f"用户数据文件 '{filename}' 不存在。")
        return {}

    # 2. 进行文件完整性校验
    current_hash = get_file_md5(filename)
    if current_hash is None:
        logger.error(f"无法校验当前文件 '{filename}' 的完整性，请检查该文件是否正常或权限！")
        return {}

    # 3. 如果都正常，读取并解析 JSON
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"成功加载用户数据文件 '{filename}'，包含 {len(data)} 个用户。")

        # 4. 检查数据类型
        if isinstance(data, dict):
            return data
        else:
            logger.warning(f"文件 '{filename}' 中的数据不是字典类型，实际类型: {type(data).__name__}。返回空字典。")
            return {}

    except json.JSONDecodeError as e:
        logger.error(f"解析 JSON 文件 '{filename}' 时发生语法错误: {e}")
        return {}
    except PermissionError as e:
        logger.error(f"没有权限读取文件 '{filename}': {e}")
        return {}
    except Exception as e:
        logger.error(f"读取文件 '{filename}' 时发生未知错误: {e}")
        return {}

# --- 数据保存 ---
def save_json_file(data, filename):
    """
    将用户数据保存到 JSON 文件
    Args:
        data (dict): 要保存的用户数据
        filename (str): JSON 文件名
    Returns:
        bool: 保存是否成功
    """
    logger.info(f"尝试保存用户数据到文件: {filename}，共 {len(data)} 个用户。")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"用户数据成功保存到文件 '{filename}'。")
        # 保存后，重新计算并记录文件哈希（可选，用于后续校验）
        new_hash = get_file_md5(filename)
        if new_hash:
            logger.debug(f"保存后文件 '{filename}' 的 MD5 哈希值: {new_hash}")
        return True

    except PermissionError as e:
        logger.error(f"没有权限写入文件 '{filename}': {e}")
    except OSError as e:
        logger.error(f"写入文件 '{filename}' 时发生 I/O 错误: {e}")
    except Exception as e:
        logger.error(f"保存文件 '{filename}' 时发生未知错误: {e}")

    return False

# --- 用户注册 ---
def add_user_info():
    """
    添加新用户信息
    """
    logger.info("用户注册流程开始。")
    print('\n' + '=' * 40)
    print(' 用 户 注 册')
    print('=' * 40)

    # 用户名
    while True:
        username = input('请输入您的用户名: ').strip()
        if not username:
            print('用户名不能为空，请重新输入！')
            continue

        # 加载现有用户数据，以便检查用户名
        existing_data = load_json_file(DATA_FILE)
        if username in existing_data:
            print(f'您输入的当前用户名 {username} 已存在，请更换用户名！')
            logger.warning(f"用户注册失败: 用户名 '{username}' 已存在。")
            continue
        else:
            break

    # 密码
    while True:
        password = input('请输入您的密码: ').strip()
        if not password:
            print('密码不能为空，请重新输入！')
            continue
        re_password = input('请确认您的密码: ').strip()
        if re_password != password:
            print('您输入的两次密码不一致，请重新输入！')
            continue
        else:
            break

    # 获取性别
    while True:
        sex = input('请输入您的性别 (nan 或 nv): ').strip()
        if sex not in ['nan', 'nv']:
            print("您输入的性别有误，请输入 'nan' 或 'nv'！")
            continue
        else:
            break

    # 把用户输入的信息保存
    new_user = {
        "password": user_md5_password(password),
        "sex": sex
    }

    # 添加新用户到数据字典
    existing_data[username] = new_user

    # 保存数据到 JSON 文件
    if save_json_file(existing_data, DATA_FILE):
        print(f'用户 {username} 注册成功！')
        logger.info(f"用户 '{username}' 注册成功。")
    else:
        print(f'用户 {username} 注册失败！数据保存失败。')
        logger.error(f"用户 '{username}' 注册失败: 数据保存失败。")

# --- 用户登录 ---
def login():
    """
    用户登录
    """
    logger.info("用户登录流程开始。")
    print('\n' + '='*40)
    print('用 户 登 录')
    print('='*40)

    while True:
        username = input('请输入您的用户名: ').strip()
        if not username:
            print('用户名不能为空，请输入！')
            continue

        # 加载用户数据
        existing_data = load_json_file(DATA_FILE)

        # 检查用户名
        if username not in existing_data:
            print(f'您输入的用户名 {username} 不存在，请重新输入!')
            logger.warning(f"用户登录失败: 用户名 '{username}' 不存在。")
            continue
        else:
            # 用户名存在，输入密码
            password = input('请输入您的密码: ').strip()
            if not password:
                print('密码不能为空，请输入您的密码！')
                continue

            # 获取存储的哈希值
            stored_hash = existing_data[username]['password']
            # 计算输入密码的哈希值
            input_hash = user_md5_password(password)

            # 对比哈希值
            if input_hash == stored_hash:
                print(f'当前用户 {username} 登录成功！')
                logger.info(f"用户 '{username}' 登录成功。")
                break
            else:
                print(f'您输入的当前用户 {username} 密码错误，请重新登录！')
                logger.warning(f"用户 '{username}' 登录失败: 密码错误。")
                continue

# --- 主程序 ---
def main():
    """
    主程序循环
    """
    logger.info("用户管理系统启动。")
    print('\n' + '='*45)
    print('欢迎使用用户管理系统')
    print('='*45)

    try:
        while True:
            print('  1. 注册新用户')
            print('  2. 用户登录')
            print('  3. 退出系统')
            print('='*45)

            choice = input('  请选择功能 (1/2/3): ').strip()

            if choice == '1':
                add_user_info()
            elif choice == '2':
                login()
            elif choice == '3':
                print('感谢使用，再见！')
                logger.info("用户管理系统正常退出。")
                break
            else:
                print('无效选择，请输入 1, 2 或 3。')
                logger.warning(f"无效的菜单选择: '{choice}'")

    except KeyboardInterrupt:
        # 捕获 Ctrl+C
        print('\n\n程序被用户中断。')
        logger.info("用户管理系统被用户中断 (Ctrl+C) 退出。")
    except Exception as e:
        # 捕获其他未预期的异常
        print(f'\n程序发生严重错误: {e}')
        logger.critical(f"用户管理系统发生未预期的严重错误: {e}", exc_info=True) # exc_info=True 会记录完整的堆栈跟踪

# --- 程序入口 ---
if __name__ == "__main__":
    main()













