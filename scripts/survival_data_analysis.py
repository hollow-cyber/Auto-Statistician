"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import pandas as pd
import streamlit as st
from lifelines import CoxPHFitter
from lifelines.statistics import multivariate_logrank_test

from scripts.process_p_value import process_p_value


@st.cache_data
def screen_categorical_vars(
		df: pd.DataFrame,
		time_col: str,
		event_col: str,
		categorical_vars: list
) -> pd.DataFrame | None:
	"""对分类变量进行稳健的单变量筛选。

	此函数会自动遍历所有指定的分类变量，并根据其类别数量智能选择
	最合适的统计检验方法（Log-rank检验或单变量Cox模型）来计算其与生存结局的关联性p值

	Args:
		df: 包含所有数据的DataFrame。
		time_col: 生存时间列的名称。
		event_col: 结局状态列的名称。
		categorical_vars: 需要进行筛选的分类变量的列名列表。

	Returns:
		第一个包含每个变量检验结果（变量/类别名，HR值，HR95%区间上限，HR95%区间下限，p值）
		的DataFrame，如果没有变量能成功检验， 则返回None。第二个是可能提示的错误信息。
	"""
	
	# 初始化一个空列表，用于存储每个变量的检验结果
	results = []
	
	# 遍历传入的分类变量列表
	for var in categorical_vars:
		try:
			# 步骤1：预清理数据，只保留对当前检验有用的列，并移除任何包含缺失值的行
			subset_df = df[[time_col, event_col, var]].dropna()
			
			# 获取当前变量的所有唯一类别，并排序以确保参考类稳定
			groups = sorted(subset_df[var].unique())
			# 如果有效类别少于2个，则无法进行比较，跳过此变量
			if len(groups) < 2:
				continue
			
			# 步骤2：检查每个分组内的数据是否有效（即结局是否包含0和1两种情况）
			valid_groups = []
			for g in groups:
				group_df = subset_df[subset_df[var] == g]
				# 只有当一个组内同时包含两种及以上结局时，才认为它是有效的，以避免统计错误
				if len(group_df[event_col].unique()) > 1:
					valid_groups.append(g)
			if len(valid_groups) < 2:
				continue
			
			# 过滤掉无效分组的数据，确保模型稳定
			model_df = subset_df[subset_df[var].isin(valid_groups)].copy()
			
			# 手动转为哑变量
			# 获取参考类（第一个有效类）
			ref_group = valid_groups[0]
			
			# 使用 pd.get_dummies 进行展开
			# drop_first=True 会自动删除第一个类别作为参考组
			model_df_encoded = pd.get_dummies(model_df, columns=[var], drop_first=True, prefix=var)
			
			# 获取展开后的自变量列名
			# 除去时间项和结局项，剩下的就是生成的哑变量列（如：文化程度_1, 文化程度_2...）
			# x_cols = [c for c in model_df_encoded.columns if c not in [time_col, event_col]]
			
			cph = CoxPHFitter()
			cph.fit(model_df_encoded, duration_col=time_col, event_col=event_col)
			# # 提取模型摘要
			summary = cph.summary
			
			# 步骤3：根据有效分组的数量，智能选择统计检验方法
			if 2 <= len(valid_groups) <= 5:
				# 如果有效分组数在2到5之间，使用Log-rank检验
				method = 'Log-rank'
				# 使用 multivariate_logrank_test获取总体p值，这是 logrank_test 的底层函数，更适合这种数据格式
				global_p = multivariate_logrank_test(model_df[time_col], model_df[var], model_df[event_col]).p_value
			
			else:
				# 如果分组数大于5，使用单变量Cox模型
				method = 'Cox Model'
				# 对于多分类变量，使用似然比检验的p值作为其总体显著性的p值
				global_p = cph.log_likelihood_ratio_test().p_value
			
			# 将类别的总结果存入results列表
			results.append({'Variable': f'{var}',
			                'Hazard Ratio (HR)': '',
			                'HR Lower 95% CI': '',
			                'HR Upper 95% CI': '',
			                'P-Value': global_p,
			                })
			
			# 对于分类变量，summary 会有多行（例如 var_类别1, var_类别2...）
			# Pandas 默认按字母顺序或数值大小排序，排在第一位的那个就是参考类别
			# 但是这里没有参考类的结果，所以需要先手动添加
			results.append({'Variable': f"{var}_{ref_group} (Ref.)",  # 构造参考类别名
			                'Hazard Ratio (HR)': 1,
			                'HR Lower 95% CI': '-',
			                'HR Upper 95% CI': '-',
			                'P-Value': '-',
			                })
			
			# 接下来记录下每一组相对于参考组的 HR
			for index, row in summary.iterrows():
				# index 此时会是 "文化程度_1" 这样的格式
				# 将结果存入results列表
				results.append({'Variable': index,  # 非参考类别名
				                'Hazard Ratio (HR)': row['exp(coef)'],
				                'HR Lower 95% CI': row['exp(coef) lower 95%'],
				                'HR Upper 95% CI': row['exp(coef) upper 95%'],
				                'P-Value': row['p'],
				                })
		
		except Exception as e:
			# 如果在检验过程中发生任何错误，打印错误信息
			st.error(f"❌ 变量 '{var}' 检验时出现错误: {e}")
	
	# 如果没有任何变量成功完成检验，返回None
	if not results:
		st.error("❌ 程序未能成功完成任何分类变量的检验。")
		return None
	
	# 返回结果DataFrame
	return pd.DataFrame(results)


@st.cache_data
def screen_continuous_vars(
		df: pd.DataFrame,
		time_col: str,
		event_col: str,
		continuous_vars: list
) -> pd.DataFrame | None:
	"""对连续变量进行单变量Cox回归筛选。

	此函数会遍历所有指定的连续变量，为每个变量单独拟合一个一元Cox模型，
	并提取其p值和风险比(HR)作为关联性强度的度量。

	Args:
		df: 包含所有数据的DataFrame。
		time_col: 生存时间列的名称。
		event_col: 结局状态列的名称。
		continuous_vars: 需要进行筛选的连续变量的列名列表。

	Returns:
		第一个包含每个变量检验结果（变量/类别名，HR值，HR95%区间上限，HR95%区间下限，p值）
		的DataFrame，如果没有变量能成功检验， 则返回None。第二个是可能提示的错误信息。
	"""
	
	# 初始化一个空列表，用于存储每个变量的检验结果
	results = []
	
	# 遍历传入的连续变量列表
	for var in continuous_vars:
		try:
			# 步骤1：为每个变量创建一个只包含生存信息和当前变量的临时DataFrame，并移除缺失行
			model_df = df[[time_col, event_col, var]].dropna()
			# 如果有效样本量太少（小于10），则跳过此变量
			if model_df.shape[0] < 10:
				continue
			
			# 步骤2：初始化并拟合一元Cox模型
			cph = CoxPHFitter()
			cph.fit(model_df, duration_col=time_col, event_col=event_col)
			
			# 步骤3：从模型摘要中提取p值和风险比(HR)
			# 获取当前变量所在的行
			summary = cph.summary.loc[var]
			p_value = summary['p']
			hr = summary['exp(coef)']
			hr_lower = summary['exp(coef) lower 95%']
			hr_upper = summary['exp(coef) upper 95%']
			
			# 将结果存入results列表
			results.append({'Variable': f'{var}',
			                'Hazard Ratio (HR)': hr,
			                'HR Lower 95% CI': hr_lower,
			                'HR Upper 95% CI': hr_upper,
			                'P-Value': p_value,
			                })
		except Exception as e:
			# 如果在建模过程中发生任何错误，打印错误信息
			st.error(f"❌ 变量 '{var}' 检验时出现错误: {e}")
	
	# 如果没有任何变量成功完成检验，返回None
	if not results:
		st.error("❌ 程序未能成功完成任何分类变量的检验。")
		return None
	
	return pd.DataFrame(results)


def format_survival_results(
		df: pd.DataFrame,
		time_col: str,
		event_col: str,
		categorical_vars: list,
		continuous_vars: list,
		hr_ci_connector: str | None,
		decimal_places: int,
		p_decimal_places: int,
		if_category_space: bool,
		if_star_symbol: bool
) -> pd.DataFrame:
	"""
	为生存分析生成格式增强的描述性统计表（"表1"）。

	Args:
		df: 包含所有数据的DataFrame。
		time_col: 生存时间列名。
		event_col: 结局列名。
		categorical_vars: 分类变量列名。
		continuous_vars: 连续型变量列名。
		hr_ci_connector: HR和其95%置信区间的书写格式
		decimal_places: 描述性结果精确位数
		p_decimal_places: p值结果精确位数
		if_category_space: 是否在分类变量各类别名称前加2个空格
		if_star_symbol: 是否在不同显著性P值结果后面添加对应数量的*号

	Returns:
		描述性统计表结果。
	"""
	
	# 定义初始的规范化表述格式字符串
	hr_ci_connector_f = "{HR:.{decimal_places}f}({lower:.{decimal_places}f}, {upper:.{decimal_places}f})"
	
	# 计算各变量的p值
	cat_results = screen_categorical_vars(df, time_col, event_col, categorical_vars)
	cont_results = screen_continuous_vars(df, time_col, event_col, continuous_vars)
	
	# 按原始列顺序处理变量（合并分类、正态、非正态变量，并按df的列顺序排序）
	all_vars_ordered = [col for col in df.columns if col in categorical_vars + continuous_vars]
	
	# 对HR和其95%置信区间的书写格式字符串进行格式化
	if hr_ci_connector:
		hr_ci_connector_f = hr_ci_connector.replace('HR', '{HR:.{decimal_places}f}').replace('lower',
		                                                                                     '{lower:.{decimal_places}f}').replace(
			'upper', '{upper:.{decimal_places}f}')
	
	# 存放单个变量的描述性统计结果的列表
	table_rows = []
	# 循环处理每个预测变量
	for var in all_vars_ordered:
		if var in categorical_vars and cat_results is not None:
			# 使用 str.startswith() 模糊匹配所有以某分类指标开头的结果行
			matched_rows = cat_results[cat_results['Variable'].str.startswith(str(var))]
			
			# 按原始顺序遍历，原来的cat_results就算依次记录的是指标总结果，参考类别和非参考类别
			added_index = set()
			for index, row in matched_rows.iterrows():
				if row['Variable'] == str(var):
					for idx, row_v in matched_rows.iterrows():
						if row_v['Hazard Ratio (HR)'] == 1:
							# 对于分类变量，先添加主行，包括分类变量名、参考类别名，HR、全局p值
							cat_name = f"  {row_v['Variable']}".replace(f"{var}_", "") if if_category_space else row_v[
								'Variable'].replace(f"{var}_", "")
							table_rows.append({
								'Variable': f"{var}",
								'Category': cat_name,
								'HR (95% CI)': f'{1:.{decimal_places}f}(Ref.)',
								'P-Value': '',
								'Overall P-Value': process_p_value(row['P-Value'], p_decimal_places,
								                                   if_star_symbol) if pd.notna(
									row['P-Value']) else '',
							})
							# 记录已经规范化结果的index，后面就会直接跳过这些index
							added_index.add(index)
							added_index.add(idx)
							break
				else:
					# 针对非参考类别，格式化HR和95%区间的结果，再添加到table_rows当中
					if index not in added_index:
						cat_name = f"  {row['Variable']}".replace(f"{var}_", "") if if_category_space else row[
							'Variable'].replace(f"{var}_", "")
						description = hr_ci_connector_f.format(
							HR=row['Hazard Ratio (HR)'],
							lower=row['HR Lower 95% CI'],
							upper=row['HR Upper 95% CI'],
							decimal_places=decimal_places
						)
						table_rows.append({
							'Variable': "",
							'Category': cat_name,
							'HR (95% CI)': description,
							'P-Value': process_p_value(row['P-Value'], p_decimal_places, if_star_symbol) if pd.notna(
								row['P-Value']) else '',
							'Overall P-Value': '',
						})
		
		elif var in continuous_vars:
			# 明确取第一个匹配变量名的行
			row = cont_results[cont_results['Variable'] == str(var)].iloc[0]
			description = hr_ci_connector_f.format(
				HR=row['Hazard Ratio (HR)'],
				lower=row['HR Lower 95% CI'],
				upper=row['HR Upper 95% CI'],
				decimal_places=decimal_places
			)
			
			table_rows.append({
				'Variable': f"{var}",
				'Category': '',
				'HR (95% CI)': description,
				'P-Value': process_p_value(row['P-Value'], p_decimal_places, if_star_symbol) if pd.notna(
					row['P-Value']) else '',
				'Overall P-Value': '',
			})
	
	# 将结果转化为DataFrame格式
	format_results_df = pd.DataFrame(table_rows)
	
	if if_star_symbol:
		p_value_list = cat_results["P-Value"].tolist() + cont_results["P-Value"].tolist()
		star_symbol_string = ''
		if any(p_value < 0.05 for p_value in p_value_list):
			star_symbol_string += '*: p<0.05, '
		if any(p_value < 0.01 for p_value in p_value_list):
			star_symbol_string += '**: p<0.01, '
		if any(p_value < 0.001 for p_value in p_value_list):
			star_symbol_string += '***: p<0.001, '
		
		# 去掉最后的半角逗号和空格并换成半角句号
		star_symbol_string = star_symbol_string[:-2] + '.'
		
		# 添加最后一行题注
		# 先使用字典创建新行数据
		# 将目标字符串放在你想显示的列，其余列内容用空字符串 ('') 填充
		star_symbol_row = {}
		for col in format_results_df.columns.tolist():
			# 假设你要将字符串放在第一列 'Variable' 中
			if col == format_results_df.columns.tolist()[0]:
				star_symbol_row[col] = star_symbol_string
			else:
				star_symbol_row[col] = ''  # 其他列填充空字符串
		
		# 使用 pd.concat() 添加新行
		# ignore_index=True 确保新行有一个连续的索引，这是标准做法。
		format_results_df = pd.concat([format_results_df, pd.DataFrame([star_symbol_row])], ignore_index=True)
	
	# 创建并返回最终的DataFrame
	return format_results_df
