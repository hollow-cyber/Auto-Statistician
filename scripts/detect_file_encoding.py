"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import chardet


def detect_file_encoding(
		file_path: str,
) -> str:
	"""
	使用 cchardet 快速检测文件的编码方式

	Args:
		file_path: 文件完整路径

	Returns:
		str: 文件的编码方式
	"""
	with open(file_path, 'rb') as f:
		# 只读取前10000字节就足够了
		raw_data = f.read(10000)
	
	return chardet.detect(raw_data)['encoding']
