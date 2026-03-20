"""
This Script is Supported by Department of Geriatrics and National Clinical Research Center for Geriatrics,
West China Hospital, Sichuan University.
"""


def process_p_value(
		p_value: float,
		p_decimal_places: int,
		if_simple_p_format: bool,
		if_star_symbol: bool
) -> str:
	"""
	传入p_value浮点数，返回处理后的精确到特定小数点位数和带*号数量的p_value字符串
	
	Args:
		p_value: p_value浮点数
		p_decimal_places: P值精确到小数点后多少位
		if_simple_p_format: 是否去掉P值小数点前面的0
		if_star_symbol: 是否根据不同显著性水平在P值后面添加对应数量的*号
		
	Returns:
		处理后的p_value字符串
	"""
	
	if round(p_value, p_decimal_places) == 0:
		p_value_str = '<0.' + '0' * (p_decimal_places - 1) + '1'
		if if_star_symbol:
			p_value_str += "*" * 3
	else:
		star_symbol_num = 0
		if if_star_symbol:
			if p_value < 0.01:
				star_symbol_num = 2
			elif p_value < 0.05:
				star_symbol_num = 1
		p_value_str = f"{p_value:.{p_decimal_places}f}" + "*" * star_symbol_num
	
	if if_simple_p_format:
		p_value_str = p_value_str.replace("0.", ".", 1)
	
	return p_value_str
