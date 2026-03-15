"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import io
import pandas as pd


def convert_df_to_tsv(
		df: pd.DataFrame,
		separator: str = '\t',
		hide_header: bool = False,
		hide_index: bool = True,
		encoding: str = 'utf-8'
) -> str:
	"""
	将DataFrame转换为制表符分隔的字符串，方便使用st.download_button下载

	Args:
		df: 存放数据结果的DataFrame
		separator: 分隔符号
		hide_header: 是否不输出列名
		hide_index: 是否不输出行名
		encoding: 文件编码格式

	Returns:
		tsv结果
	"""
	
	# 使用StringIO创建内存中的文件对象
	output = io.StringIO()
	# 将DataFrame写入到内存中的文件对象，使用制表符分隔
	df.to_csv(output, sep=separator, header=not hide_header, index=not hide_index, encoding=encoding)
	# 获取字符串内容
	return output.getvalue()