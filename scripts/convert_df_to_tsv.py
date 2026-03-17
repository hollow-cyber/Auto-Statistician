"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import io
import pandas as pd


def convert_df_to_tsv(
		df: pd.DataFrame,
		file_extension: str = '.txt',
		hide_header: bool = False,
		hide_index: bool = True,
		encoding: str = 'utf-8'
) -> str:
	"""
	将DataFrame转换为制表符分隔的字符串，方便使用st.download_button下载

	Args:
		df: 存放数据结果的DataFrame
		file_extension: 拟输出的文件类型，用来选择.to_csv的sep参数值
		hide_header: 是否不输出列名
		hide_index: 是否不输出行名
		encoding: 文件编码格式

	Returns:
		tsv结果
	"""
	
	# 使用StringIO创建内存中的文件对象
	output = io.StringIO()
	# 将DataFrame写入到内存中的文件对象，使用制表符分隔
	separator = ',' if file_extension == '.csv' else '\t'
	df.to_csv(output, sep=separator, header=not hide_header, index=not hide_index, encoding=encoding)
	# 获取字符串内容
	return output.getvalue()