"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import streamlit as st


def connect_branch_text(
		text: str,
		add_space: bool = True,
) -> str:
	"""
	拼接多行字符串内容为一行，方便st.code显示
	
	Args:
		text: 需要拼接的多行字符串
		add_space: 是否在各行字符串之间添加一个空格

	Returns:
		拼接后的单行字符串
	"""
	
	# 先去除每一行首尾的空白字符
	lines = [line.strip() for line in text.strip().split('\n')]
	
	# 接着按需求拼接各行内容
	result = ""
	for line in lines:
		if add_space:
			result += " " + line
		else:
			result += line
	
	return result.strip()


def show_analysis_method_content(
		analysis_funcs: dict[int, str],
		analysis_task: str,
		chi2_result_connector: str = "N(percent)",
		mean_std_connector: str = "mean±std",
) -> None:
	"""
	展示一段用户可以直接粘贴到文章中的统计分析方法学（包含中英文双版本）的介绍内容
	
	Args:
		analysis_funcs: 函数功能字典
		analysis_task: 用户选择进行的操作，对应analysis_funcs的各value
		chi2_result_connector: 样本量N和比例percent/ratio的书写格式
		mean_std_connector: 平均值mean和标准差std的书写格式
	"""
	
	with st.expander("📄 统计分析方法学中英文介绍内容", expanded=True):
		st.markdown("**英文版/ENG：**")
		# 定义介绍内容会用到的字符串变量
		show_string = ""
		
		# 如果进行的是分类结局变量单因素分析
		# 虽然数据中不一定有分类或连续型变量，但是在方法学部分仍然要描述其统计分析方法
		if analysis_task == analysis_funcs[1]:
			
			chi2_string = """
				Categorical variables were reported as frequencies and percentages (N, %),
				with group differences evaluated using Pearson's chi-square test or Fisher's exact test as appropriate.
				"""
			# 代码中分段的字符串通过st.code显示出来的也是分段的内容，所以这里处理一下，将分段内容用空格连接
			chi2_string = connect_branch_text(chi2_string)
			if "ratio" in chi2_result_connector:
				chi2_string = chi2_string.replace("percentages (N, %)", "ratios (N, ratio)")
			
			mean_std_string = f"""
				Variables following a normal distribution were expressed as {mean_std_connector}
				and compared using Student's t-test.
				"""
			mean_std_string = mean_std_string.replace("std", "standard deviation (SD)").replace("±", " ± ")
			mean_std_string = connect_branch_text(mean_std_string)
			
			quartiles_string = f"""
				Non-normally distributed variables were presented as median and
				interquartile range (IQR) and compared using the Mann-Whitney U test.
				"""
			quartiles_string = connect_branch_text(quartiles_string)
			
			if mean_std_string and quartiles_string:
				# 正态和非正态的统计分析都做了，则拼接一下两者的描述内容
				continuous_var_string = mean_std_string[:-1] + ", while n" + quartiles_string[1:]
			elif mean_std_string:
				continuous_var_string = mean_std_string
			elif quartiles_string:
				continuous_var_string = quartiles_string
			
			# 因为要考虑句子之间的空格，所以这里再合并所有涉及到书写格式的字符串
			# 后面在中文内容中就没有合并，因为中文句子之间不需要空格
			if chi2_string:
				total_string = f"{continuous_var_string} {chi2_string}"
			else:
				total_string = continuous_var_string
			
			# 最终展示给用户的统计分析方法学内容字符串
			show_string = f"""
				Descriptive statistics were performed to characterize the study population.
				The normality of continuous variables was assessed using Shapiro-Wilk test.
				{total_string}
				All statistical tests were two-sided, with a significance level of P < 0.05.
				Analyses were implemented in Python (version 3.12) using the scipy package.
				"""
		
		if analysis_task == analysis_funcs[2]:
			show_string = f"""
			Univariate survival analyses were performed to evaluate the association between candidate variables and Outcome.
			For continuous variables, univariate Cox proportional hazards regression models were employed.
			For categorical variables, the statistical testing method was selected based on the number of categories:
			the Log-rank test was utilized to compare survival distributions for variables with 2 to 5 categories,
			while univariate Cox models, with significance assessed via the likelihood ratio test,
			were applied for variables with more than 5 categories.
			For all categorical analyses, a reference group was designated for comparison.
			Results were reported as Hazard Ratios (HR) with their corresponding 95% Confidence Intervals (CI).
			All statistical tests were two-sided, with a significance level of P < 0.05.
			Analyses were implemented in Python (version 3.12) using lifelines package.
			"""
		
		show_string = connect_branch_text(show_string)
		# 设置wrap_lines=True取消横向滚动条，让内容自动跨行显示
		if show_string:
			st.code(show_string, language=None, wrap_lines=True)
			st.caption("⚠️ 注意：英文半角单引号可能和手打的符号不同，请手动替换")
		
		st.markdown("**中文版/CN：**")
		show_string = ""
		
		if analysis_task == analysis_funcs[1]:
			
			chi2_string = """
				定性资料采用频数（百分比）描述，组间差异比较采用卡方检验或Fisher精确检验。
				"""
			# 合并中文分段内容时中间不需要添加空格
			chi2_string = connect_branch_text(chi2_string, add_space=False)
			if "ratio" in chi2_result_connector:
				chi2_string = chi2_string.replace("百分比", "比例")
			
			mean_std_string = f"""
				正态分布数据以{mean_std_connector}表示，组间比较使用独立样本t检验。
				"""
			mean_std_string = mean_std_string.replace("mean", "均数").replace("std", "标准差")
			mean_std_string = connect_branch_text(mean_std_string, add_space=False)
			
			quartiles_string = f"""
				非正态分布数据以中位数（四分位间距）表示。
				"""
			quartiles_string = connect_branch_text(quartiles_string, add_space=False)
			
			if mean_std_string and quartiles_string:
				continuous_var_string = mean_std_string[:-1] + "；" + quartiles_string
			elif mean_std_string:
				continuous_var_string = mean_std_string
			elif quartiles_string:
				continuous_var_string = quartiles_string
			
			show_string = f"""
				描述性统计用于分析研究人群的基础特征，通过Shapiro-Wilk检验进行正态性测试。
				{continuous_var_string}{chi2_string}
				统计学显著性水平设定为双侧P<0.05。
				上述算法基于Python（version 3.12）环境，主要调用scipy库实现。
				"""
		
		if analysis_task == analysis_funcs[2]:
			show_string = f"""
			采用单因素生存分析评估各研究变量与结局指标的关联。
			对于连续型变量，采用单变量Cox比例风险回归模型进行分析。
			对于分类变量，根据其类别数量选择不同的统计检验方法：
			当变量类别数小于等于5个时，采用Log-rank检验评估各组间的生存分布差异；
			当变量类别数超过5个时，则采用单变量Cox模型，并以似然比检验评估其总体显著性。
			分类变量的结果以参考组为基准进行展示。
			所有分析结果均以风险比（Hazard Ratio，HR）及其95%置信区间（CI）表示。
			统计学显著性水平设定为双侧P<0.05。
			上述算法基于Python（version 3.12）环境，主要调用lifelines库实现。
            """
		
		show_string = connect_branch_text(show_string, add_space=False)
		if show_string:
			st.code(show_string, language=None, wrap_lines=True)
