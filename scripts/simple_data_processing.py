"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import os
import time
import numpy as np
import pandas as pd
import streamlit as st
from typing import Literal

from scripts.set_st_custom_style import show_custom_toast
from scripts.convert_df_to_tsv import convert_df_to_tsv


def clear_st_data_processed() -> None:
	"""定义一个回调函数，用来清空计算结果，保证在重新选择执行的任务后需要重新点击计算按钮才出现结果"""
	st.session_state.pop('data_processed', None)
	
	
def get_original_precision(
		series: pd.Series,
) -> int:
	"""
	计算一个Pandas Series中数值的最大小数位数。

	Args:
		series: 输入的数据列。

	Returns:
		数据列中的最大小数位数。
	"""
	
	# 移除缺失值以进行计算
	series_non_null: pd.Series[int | float] = series.dropna()
	
	# 如果数据为空或者全部是整数，则精度为0
	if series_non_null.empty or (series_non_null.mod(1) == 0).all():
		return 0
	
	# 将数值转换为字符串，分离小数部分，并计算其长度
	decimal_precisions = series_non_null.astype(str).str.split('.').str[1].str.len()
	
	# 返回其中最大的长度作为精度
	return decimal_precisions.max()


def detect_nan(
		data: pd.DataFrame | np.ndarray,
) -> bool:
	"""检查数据集中是否有缺失值，并输出缺失值个数统计信息。

	Args:
		data: 输入的原始数据集，支持 pandas DataFrame 或 numpy ndarray。

	Returns:
		是否有缺失值。
	"""
	
	# 统一使用 pandas 方法处理
	if isinstance(data, pd.DataFrame):
		mask = data.isna()
		total_nan = mask.sum().sum()
		if total_nan:
			rows_with_nan = mask.any(axis=1).sum()
			cols_with_nan = mask.any(axis=0).sum()
			st.warning(
				f"⚠️ 程序检测到原始数据集中共有 {cols_with_nan} 列 {rows_with_nan} 行包含缺失值，共计 {int(total_nan)} 个缺失值。")
			return True
		else:
			return False
	else:
		# numpy 数组的情况
		arr = data
		try:
			mask = np.isnan(arr)
		except TypeError:
			st.error("❌ 程序无法处理该数据类型，请检查你传入的数据集及分隔符号。进行简单插补时")
			st.stop()
		
		total_nan = np.sum(mask)
		if total_nan:
			rows_with_nan = np.sum(np.any(mask, axis=1))
			cols_with_nan = np.sum(np.any(mask, axis=0))
			st.warning(
				f"⚠️ 程序检测到原始数据集中共有 {cols_with_nan} 列 {rows_with_nan} 行包含缺失值，共计 {total_nan} 个缺失值。")
			return True
		else:
			return False


def delete_nan(
		data: pd.DataFrame | np.ndarray,
		delete_type: Literal["col", "row"] = 'row',
) -> pd.DataFrame:
	"""
	使用布尔掩码删除含有缺失值的行或列
	
	Args:
		data: 输入的原始数据集，支持 pandas DataFrame 或 numpy ndarray。
		delete_type: 选择按行还是列删除缺失值数据。
		
	Returns:
		删除含有缺失值的行或列后的数据集
	"""
	
	if delete_type not in ['row', 'col']:
		raise ValueError(f"无效的删除类型参数：{delete_type}，delete_type应为 'row' 或 'col'")
	
	# 分数据类型及删除情况进行处理
	if isinstance(data, pd.DataFrame):
		if delete_type == 'row':
			clean_data = data.dropna()
			deleted_count = len(data) - len(clean_data)
			if deleted_count:
				show_custom_toast(f"程序已删除 {deleted_count} 条含空值的数据条，剩余 {len(clean_data)} 条。", icon="✅")
			else:
				show_custom_toast("程序未发现任何缺失值，不做处理。")
			return clean_data
		else:
			clean_data = data.dropna(axis=1)
			deleted_count = len(data.columns) - len(clean_data.columns)
			if deleted_count:
				show_custom_toast(f"程序已删除 {deleted_count} 列含空值的特征列，剩余 {len(clean_data.columns)} 列。",
				                  icon="✅")
			else:
				show_custom_toast("程序未发现任何缺失值，不做处理。")
			return clean_data
	else:
		arr = data
		mask = np.isnan(arr).any(axis=1 if delete_type == 'row' else 0)
		if delete_type == 'row':
			clean_data = arr[~mask]
			deleted_count = np.sum(mask)
			if deleted_count:
				show_custom_toast(f"程序已删除 {deleted_count} 条含空值的数据条，剩余 {len(clean_data)} 条。", icon="✅")
			else:
				show_custom_toast("程序未发现任何缺失值，不做处理。")
			return clean_data
		else:
			clean_data = arr[:, ~mask]
			deleted_count = np.sum(mask)
			if deleted_count:
				show_custom_toast(f"程序已删除 {deleted_count} 列含空值的特征列，剩余 {clean_data.shape[1]} 列。",
				                  icon="✅")
			else:
				show_custom_toast("程序未发现任何缺失值，不做处理。")
			return pd.DataFrame(clean_data)


def simple_impute_nan(
		data: pd.DataFrame,
		match_cols: list[str] | None = None,
		method: str = 'mean',
		**kwargs,
) -> pd.DataFrame:
	"""
	利用 pandas 分组进行简单缺失值插补
	
	Args:
		data: 原始数据集。
		match_cols: 需要按照分组进行插补的列。
		method: 缺失值插补方法。
		kwargs: 当method == 'constant'时，需要传入表示插补常数的constant_val参数。
		
	Returns:
		插补后的数据集。
	"""
	
	def apply_imputation(series, method, num_precision):
		"""应用插补方法到单个序列"""
		if method == 'mean':
			return series.fillna(round(series.mean(), num_precision))
		elif method == 'median':
			return series.fillna(round(series.median(), num_precision))
		elif method == 'mode':
			mode_val = series.mode()
			return series.fillna(mode_val[0] if not mode_val.empty else np.nan)
		elif method == 'random_choose':
			non_null = series.dropna()
			return series.fillna(np.random.choice(non_null) if not non_null.empty else np.nan)
		elif method == 'random':
			# noinspection PyTypeChecker
			return series.fillna(
				round(np.random.uniform(series.min(), np.nextafter(series.max(), np.inf)), num_precision))
		elif method == 'constant':
			if kwargs.get('constant_val') is None:
				# st.error(f"请输入用于填充缺失值的常数。")
				st.stop()
			return series.fillna(kwargs.get('constant_val'))
		else:
			# st.error(f"程序当前不支持该插补方法：{method}，请重新选择。")
			st.stop()
	
	# 获取含空值的列
	nan_cols = [c for c in data.columns if data[c].isna().any()]
	
	for col in nan_cols:
		try:
			# 获取该列的数字精度
			num_precision = get_original_precision(data[col])
		except TypeError:
			show_custom_toast("简单插补要求数据集中不能有非数字内容，请检查。", icon="❌")
			st.stop()
		
		# 根据是否分组来选择不同的插补方式
		if match_cols:
			group = data.groupby(match_cols)[col]
			data[col] = group.transform(lambda x: apply_imputation(x, method, num_precision))
		else:
			# 不进行分组，使用所有数据进行插补
			data[col] = apply_imputation(data[col], method, num_precision)
	
	return data


def st_impute_data(
		data: pd.DataFrame,
		file_name: str,
		file_extension: str = '.txt',
) -> pd.DataFrame:
	"""
	检测用户上传的原始数据集是否包含缺失值，并让用户选择是否进行简单处理。

	Args:
		data: 原始数据集。
		file_name: 数据文件名。
		file_extension: 拟输出的文件类型。

	Returns:
		处理后的数据集。
	"""
	
	if detect_nan(data):
		st.sidebar.divider()
		if st.sidebar.toggle('简单处理原数据集中的缺失值', on_change=clear_st_data_processed,
		                     help="处理时数据集中不能有非数字内容"):
			if "data_processed" not in st.session_state:
				st.session_state.data_processed = None
			
			func_dict = {
				'1': '删除数据集中有空值的数据条/列',
				'2': '按同类别样本特征数据进行简单缺失值插补',
			}
			processing_func = st.sidebar.radio('缺失值处理方式：', func_dict.values(), on_change=clear_st_data_processed)
			
			# 设置一些参数的默认值
			delete_type: Literal["col", "row"] = "row"
			match_cols = None
			impute_method_dict = {
				'均值填充': "mean",
				'中位数填充': 'median',
				'众数填充': 'mode',
				'在对应列随机选一特征值填充': 'random_choose',
				'在对应列特征值范围内使用随机数填充': 'random',
				'常数填充': 'constant',
			}
			impute_method = '均值填充'
			constant_val = 0
			
			if processing_func == func_dict['1']:
				delete_type = st.sidebar.radio('删除缺失值的方式：', ['删除行', '删除列'], horizontal=True,
				                               help="此方法用来删除缺失值所在的行/列，会大大降低数据利用度")
				delete_type = "row" if delete_type == '删除行' else "col"
			else:
				match_cols = st.sidebar.multiselect('需要按照哪些相同特征列进行缺失值插补：', options=data.columns,
				                                    help="对于每个缺失值，程序会找到缺失值数据条与你选择的列的值完全相同的所有行，并使用这些行的特征进行插补。如果不选择则表示使用该缺失值所在列有值的所有数据条。")
				if not match_cols:
					match_cols = None
				impute_method = st.sidebar.selectbox('缺失值插补方式：', impute_method_dict.keys())
				if impute_method == '常数填充':
					constant_val = st.sidebar.text_input('请输入用于填充缺失值的常数：', placeholder="如：3.1415")
					if not constant_val:
						st.stop()
					try:
						constant_val = float(constant_val)
					except ValueError:
						st.error("请输入正确的数字常数。")
						st.stop()
			
			cols = st.sidebar.columns([1, 1])
			with cols[0]:
				if processing_func == func_dict['1']:
					if st.button("开始删除"):
						st.session_state.data_processed = delete_nan(data, delete_type=delete_type)
				else:
					if st.button("开始插补"):
						st.session_state.data_processed = simple_impute_nan(data, match_cols,
						                                              impute_method_dict[impute_method],
						                                              constant_val=constant_val)
						show_custom_toast(f"程序已对原始数据集进行了{impute_method}简单缺失值处理。", icon="✅")
			with cols[1]:
				if st.session_state.data_processed is not None:
					if st.download_button(
							label="下载结果文件",
							data=convert_df_to_tsv(st.session_state.data_processed, file_extension=file_extension, hide_index=True),
							file_name=f"{os.path.splitext(file_name)[0]}-简单插补结果-{time.strftime("%Y-%m-%d %H:%M:%S")}{file_extension}",
							mime="text/plain",
							type="primary",
					):
						st.toast("简单插补结果文件下载成功！", icon="🎉")
					return st.session_state.data_processed
				else:
					# 没有计算插补结果时就暂停
					st.stop()
	
	return data


def detect_duplicate(
		data: pd.DataFrame,
		exclude_cols: list[str] | None = None,
		keep_mode: Literal["first", "last", False] = 'first',
) -> pd.DataFrame:
	"""
	检测并删除重复数据。

	Args:
		data: 输入的原始数据集。
		exclude_cols: 需要排除的列索引列表（即：这些列的内容不参与重复判断）。
		keep_mode: keep='first' 保留第一次出现的，keep='last' 保留最后一次，keep=False 删除所有重复行。
		
	Returns:
		清理后的数据集。
	"""
	
	# 获取参与判断的列名（总列数 - 排除的列）
	subset_cols = [c for c in list(data.columns) if c not in (exclude_cols or [])]
	
	# 使用data.duplicated方法查找重复项
	duplicated_mask = data.duplicated(subset=subset_cols, keep=keep_mode)
	# 获取不重复的数据
	clean_data = data[~duplicated_mask]
	
	count = duplicated_mask.sum()
	if count:
		st.success(f"程序检测到 {count} 条重复数据，已成功删除。")
	else:
		st.info("程序未检测到任何重复数据条。")
	
	return clean_data
