"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import os, time
import pandas as pd
import streamlit as st
from pathlib import Path
from scipy import stats
from itertools import zip_longest

from scripts.clear_st_session_state import clear_st_session_state
from scripts.set_st_custom_style import set_st_header, show_custom_toast
from scripts.upload_and_read_data import upload_and_read_data
from scripts.simple_data_processing import st_impute_data
from scripts.identify_categorical_columns import identify_categorical_columns
from scripts.statistical_data_analysis import format_statistical_results
from scripts.survival_data_analysis import format_survival_results
from scripts.show_analysis_method_content import show_analysis_method_content
from scripts.convert_df_to_tsv import convert_df_to_tsv
# 导入全局变量
import scripts.global_vars


def main() -> None:
	# 使用 st.session_state 动态控制格式化结果的显示
	if 'format_results_df' not in st.session_state:
		st.session_state.format_results_df = None
	
	# 获取当前脚本所在目录
	current_dir = Path(__file__).parent
	# 使用 / 操作符拼接路径
	image_path = current_dir / "imgs" / "华西logo.ico"
	# image_path = os.path.join(current_dir, r'imgs\华西logo.ico')
	st.write(os.path.abspath(r'imgs\华西logo.ico'))
	
	# 进行主要窗口标题设置
	set_st_header(
		main_title="自动统计分析专家v1.0",
		sidebar_title="程序参数设置",
		logo_path=image_path,
		notice_str="本项目受到四川大学华西医院、国家老年疾病临床医学研究中心的支持，请勿商用。"
	)
	
	with st.expander("点击查看当前版本更新特性功能"):
		# st.info可以直接解析markdown格式，- 表示分行前面加小点。
		st.info("""
		**✨ v1.0 版本惊艳更新！**
		- 🤗1：优化了UI交互界面。
		- 🤤2：新增了用于生存分析数据的单因素统计功能。
		- 🥰3：新增了处理数据集中的缺失值功能，缺失值统计结果见格式化统计分析结果表格最后一列。
		""")
	
	# 画一条分割线
	st.divider()
	
	# 能传出data则一定成功读取了数据，所以后面不用判断if data
	data, file_name, output_file_extension = upload_and_read_data()
	# 让用户选择是否处理数据集中的缺失值
	data = st_impute_data(data, file_name, output_file_extension)
	
	# if len(data) < 30:
	# 	st.error(f"❌ 数据样本量太小（共{len(data)}条有效数据），无法进行统计检验，请上传至少包含30条有效数据的文件。")
	# 	st.stop()
	
	# 画一条分割线
	st.sidebar.divider()
	st.sidebar.markdown("**统计分析设置**")
	
	analysis_funcs = {
		1: "📊 分类结局变量单因素分析",
		2: "📉 生存分析数据单因素分析",
	}
	st.sidebar.markdown("**请选择你要进行的操作：**")
	analysis_task = st.sidebar.segmented_control('请选择你要进行的操作：', analysis_funcs.values(),
	                                             default=list(analysis_funcs.values())[0],
	                                             on_change=clear_st_session_state, label_visibility="collapsed")
	
	cols = st.sidebar.columns([1, 1])
	if analysis_task == analysis_funcs[2]:
		with cols[0]:
			# 指定结局变量
			dependent_var_name = st.selectbox(
				"结局指标/因变量名称或列数：",
				data.columns.tolist(),
				index=len(data.columns.tolist()) - 1,
				help="请从传入的txt文件中选择结局指标名称或列数，仅支持单选，仅支持分类结局因变量"
			)
	else:
		dependent_var_name = st.sidebar.selectbox(
			"结局指标/因变量名称或列数：",
			data.columns.tolist(),
			index=len(data.columns.tolist()) - 1,
			help="请从传入的txt文件中选择结局指标名称或列数，仅支持单选，仅支持分类结局因变量"
		)
	
	time_var_name = None
	if analysis_task == analysis_funcs[2]:
		with cols[1]:
			# 指定生存时间变量
			time_var_name = st.selectbox(
				"生存时间指标名称或列数：",
				data.columns.tolist(),
				index=len(data.columns.tolist()) - 2,
				help="请从传入的txt文件中选择生存时间指标名称或列数，仅支持单选"
			)
		if (data[time_var_name] == 0).any():
			st.error("❌ 程序发现生存时间列中包含0值，请检查。")
	
	cols = st.sidebar.columns([1, 1])
	with cols[0]:
		max_unique_num = st.number_input(
			'分类变量最多含有多少种类别：',
			min_value=2, max_value=20, value=10, step=1,
			help="允许的变化范围为2-20, 超过设定的数量则认为是连续型变量")
	
	# 多选不需要进行分析的自变量
	independent_vars = data.columns.tolist()
	independent_vars.remove(dependent_var_name)
	if analysis_task == analysis_funcs[2]:
		# 如果处理生存分析数据，则还要排除掉生存时间列
		independent_vars.remove(time_var_name)
	with cols[1]:
		excluded_vars = st.multiselect(
			'不需要进行分析的自变量：',
			independent_vars,
			placeholder="请下拉选择变量",
			help="可以多选不纳入进行统计分析的自变量，最终输出结果也不会包含这些变量"
		)
	
	if len(excluded_vars) == len(independent_vars):
		st.error("❌ 你排除了所有自变量，当前没有自变量能用于分析，请重新选择不需要进行分析的自变量。")
		st.stop()
	
	# 获取自变量和因变量
	X: pd.DataFrame = data.drop(columns=[dependent_var_name] + excluded_vars)
	if analysis_task == analysis_funcs[2]:
		X = X.drop(columns=[time_var_name])
	y = data[dependent_var_name]
	
	# 判断因变量类型
	if y.nunique() == 2:
		st.info(
			f"📊 程序判断结局指标/因变量【{dependent_var_name}】是二分类变量，类别包含: {"、".join([str(cat) for cat in list(y.unique())])}")
	elif y.nunique() > 2:
		st.info(
			f"📊 程序判断结局指标/因变量【{dependent_var_name}】是多分类变量，类别包含: {"、".join([str(cat) for cat in list(y.unique())])}")
	else:
		st.error("❌ 程序判断结局指标/因变量类别少于 2，无法进行后续单因素统计分析。")
		st.stop()
	
	# 调用函数，自动识别出所有的协变量类型
	categorical_vars = identify_categorical_columns(X, max_categories=max_unique_num)
	continuous_vars = [var for var in X.columns if var not in categorical_vars]
	# 初始化记录正态和非正态分布变量的列表
	normal_dis_vars, non_normal_dis_vars = [], []
	
	# 如果进行常规统计分析，那么还要进行正态检验以确定连续型变量的值书写格式
	if analysis_task == analysis_funcs[1] and continuous_vars:
		for col in continuous_vars:
			# 假设所有分组都符合正态分布
			is_all_groups_normal = True
			
			# 将当前列数据按 y 的类别进行分组
			# 只要 X[col] 和 y 的 索引（Index）是一致的，或者长度是相同的，Pandas就可以根据 y 的值来对 X[col] 的数据进行拆分
			groups = X[col].groupby(y)
			
			for name, group_data in groups:
				# 剔除缺失值
				clean_data = group_data.dropna()
				
				# 样本量太小无法检验（Shapiro要求至少3个样本）
				if len(clean_data) < 3:
					is_all_groups_normal = False
					break
				
				# 根据当前分组的样本量自动选择检验方法
				if len(clean_data) <= 5000:
					_, p_value = stats.shapiro(clean_data)
				else:
					_, p_value = stats.kstest(clean_data, 'norm', args=(clean_data.mean(), clean_data.std(ddof=1)))
				
				# 只要有一个组不符合正态分布 (p <= 0.05)，则该变量整体判定为非正态
				if p_value <= 0.05:
					is_all_groups_normal = False
					break
			
			# 根据分组检验结果分类
			if is_all_groups_normal:
				normal_dis_vars.append(col)
			else:
				non_normal_dis_vars.append(col)
	
	# 画一条分割线
	st.sidebar.divider()
	st.sidebar.markdown("**输出格式设置**")
	
	# 设定一些分类变量输出格式的初始默认值，然后根据用户设置调整变量值
	cal_column_pct = True
	chi2_result_connector = None
	if_category_space = False
	mean_std_connector = None
	quartiles_connector = None
	hr_ci_connector = None
	
	# 如果进行常规统计分析，则要设定变量的值书写格式
	if analysis_task == analysis_funcs[1]:
		# 展示各变量分别属于哪些类型
		# 过滤空的变量类型列表
		non_empty_data = []
		non_empty_cols = []
		col_names = ["分类自变量", "正态分布自变量", "非正态分布自变量"]
		for data, col in zip([categorical_vars, normal_dis_vars, non_normal_dis_vars], col_names):
			if data:
				non_empty_data.append(data)
				non_empty_cols.append(col)
		
		# 考虑到不同类型的变量数量不一致的情况，使用 zip_longest 行转列并填充多余的位置为空字符串
		# noinspection PyArgumentList
		rows = list(zip_longest(*non_empty_data, fillvalue=''))
		with st.expander("程序检查传入的数据文件中各类型的变量如下："):
			st.dataframe(pd.DataFrame(rows, columns=non_empty_cols))
		
		if categorical_vars:
			with st.sidebar.container(border=True):
				st.markdown("**分类变量**")
				cal_column_pct = st.radio('选择按列还是按行计算各类别占比：', ['列', '行'], horizontal=True,
				                          help="按列计算占比时，每列占比总和=100%")
				cal_column_pct = True if cal_column_pct == '列' else False
				chi2_result_connector = st.radio(
					"样本量N和比例percent/ratio的书写格式：",
					options=["N(percent)", "N(ratio)", "自定义"],
					horizontal=True  # 横向排列
				)
				if chi2_result_connector == '自定义':
					chi2_result_connector_customize = st.text_input(
						"请输入自定义的样本量N和比例percent/ratio的书写格式：",
						placeholder="例如: N [percent] 或 N [ratio]",
						help="自定义的书写格式仅能包含一个N和一个percent或ratio。若不规范则会采用默认的 N(percent)"
					)
				# 规范的书写是离散型变量的小分类名前面会缩进一个字符，但是python无法做到
				# 所以要么是在前面加两个空格，要么是用户自己设置缩进
				if_category_space = st.checkbox("在分类变量的各分类名前面添加两个空格以模拟缩进一个字符的效果")
			if chi2_result_connector == '自定义':
				if chi2_result_connector_customize == '':
					chi2_result_connector = "N(percent)"
				# 使用亦或符号^来保证'percent'和'ratio'不会同时出现
				elif chi2_result_connector_customize.count('N') == 1 and ((chi2_result_connector_customize.count(
						'percent') == 1) ^ (chi2_result_connector_customize.count('ratio') == 1)):
					chi2_result_connector = chi2_result_connector_customize
				else:
					st.warning(
						'🚫 您输入的自定义样本量N和比例percent/ratio的书写格式不规范, 已自动变更为默认格式: N(percent)')
					chi2_result_connector = "N(percent)"
		
		if normal_dis_vars:
			with st.sidebar.container(border=True):
				st.markdown("**正态分布变量**")
				# 如果存在正态分布变量，则让用户设置对应的输出格式
				mean_std_connector = st.radio(
					"平均值mean和标准差std的书写格式：",
					options=["mean±std", "mean(std)", "自定义"],
					horizontal=True  # 横向排列
				)
				if mean_std_connector == '自定义':
					mean_std_connector_customize = st.text_input(
						"请输入自定义的平均值mean和标准差std书写格式：",
						placeholder="例如: mean[std]",
						help="自定义的书写格式仅能包含一个mean和一个std。若不规范则会采用默认的mean±std"
					)
			if mean_std_connector == '自定义':
				if mean_std_connector_customize == '':
					mean_std_connector = "mean±std"
				elif mean_std_connector_customize.count('mean') != 1 or mean_std_connector_customize.count('std') != 1:
					st.warning('🚫 您输入的自定义平均值mean和标准差std书写格式不规范, 已自动变更为默认格式: mean±std')
					mean_std_connector = "mean±std"
				else:
					mean_std_connector = mean_std_connector_customize
		
		if non_normal_dis_vars:
			with st.sidebar.container(border=True):
				st.markdown("**非正态分布变量**")
				quartiles_connector = st.radio(
					"四分位数Q1, Q2, Q3的书写格式：",
					options=["Q2(Q1, Q3)", "Q2[Q1, Q3]", "自定义"],
					index=0,
					horizontal=True  # 横向排列
				)
				if quartiles_connector == '自定义':
					quartiles_connector_customize = st.text_input(
						"请输入自定义的四分位数Q1, Q2, Q3书写格式：",
						placeholder="例如: Q2(Q1 to Q3)",
						help="自定义的书写格式仅能包含一个Q1, Q2, Q3。若不规范则会采用默认的Q2(Q1, Q3)"
					)
			if quartiles_connector == '自定义':
				if quartiles_connector_customize == '':
					quartiles_connector = "Q2(Q1, Q3)"
				elif quartiles_connector_customize.count('Q1') != 1 or quartiles_connector_customize.count(
						'Q2') != 1 or quartiles_connector_customize.count('Q3') != 1:
					st.warning('🚫 您输入的自定义四分位数Q1, Q2, Q3书写格式不规范, 已自动变更为默认格式: Q2(Q1, Q3)')
					quartiles_connector = "Q2(Q1, Q3)"
				else:
					quartiles_connector = quartiles_connector_customize
	
	# 对于生存分析，只用设定HR和其95%置信区间的书写格式
	elif analysis_task == analysis_funcs[2]:
		hr_ci_connector = st.sidebar.radio(
			"HR和其95%置信区间的书写格式：",
			options=["HR(lower, upper)", "HR[lower, upper]", "自定义"],
			horizontal=True  # 横向排列
		)
		if hr_ci_connector == '自定义':
			hr_ci_connector_customize = st.sidebar.text_input(
				"请输入自定义的HR和其95%置信区间HR, lower, upper书写格式：",
				placeholder="例如: HR(lower to upper)",
				help="自定义的书写格式仅能包含一个HR, lower, upper。若不规范则会采用默认的HR(lower, upper)"
			)
			if hr_ci_connector_customize == '':
				hr_ci_connector = "HR(lower, upper)"
			elif hr_ci_connector_customize.count('HR') != 1 or hr_ci_connector_customize.count(
					'lower') != 1 or hr_ci_connector_customize.count('upper') != 1:
				st.warning(
					'🚫 您输入的自定义HR和其95%置信区间HR, lower, upper书写格式不规范, 已自动变更为默认格式: HR(lower, upper)')
				hr_ci_connector = "HR(lower, upper)"
			else:
				hr_ci_connector = hr_ci_connector_customize
	
	if_add_connector, if_add_overall = True, True
	if analysis_task == analysis_funcs[1]:
		if_add_connector = st.sidebar.checkbox("在变量的后面添加对应的数据描述性结果书写格式", value=True,
		                                       help="此功能会根据各变量的类型在其后添加你前面设置的书写格式")
		if_add_overall = st.sidebar.checkbox("在第2列添加整体数据（不分组）的描述性结果", value=True)
	
	cols = st.sidebar.columns([1, 1])
	with cols[0]:
		decimal_places = st.number_input(f'描述性输出结果保留到几位小数：', min_value=1, max_value=6, value=2,
		                                 step=1,
		                                 help="可设置的范围为1到6")
	with cols[1]:
		p_decimal_places = st.number_input(f'P值结果保留到几位小数：', min_value=1, max_value=6, value=3, step=1,
		                                   help="可设置的范围为1到6")
	if_star_symbol = st.sidebar.checkbox("在不同显著性水平P值结果后面添加对应数量的*号",
	                                     help="此功能会同时在表格末尾会添加一行题注，但注意符号不是上标形式，基础显著性是0.05")
	
	# 画一条分割线
	st.divider()
	st.sidebar.divider()
	
	cols = st.sidebar.columns([1, 1])
	with cols[0]:
		if st.button('开始统计分析'):
			scripts.global_vars.button_click_times += 1
			if scripts.global_vars.button_click_times % 5 == 0:
				show_custom_toast("阿伟你又在连夜搞科研喔。休息一下吧，去收个病人好不好？", icon="🧐")
			
			if analysis_task == analysis_funcs[1]:
				st.session_state.format_results_df = format_statistical_results(X, y,
				                                                                categorical_vars,
				                                                                normal_dis_vars,
				                                                                cal_column_pct,
				                                                                chi2_result_connector,
				                                                                mean_std_connector,
				                                                                quartiles_connector,
				                                                                if_add_connector,
				                                                                if_add_overall,
				                                                                decimal_places,
				                                                                p_decimal_places,
				                                                                if_category_space,
				                                                                if_star_symbol)
			
			elif analysis_task == analysis_funcs[2]:
				st.session_state.format_results_df = format_survival_results(data,
				                                                             time_var_name,
				                                                             dependent_var_name,
				                                                             categorical_vars,
				                                                             continuous_vars,
				                                                             hr_ci_connector,
				                                                             decimal_places,
				                                                             p_decimal_places,
				                                                             if_category_space,
				                                                             if_star_symbol)
			show_custom_toast("统计分析处理完毕", icon="🎉")
			
	if st.session_state.format_results_df is not None:
		# 将格式化的结果转换为TSV格式的字符串
		tsv_data = convert_df_to_tsv(st.session_state.format_results_df, file_extension=output_file_extension, hide_index=True)
		st.success(f"""
		🎉 {time.strftime("%Y-%m-%d %H:%M:%S")}：格式化描述性和统计分析结果已经计算完毕，详见下表，
		你可点击下方的下载按钮进行下载。同时你也可复制下面关于统计分析方法学的介绍内容到你的文章当中。
		""")
		st.subheader(f"{analysis_task}格式化结果预览")
		st.dataframe(st.session_state.format_results_df, use_container_width=True, hide_index=True)
		
		# 最后写一段用户可以直接粘贴到文章中的统计分析方法学的介绍内容
		show_analysis_method_content(analysis_funcs, analysis_task, chi2_result_connector, mean_std_connector)
		
		if tsv_data:
			# 创建下载按钮
			with cols[1]:
				if st.download_button(
						label="下载结果文件",
						data=tsv_data,
						file_name=f"{os.path.splitext(file_name)[0]}-{analysis_task}结果-{time.strftime("%Y-%m-%d %H:%M:%S")}{output_file_extension}",
						mime="text/plain",
						type="primary",
				):
					st.toast("格式化描述性和统计分析结果文件下载成功！", icon="🎉")


if __name__ == '__main__':
	main()
