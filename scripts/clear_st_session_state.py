"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""

import streamlit as st


def clear_st_session_state() -> None:
	"""定义一个回调函数，用来清空计算结果，保证在重新选择执行的任务后需要重新点击计算按钮才出现结果"""
	st.session_state.pop('format_results_df', None)
	st.session_state.pop('data_processed', None)