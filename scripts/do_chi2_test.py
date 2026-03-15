"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import pandas as pd
import numpy as np
from scipy import stats


def calculate_category_proportions(
		crosstab_data: pd.DataFrame,
		cal_column_pct: bool = True
) -> pd.DataFrame:
	"""
	直接从列联表计算各种类别的比例

	Args:
		crosstab_data: 二维数组或DataFrame，列联表数据
		cal_column_pct: 按列还是按行计算百分比

	Returns:
		包含所有比例结果的DataFrame
	"""
	
	# 将列联表转换为DataFrame
	if isinstance(crosstab_data, pd.DataFrame):
		crosstab = crosstab_data.copy()
	else:
		crosstab = pd.DataFrame(crosstab_data)
	
	if cal_column_pct:
		# 列百分比（每列总和=100%）
		col_total = crosstab.sum(axis=0)
		col_pct = crosstab.div(col_total, axis=1) * 100
		var_pct_df = col_pct.round(2)
	else:
		# 行百分比（每行总和=100%）
		row_total = crosstab.sum(axis=1)
		row_pct = crosstab.div(row_total, axis=0) * 100
		var_pct_df = row_pct.round(2)
	
	return var_pct_df


def auto_chi2_test(
		crosstab_data: pd.DataFrame,
		alpha: float = 0.05,
		correction: bool = True
) -> dict[str, int | float]:
	"""
	自动进行卡方检验，根据条件判断是否使用Fisher精确检验

	Args:
		crosstab_data: 二维数组或DataFrame，列联表数据
		alpha: 显著性水平，默认0.05
		correction: 是否使用Yates连续性校正，默认True

	Returns:
		包含检验结果的字典
	"""
	
	# 转换为numpy数组
	observed = np.array(crosstab_data)
	
	# 计算期望频数
	chi2_stat, p_value_chi2, dof, expected = stats.chi2_contingency(observed, correction=correction)
	
	# 检查期望频数条件
	n_total = observed.sum()
	# 检查期望频数<1和<5的个数
	expected_lt_5 = (expected < 5).sum()
	expected_lt_1 = (expected < 1).sum()
	# 检查期望频数<5的单元格百分比
	percent_lt_5 = (expected_lt_5 / expected.size) * 100
	
	# 判断是否使用Fisher精确检验的条件
	use_fisher = False
	p_value_fisher = None
	warning_message = ""
	
	if observed.shape == (2, 2):
		# 2x2列联表
		if n_total < 40 or expected_lt_1 > 0:
			warning_message += "样本量<40|"
		if expected_lt_1 > 0:
			warning_message += "存在期望频数<1|"
		if percent_lt_5 > 20:
			warning_message += f"期望频数<5的单元格占比{percent_lt_5:.1f}% > 20%|"
		if warning_message:
			use_fisher = True
	else:
		# 大于2x2的列联表
		if expected_lt_1 > 0:
			warning_message += "存在期望频数<1|"
		if percent_lt_5 > 20:
			warning_message += f"期望频数<5的单元格占比{percent_lt_5:.1f}% > 20%|"
	
	# 进行Fisher精确检验
	if use_fisher:
		try:
			_, p_value_fisher = stats.fisher_exact(observed)
		except:
			p_value_fisher = None
			warning_message += " (Fisher检验失败)"
	
	# 准备结果
	result = {
		'observed': observed,
		'expected': expected,
		'table_size': observed.shape,
		'total_sample': n_total,
		'chi2_statistic': chi2_stat,
		'p_value_chi2': p_value_chi2,
		'degrees_of_freedom': dof,
		'use_fisher': use_fisher,
		'warning_message': warning_message,
		'p_value_fisher': p_value_fisher,
		'expected_lt_5_count': expected_lt_5,
		'expected_lt_5_percent': percent_lt_5,
		'expected_lt_1_count': expected_lt_1,
		'significance_level': alpha
	}
	
	# 确定最终使用的p值
	if use_fisher and p_value_fisher is not None:
		result['final_p_value'] = p_value_fisher
		result['test_used'] = "Fisher精确检验"
	elif warning_message:
		# 不满足标准卡方检验情况，但仍使用卡方结果，同时给出警告
		result['final_p_value'] = p_value_chi2
		result['test_used'] = "卡方检验（条件不完全满足）"
	else:
		# 没有warning_message代表满足标准卡方检验情况
		result['final_p_value'] = p_value_chi2
		result['test_used'] = "卡方检验" + ("(Yates校正)" if correction and observed.shape == (2, 2) else "")
	
	# 判断显著性
	result['significant'] = result['final_p_value'] < alpha
	
	return result
