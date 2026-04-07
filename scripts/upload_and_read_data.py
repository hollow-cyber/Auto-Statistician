"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import io
import os
import glob
import chardet
import pandas as pd
import streamlit as st

from scripts.detect_file_encoding import detect_file_encoding


def clear_all_inputs() -> None:
	"""定义一个回调函数，用来清空状态，在对应组件中必须要有对应的key"""
	# 使用 pop(key, None) 安全删除，如果 key 不存在也不会报错
	# 删除后，下次渲染该组件时，它会重置为默认值（空）
	st.session_state.pop("file_uploader", None)  # 清空文件上传器
	st.session_state.pop("path_input", None)  # 清空路径输入框
	st.session_state.pop("file_select", None)  # 清空文件下拉框


def clear_st_results_df() -> None:
	"""定义一个回调函数，用来清空计算结果，保证在重新选择执行的任务后需要重新点击计算按钮才出现结果"""
	st.session_state.pop('format_results_df', None)
	
	
def upload_and_read_data() -> tuple[pd.DataFrame, str, str]:
	"""
	用户上传/选择数据文件并返回读取的dataframe，同时给出数据文件信息
	
	Returns:
		数据内容，上传文件名称，上传文件格式名
	"""
	# 显示示例文件格式
	with st.expander("📋 查看示例文件格式"):
		st.markdown("#### 制表符分隔示例（excel内容直接复制到txt是这种格式）：")
		demo_sep = [
			"姓名    年龄    城市    工资",
			"张三    25    北京    5000",
			"李四    30    上海    8000",
			"王五    35    广州    6000",
		]
		st.code("\n".join(demo_sep))
		
		st.markdown("#### 半角逗号分隔示例（csv文件内容是这种格式）：")
		demo_comma = [
			"姓名,年龄,城市,工资",
			"张三,25,北京,5000",
			"李四,30,上海,8000",
			"王五,35,广州,6000",
		]
		st.code("\n".join(demo_comma))
	
	st.sidebar.markdown("**数据文件上传/选择设置**")
	
	uploaded_file, file_dir, file_name = None, None, None
	file_upload_method = st.sidebar.radio("请选择上传文件或者输入路径读取文件：", ["上传文件", "输入路径读取文件"],
	                                      key="method_radio",
	                                      horizontal=True,
	                                      # 每次切换选项，都先执行清空操作
	                                      on_change=clear_all_inputs,
	                                      help="选择上传文件会把文件上传到streamlit服务器，如果是隐私数据建议选择通过输入路径读取文件，这样就只会读取到本地计算机的内存中")
	
	if file_upload_method == "上传文件":
		# 在侧边栏创建文件上传器
		uploaded_file = st.sidebar.file_uploader(
			"选择数据文件",
			type=['txt', 'csv'],
			key="file_uploader",
			help="支持多种列数据分隔符号内容的txt文件和csv文件",
			on_change=clear_st_results_df
		)
		file_extension = ".txt"
		if uploaded_file:
			file_extension = os.path.splitext(uploaded_file.name)[1].lower()
	else:
		file_dir = st.sidebar.text_input("txt/csv文件所在的文件夹路径：", placeholder=r"例如：D:\数据处理\示例文件夹",
		                                 key="file_dir_input",
		                                 help="Windows系统用户可在文件夹窗口顶部的地址栏（显示路径的地方）点击右键复制地址")
		
		if not file_dir:
			st.stop()
		elif not os.path.isdir(file_dir):
			st.error("❌ 你输入的文件夹路径不存在或不是文件夹，请检查。")
			st.stop()
		else:
			# 使用glob.glob高效查找指定类型文件，recursive=False表示不递归子文件夹
			txt_files = glob.glob(os.path.join(file_dir, '*.txt'), recursive=False)
			csv_files = glob.glob(os.path.join(file_dir, '*.csv'), recursive=False)
			
			# 合并结果
			all_files = txt_files + csv_files
			if not all_files:
				st.error("❌ 程序未在你输入的文件夹路径中查找到任何txt/csv文件，请检查。")
				st.stop()
			else:
				file_name = st.sidebar.selectbox("需要进行统计分析的数据文件：",
				                                 [os.path.basename(file) for file in all_files],
				                                 index=None,
				                                 key="file_select",
				                                 placeholder="请下拉选择文件",
				                                 on_change=clear_st_results_df)
				if not file_name:
					st.stop()
				file_extension = os.path.splitext(file_name)[1].lower()
				
	cols = st.sidebar.columns([1, 1])
	with cols[0]:
		# 列分隔符选择
		sep_option = st.selectbox(
			"列数据分隔符类型：",
			["制表符(\\t)", "半角逗号(,)", "单空格", "半角分号(;)"],
			index=1 if file_extension == ".csv" else 0,
			help="选择文件中使用的列内容分隔符，csv文件为半角逗号(,)"
		)
	with cols[1]:
		# 列分隔符选择
		output_file_extension = st.selectbox(
			"结果文件输出格式：",
			[".txt", ".csv",],
			index=1 if file_extension == ".csv" else 0,
		)
		
	# 映射分隔符
	sep_map = {
		"制表符(\\t)": "\t",
		"半角逗号(,)": ",",
		"单空格": " ",
		"半角分号(;)": ";"
	}
	selected_sep = sep_map[sep_option]
	
	has_header = st.sidebar.checkbox("文件首行为列名", value=True,
	                                 help="最好是文件首行包含列名，否则程序将会自动用列数减1代替各变量名")
	
	if file_upload_method == "上传文件":
		# 读取上传数据
		if uploaded_file is not None:
			file_name = uploaded_file.name
			df = None
			try:
				# 读取上传文件的原始字节数据 (bytes)
				raw_data = uploaded_file.read()
				if raw_data:
					# 使用 chardet 检测编码
					# 为了提高大文件的检测速度，我们只取前 10000 个字节进行检测
					encoding = chardet.detect(raw_data[:10000])['encoding']
					
					if encoding:
						# 读取文件内容
						file_content = uploaded_file.getvalue()
						
						# 使用StringIO将文件内容转换为类文件对象
						file_like_object = io.StringIO(file_content.decode(encoding))
						
						# 读取为DataFrame
						df = pd.read_csv(
							file_like_object,
							sep=selected_sep,
							header=0 if has_header else None,
							encoding=encoding
						)
						# 如果第一行不是列名，则人为修改列名
						if not has_header:
							df.columns = [f"第{i + 1}列" for i in range(df.shape[1])]
					
					else:
						st.error("❌ 无法检测到文件的编码格式。")
						st.stop()
				else:
					st.warning("⚠️ 你上传的是一个空文件，请检查！")
					st.stop()
			except pd.errors.ParserError:
				st.error("解析错误！请检查分隔符选择是否正确。")
				st.stop()
			
			except Exception as e:
				st.error(f"读取文件时发生错误: {str(e)}")
				st.stop()
		
		else:
			st.stop()
	else:
		# 直接根据路径读取为DataFrame
		assert isinstance(file_dir, str)
		assert isinstance(file_name, str)
		file_path = os.path.join(file_dir, file_name)
		encoding = detect_file_encoding(file_path)
		df = pd.read_csv(file_path,
		                 sep=selected_sep,
		                 header=0 if has_header else None,
		                 encoding=encoding)
	
	# 显示成功信息
	st.success("✅ 数据文件读取成功！")
	
	# 创建两列布局
	cols = st.columns([1, 4])
	
	with cols[0]:
		st.subheader("📋 数据概览")
		st.markdown(f"""
					- **文件名**: {file_name}
					- **数据形状**: {df.shape[0]} 行 × {df.shape[1]} 列
					- **分隔符**: {repr(selected_sep)}
					- **编码**: {encoding}
					""")
	
	# 显示数据类型
	# st.subheader("🔍 数据类型")
	# dtypes_df = pd.DataFrame({
	# 	'列名': df.columns,
	# 	'数据类型': df.dtypes.values
	# })
	# st.dataframe(dtypes_df, use_container_width=True)
	
	with cols[1]:
		st.subheader("🔍 数据预览（前5行）")
		st.dataframe(df.head(), use_container_width=True)
	
	# 显示统计信息
	st.subheader("📰 描述性数据结果")
	st.dataframe(df.describe(), use_container_width=True)
	
	return df, file_name, output_file_extension
