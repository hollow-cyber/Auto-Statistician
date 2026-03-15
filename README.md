# Auto-Statistician (自动统计分析专家) 📊🏥

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: Non-Commercial](https://img.shields.io/badge/License-Non_Commercial-red.svg)](#)

**Auto-Statistician** 是一款专为临床医学研究和科研人员打造的**自动统计分析 Web UI 工具**。只需导入数据，程序即可自动识别变量类型、执行正态性检验、智能选择对应的统计学检验方法，并一键生成符合学术期刊发表标准的“基线特征表（Table 1）”或生存分析结果。

> 💡 **背景与致谢**：本项目受到 **四川大学华西医院、国家老年疾病临床医学研究中心** 的支持。程序仅供科研与学习使用，**请勿商用**。

---

## ✨ 核心特性 (Key Features)

### 1. 🤖 智能统计检验 (Smart Statistical Testing)
*   **连续变量**：自动进行 Shapiro-Wilk / KS 正态性检验。根据数据分布和组别数量，智能切换 **Student's t-test、Mann-Whitney U 检验、ANOVA 或 Kruskal-Wallis 检验**。
*   **分类变量**：自动计算频数与比例。内置期望频数检查，智能在 **Pearson卡方检验** 和 **Fisher精确检验** 之间无缝切换。
*   **生存分析**：自动进行单因素生存分析筛选。根据分类变量的类别数，智能选择 **Log-rank 检验**（≤5个类别）或 **单因素 Cox 比例风险模型**（>5个类别或连续变量），并自动计算 HR 及 95% CI。

### 2. 📑 一键生成期刊级图表 (Publication-Ready Tables)
*   支持高度自定义的描述性统计格式（如 `N(%)` 或 `N(ratio)`，`mean±std`，`Q2(Q1, Q3)` 等）。
*   可根据不同显著性水平自动在 P 值后标记星号（`*`、`**`、`***`）。
*   结果可一键下载为纯文本（`.txt`），方便直接粘贴入 Excel 或 Word。

### 3. ✍️ 自动撰写方法学 (Auto-generate Methods Section)
*   分析完成后，程序会根据实际执行的检验方法，**自动生成中英双语的“统计分析方法（Statistical Methods）”段落**，你可以直接复制到你的 SCI 论文或中文核心期刊中。

### 4. 🧹 数据预处理 (Data Preprocessing)
*   **缺失值处理**：支持删除包含空值的行/列，或使用均值、中位数、众数、随机数、常数进行简单插补。还支持**按同类别样本特征分组进行缺失值插补**。

---

## 🚀 安装与运行 (Installation & Usage)

### 1. 环境准备
确保你的计算机上已安装 Python 3.8 或更高版本。

### 2. 克隆仓库
```bash
git clone https://github.com/hollow-cyber/Auto-Statistician.git
cd Auto-Statistician
```

### 3. 安装依赖库
建议在虚拟环境（如 venv 或 conda）中安装以下依赖：
```bash
pip install pandas numpy scipy lifelines streamlit chardet
```

### 4. 启动程序
在项目根目录下运行以下命令启动 Web UI：
```bash
streamlit run 自动统计分析专家v1.0-webUI.py
```
*(运行后，浏览器会自动打开 `http://localhost:8501`)*

---

## 📖 快速使用指南 (Quick Start Guide)

1. **导入数据**：在左侧边栏选择上传 `.txt` 或 `.csv` 文件，设定好数据分隔符（逗号、制表符等）。
2. **处理缺失值**：程序会自动检测缺失值。你可以在左侧边栏开启“简单处理原数据集中的缺失值”进行预处理。
3. **设置分析参数**：
   * 选择操作类型：“📊 分类结局变量单因素分析” 或 “📉 生存分析数据单因素分析”。
   * 指定**结局变量**（因变量）和**生存时间变量**（如适用）。
   * 排除不需要分析的变量（如患者ID）。
4. **自定义输出格式**：设置分类变量、正态/非正态分布变量在表格中的呈现格式（如 `mean±std`）。
5. **开始分析**：点击“开始统计分析”按钮，预览格式化结果表。
6. **导出与撰写**：点击下载结果文件，并展开下方的“📄 统计分析方法学中英文介绍内容”复制到你的手稿中。

---

## 🛠️ 技术栈 (Tech Stack)

* **前端交互**: [Streamlit](https://streamlit.io/)
* **数据处理**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
* **统计计算**: [SciPy](https://scipy.org/) (常规统计检验), [Lifelines](https://lifelines.readthedocs.io/) (生存分析)
* **编码检测**: [Chardet](https://pypi.org/project/chardet/)

---

## ✉️ 反馈与支持 (Support)

本程序受到四川大学华西医院、国家老年疾病临床医学研究中心的支持。
如果您在使用过程中遇到任何 Bug，或有新的功能建议，欢迎提交 Issue。

---
*✨ "阿伟你又在连夜搞科研喔。休息一下吧，去收个病人好不好？"* 🧐
