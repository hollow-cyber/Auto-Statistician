"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder


def is_categorical_column(
		series: pd.Series,
		min_categories: int = 2,
		max_categories: int = 10
) -> bool:
	"""
	判断一个Pandas Series是否是分类变量

	Args:
		series : 要判断的数据列
		min_categories: 最小类别数(默认为2)
		max_categories: 最大类别数(默认为10)

	Returns:
		是否是分类变量
	"""
	# 排除缺失值
	non_null = series.dropna()
	
	if len(non_null) == 0:
		return False
	
	# 检查数据类型
	is_numeric = pd.api.types.is_numeric_dtype(non_null)
	is_string = non_null.apply(lambda x: isinstance(x, str)).any()
	
	# 基本统计信息
	n_unique = non_null.nunique()
	
	# 情况1: 已经是数值类型
	if is_numeric:
		# 检查所有值是否为整数
		if not all(isinstance(x, (int, np.integer)) or (isinstance(x, float) and x.is_integer()) for x in non_null):
			return False
		
		# 检查值范围是否在给定变化范围之间
		# if non_null.min() < 0 or non_null.max() > max_categories:
		# 	return False
		
		# 检查唯一值数量是否在合理范围内
		if n_unique < min_categories or n_unique > max_categories:
			return False
	
	# 情况2: 包含字符串类型
	elif is_string:
		# 检查唯一值数量
		if n_unique < min_categories or n_unique > max_categories:
			return False
		
		# 使用LabelEncoder进行编码
		le = LabelEncoder()
		encoded_values = le.fit_transform(non_null)
		encoded_series = pd.Series(encoded_values, index=non_null.index)
		
		# 编码后再像数字分类变量一样做一遍检查
		encoded_n_unique = encoded_series.nunique()
		if not all(
				isinstance(x, (int, np.integer)) or (isinstance(x, float) and x.is_integer()) for x in encoded_series):
			return False
		if encoded_n_unique < min_categories or encoded_n_unique > max_categories:
			return False
	
	# 情况3: 其他类型（如布尔、日期等）
	else:
		# 对于布尔类型，也认为是分类变量
		if n_unique <= 2 and set(non_null.unique()).issubset({True, False, 0, 1, 'True', 'False', 'Yes', 'No'}):
			return True
		
		return False
	
	return True


def identify_categorical_columns(
		df: pd.DataFrame,
		min_categories: int = 2,
		max_categories: int = 10
) -> list:
	"""
	识别DataFrame中的分类变量

	Args:
		df: 输入数据
		min_categories: 最小类别数
		max_categories: 最大类别数

	Return:
		分类变量名列表
	"""
	categorical_cols = []
	
	for col in df.columns:
		if is_categorical_column(df[col], min_categories, max_categories):
			categorical_cols.append(col)
	
	return categorical_cols
