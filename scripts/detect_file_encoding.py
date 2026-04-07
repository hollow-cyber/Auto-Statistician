"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import chardet


def detect_file_encoding(
		file_path: str,
) -> str:
	"""
	使用 chardet 检测文件的编码方式

	Args:
		file_path: 文件完整路径

	Returns:
		str: 文件的编码方式
	"""
	with open(file_path, 'rb') as f:
		# 读取更多字节以提高检测准确性，有利于检测大文件的编码
		raw_data = f.read(100000)
	
	result = chardet.detect(raw_data)
	encoding = result['encoding']
	confidence = result.get('confidence', 0)
	
	if encoding:
		# ASCII 是 UTF-8 的子集，统一返回 utf-8
		if encoding.lower() == 'ascii':
			return 'utf-8'
		# 如果置信度较高，直接返回检测结果
		if confidence > 0.7:
			return encoding
		# 置信度较低时，优先使用 utf-8
		return 'utf-8'
	else:
		return 'utf-8'

