"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import pandas as pd
import numpy as np
import streamlit as st
from scipy import stats

from scripts.do_chi2_test import calculate_category_proportions, auto_chi2_test
from scripts.process_p_value import process_p_value


# 这里使用装饰器，让用户仅改变格式参数的时候不会重复进行统计分析计算
@st.cache_data
def auto_statistical_analysis_and_summary(
		X: pd.DataFrame,
		y: pd.Series,
		categorical_vars: list,
		normal_dis_vars: list,
		cal_column_pct: bool
) -> dict[str, list]:
	"""
	自动根据自变量和因变量类型执行相应的统计分析，同时计算描述性统计量

	Args:
		X: 包含自变量的数据集
		y: 包含因变量的数据集
		categorical_vars: 分类变量的列名
		normal_dis_vars): 正太分布变量的列名
		cal_column_pct: 按列还是按行计算百分比

	Returns:
		未格式化的描述性和统计分析结果
		存放每个变量对应的统计分析结果，字典的key为变量名，value为存储描述性和统计分析结果的列表。
		对于离散型变量：value列表前2个元素为描述性结果的DataFrame，
		DataFrame的行名是各类别，列名是因变量各类，第1个DataFrame是列联表，第2个是百分比，列表最后一个元素为p值。
		对于正态分布变量：value列表存着一个字典和p值，字典的key是因变量类别名，value是保存的对应平均值和标准差的list。
		对于正态分布变量：value列表存着一个字典和p值，字典的key是因变量类别名，value是保存的对应q25, median, q75的list。
	"""
	# 确保 y 没有任何缺失值
	# 如果 y 有缺失，对应的 X 里的行也必须剔除，否则后续 y.unique() 会包含 nan
	mask = y.notna()
	X_clean = X[mask]
	y_clean = y[mask]
	# 提前获取 y 的唯一值类别，并排序，保证表格列顺序固定
	y_categories = sorted(y_clean.unique())
	
	# 存放所有自变量分析结果的字典
	statistical_results_dict = {}
	
	# 遍历协变量并进行统计分析
	for col in X.columns:
		# 存放单个变量的统计分析结果，先存描述性结果，然后是p值
		result = []
		
		if col in categorical_vars:
			# 将数据转换成列联表
			# pd.crosstab 默认会排除X[col]或y中任何一个为NaN的行
			contingency_table = pd.crosstab(X_clean[col], y_clean)
			var_result = calculate_category_proportions(contingency_table, cal_column_pct=cal_column_pct)
			chi2_result = auto_chi2_test(contingency_table)
			
			# 依次记录结果，并最终存入statistical_results_dict中
			result.extend([contingency_table, var_result, chi2_result['final_p_value']])
			statistical_results_dict[col] = result
		
		else:
			# 提取连续变量数据时直接 dropna
			# 这样保证了 group_data 里的每个 Series 都是纯净的数值
			group_data = [X_clean[col][y_clean == cat].dropna() for cat in y_categories]
			
			# 根据正态性执行统计检验并计算描述性统计
			if y.nunique() == 2:
				# 连续 vs. 二分类
				
				# 检查是否有组变成了空的（比如某组年龄全缺失）
				if any(len(g) == 0 for g in group_data):
					statistical_results_dict[col] = [{}, np.nan]
					continue
				
				if col in normal_dis_vars:
					# 执行独立样本 t 检验
					t_stat, p_value = stats.ttest_ind(group_data[0], group_data[1], equal_var=False)
					# 这里存的value是每一个结局分组的描述性结果子列表
					result_dict = {cat: [g.mean(), g.std()] for cat, g in zip(y_categories, group_data)}
				else:
					# 执行Mann-Whitney U 检验，添加 nan_policy='omit' 来排除缺失值
					u_stat, p_value = stats.mannwhitneyu(group_data[0], group_data[1])
					result_dict = {cat: [g.quantile(0.25), g.median(), g.quantile(0.75)] for cat, g in
					               zip(y_categories, group_data)}
			
			else:
				# 连续 vs. 多分类
				if col in normal_dis_vars:
					# 单因素方差分析
					f_stat, p_value = stats.f_oneway(*group_data)
					result_dict = {cat: [g.mean(), g.std()] for cat, g in zip(y_categories, group_data)}
				else:
					# 克鲁斯卡尔 - 沃利斯H检验
					h_stat, p_value = stats.kruskal(*group_data)
					result_dict = {cat: [g.quantile(0.25), g.median(), g.quantile(0.75)] for cat, g in
					               zip(y_categories, group_data)}
			
			result.extend([result_dict, p_value])
			statistical_results_dict[col] = result
	
	# st.success("自动统计分析和描述性统计结束。")
	return statistical_results_dict


def format_statistical_results(
		X: pd.DataFrame,
		y: pd.Series,
		categorical_vars: list,
		normal_dis_vars: list,
		cal_column_pct: bool,
		chi2_result_connector: str | None,
		mean_std_connector: str | None,
		quartiles_connector: str | None,
		add_connector: bool,
		add_overall: bool,
		decimal_places: int,
		p_decimal_places: int,
		if_category_space: bool,
		if_simple_p_format: bool,
		if_star_symbol: bool
) -> pd.DataFrame:
	"""
	根据用户的设置格式化描述性和统计分析结果

	Args:
		X: 原始自变量数据集，用于计算缺失值
		y: 因变量列
		categorical_vars: 分类自变量列名
		normal_dis_vars: 正态分布自变量列名
		cal_column_pct: 按列还是按行计算百分比
		chi2_result_connector: 卡方检验描述性结果输出格式
		mean_std_connector: 平均值和标准差描述性结果输出格式
		quartiles_connector: 四分位数描述性结果输出格式
		add_connector: 是否在变量的后面添加对应的数据描述性结果书写格式
		add_overall: 是否第2列添加整体数据（不分组）的描述性结果
		decimal_places: 描述性结果精确位数
		p_decimal_places: p值结果精确位数
		if_category_space: 是否在分类变量各类别名称前加2个空格
		if_simple_p_format: 是否去掉P值小数点前面的0
		if_star_symbol: 是否在不同显著性P值结果后面添加对应数量的*号

	Returns:
		格式化后的描述性和统计分析结果
	"""
	
	# 进行单因素统计分析
	statistical_results_dict = auto_statistical_analysis_and_summary(X, y, categorical_vars, normal_dis_vars,
	                                                                 cal_column_pct)
	
	# 定义初始的规范化表述格式字符串
	chi2_result_connector_f = "{N:.0f}({percent:.{decimal_places}f}%)"
	mean_std_connector_f = "{mean:.{decimal_places}f}±{std:.{decimal_places}f}"
	quartiles_connector_f = "{Q1:.{decimal_places}f}({Q2:.{decimal_places}f}, {Q3:.{decimal_places}f})"
	
	# 预先计算好列名映射 (只做一次)
	# 计算因变量每类的数量，注意这里的cat是y的各类别，不是分类变量的各类别
	value_counts = y.value_counts()
	col_map = {cat: f"{cat}(N={count})" for cat, count in value_counts.items()}
	# 设定总体描述性结果列
	overall_col = f'Overall (N={y.count()})' if add_overall else ''
	
	# 对各种变量对应的描述性结果字符串进行格式化
	if chi2_result_connector:
		if 'percent' in chi2_result_connector:
			# 将N和percent括起来，并生成格式化字符串，注意percent后面加了%
			chi2_result_connector_f = chi2_result_connector.replace('N', '{N:.0f}').replace('percent',
			                                                                                '{percent:.{decimal_places}f}%')
		elif 'ratio' in chi2_result_connector:
			# 将N和ratio括起来，并生成两个格式化字符串
			chi2_result_connector_f = chi2_result_connector.replace('N', '{N:.0f}').replace('ratio',
			                                                                                '{ratio:.{decimal_places}f}')
	if mean_std_connector:
		mean_std_connector_f = mean_std_connector.replace('mean', '{mean:.{decimal_places}f}').replace('std',
		                                                                                               '{std:.{decimal_places}f}')
	if quartiles_connector:
		quartiles_connector_f = quartiles_connector.replace('Q1', '{Q1:.{decimal_places}f}').replace('Q2',
		                                                                                             '{Q2:.{decimal_places}f}').replace(
			'Q3', '{Q3:.{decimal_places}f}')
	
	# 存储结果表每行数据的列表，最后会转为DataFrame
	table_rows = []
	
	for var in statistical_results_dict.keys():
		# 计算当前变量的缺失值信息
		missing_count = X[var].isnull().sum()
		total_count = len(X[var])
		# 格式化为 "Count (Percent%)"
		missing_string = f"{missing_count} ({missing_count / total_count:.{decimal_places}%})"
		# 提取该变量列非空数据
		overall_series = X[var].dropna()
		
		if var in categorical_vars:
			# 准备可能需要的变量数据整体描述性结果
			# 计算各类别的频数 (Count) 和 频率 (Percentage)
			counts = overall_series.value_counts(sort=False)  # 保持原始顺序或按数值排序
			# 注意这里不是除以len(X[var])
			ratios = (counts / len(overall_series))
			
			# 使用列表先写分类变量开头首行，由于var可能是int列数，所以记录时都转换为str
			var_string = f"{var}, {chi2_result_connector}" if add_connector else f"{var}"
			# 格式化p值结果
			p_value_str = process_p_value(statistical_results_dict[var][-1], p_decimal_places, if_simple_p_format, if_star_symbol)
			
			data_dict = {
				'Variable': var_string,
				overall_col: '',
				**{col_map[cat]: '' for cat in col_map.keys()},  # 动态解包组别，此时这里全部添加空字符串
				'P-Value': p_value_str,
				'Missing (N (%))': missing_string
			}
			table_rows.append(data_dict)
			
			# 逐行添加statistical_results_dict[var]中的前2个df各元素到data_dict中
			for idx in statistical_results_dict[var][0].index:
				# 准备该分类变量的整体数据描述性结果字符串
				overall_string = ''
				if add_overall:
					if 'percent' in chi2_result_connector:
						overall_string = chi2_result_connector_f.format(
							N=counts[idx],
							percent=ratios[idx] * 100,
							decimal_places=decimal_places
						)
					elif 'ratio' in chi2_result_connector:
						overall_string = chi2_result_connector_f.format(
							N=counts[idx],
							percent=ratios[idx],
							decimal_places=decimal_places
						)
				
				# 准备该分类变量各类别的描述性结果字符串
				value_groups = {}
				for cat in statistical_results_dict[var][0].columns:
					if 'percent' in chi2_result_connector:
						# 对两个df对应位置元素进行格式化字符串连接处理
						value_string = chi2_result_connector_f.format(
							N=statistical_results_dict[var][0].loc[idx, cat],
							percent=statistical_results_dict[var][1].loc[idx, cat],
							decimal_places=decimal_places)
					elif 'ratio' in chi2_result_connector:
						value_string = chi2_result_connector_f.format(
							N=statistical_results_dict[var][0].loc[idx, cat],
							ratio=statistical_results_dict[var][1].loc[idx, cat] / 100,
							decimal_places=decimal_places)
					else:
						value_string = ''
					value_groups[cat] = value_string
				
				# 挨个存入dict中，此时不存入P值和缺失值统计信息
				data_dict = {
					'Variable': '  ' + f'{idx}' if if_category_space else f'{idx}',
					overall_col: overall_string,
					**{col_map[cat]: string for cat, string in value_groups.items()},  # 动态解包组别
					'P-Value': '',
					'Missing (N (%))': ''
				}
				table_rows.append(data_dict)
		
		else:
			# 对于连续型变量，P值和缺失值可以在下面这个if分支之后再加
			if var in normal_dis_vars:
				# 准备可能需要的变量数据整体描述性结果
				overall_mean, overall_std = overall_series.mean(), overall_series.std()
				
				# 自动判断变量的表示需不需要加上数据书写方式
				var_string = f"{var}, {mean_std_connector}" if add_connector else f"{var}"
				
				overall_string = ''
				if add_overall:
					overall_string = mean_std_connector_f.format(
						mean=overall_mean,
						std=overall_std,
						decimal_places=decimal_places
					)
				
				value_groups = {}
				# 提取记录统计结果的字典
				cat_dict = statistical_results_dict[var][0]
				for cat, value_list in cat_dict.items():
					value_string = mean_std_connector_f.format(
						mean=value_list[0],
						std=value_list[1],
						decimal_places=decimal_places
					)
					value_groups[cat] = value_string
			
			else:
				# 准备可能需要的变量数据整体描述性结果
				overall_q25, overall_median, overall_q75 = np.nanpercentile(overall_series, [25, 50, 75])
				
				var_string = f"{var}, {quartiles_connector}" if add_connector else f"{var}"
				
				overall_string = ''
				if add_overall:
					overall_string = quartiles_connector_f.format(
						Q1=overall_q25,
						Q2=overall_median,
						Q3=overall_q75,
						decimal_places=decimal_places
					)
				
				value_groups = {}
				cat_dict = statistical_results_dict[var][0]
				for cat, value_list in cat_dict.items():
					value_string = quartiles_connector_f.format(
						Q1=value_list[0],
						Q2=value_list[1],
						Q3=value_list[2],
						decimal_places=decimal_places
					)
					value_groups[cat] = value_string
			
			p_value_str = process_p_value(statistical_results_dict[var][-1], p_decimal_places, if_simple_p_format, if_star_symbol)
			data_dict = {
				'Variable': var_string,
				overall_col: overall_string,
				**{col_map[cat]: string for cat, string in value_groups.items()},  # 动态解包组别
				'P-Value': p_value_str,
				'Missing (N (%))': missing_string
			}
			table_rows.append(data_dict)
	
	# 将结果转化为DataFrame格式
	format_results_df = pd.DataFrame(table_rows)
	
	if if_star_symbol:
		star_symbol_string = ''
		if any(results_list[-1] < 0.05 for results_list in statistical_results_dict.values()):
			star_symbol_string += '*: p<0.05, '
		if any(results_list[-1] < 0.01 for results_list in statistical_results_dict.values()):
			star_symbol_string += '**: p<0.01, '
		if any(results_list[-1] < 0.001 for results_list in statistical_results_dict.values()):
			star_symbol_string += '***: p<0.001, '
		
		# 去掉最后的半角逗号和空格并换成半角句号
		star_symbol_string = star_symbol_string[:-2] + '.'
		
		# 创建新行数据（第一列有值，其余为空字符串）
		star_symbol_row = {
			'Variable': star_symbol_string,
			overall_col: '',
			**{col_map[cat]: '' for cat in col_map.keys()},
			'P-Value': '',
			'Missing (N (%))': ''
		}
		# 追加到DataFrame
		format_results_df = pd.concat([format_results_df, pd.DataFrame([star_symbol_row])], ignore_index=True)
	
	# 删除空字符串列（当add_overall=False时overall_col为空字符串）
	format_results_df = format_results_df.drop(columns=['']) if not add_overall else format_results_df
	
	return format_results_df
