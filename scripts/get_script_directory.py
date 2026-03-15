"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import os
import sys


def get_script_directory() -> str:
	"""
	获取当前 Python 脚本文件所在的目录。在封装成可执行文件时仍然有效。

	Returns:
		脚本文件所在目录的绝对路径。
	"""
	# 获取当前脚本文件所在路径
	if getattr(sys, 'frozen', False):  # 检测是否为打包后的可执行文件
		script_dir = os.path.dirname(sys.executable)  # 可执行文件所在目录
	else:
		script_dir = os.path.dirname(os.path.abspath(__file__))  # 脚本文件所在目录
	
	# print(f"当前脚本所在路径为: {script_dir}")
	
	return script_dir
