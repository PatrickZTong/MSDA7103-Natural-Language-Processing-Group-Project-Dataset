# MSDA7103 NLP Group Project — Dataset & Preprocessing

本仓库收录政治演讲相关语料、预处理脚本，以及由脚本生成的纯文本与汇总表。

## 目录说明

| 路径 | 内容 |
|------|------|
| **`original_ data/`** | 原始 **Word（`.docx`）** 文稿，按演讲者与时间命名；Harris 部分文件名为「年份代号 + Harris + 月份」形式。 |
| **`processed_data/`** | 经 `c_data_preprocessing.py` 清洗后的 **纯文本（`.txt`）**，与源文件**同名主文件名**（扩展名为 `.txt`）。默认还在此目录输出汇总表 **`processed_data_outpout.xlsx`** 与 **`processed_data_outpout.csv`**（由 `d_output_result.py` 生成）。 |
| **`Code/01_preprocessing/`** | 预处理与导出脚本（按建议顺序）：`a_rename_documents.py`（下划线改空格）、`b_standardized_naming.py`（文件名规则化）、`c_data_preprocessing.py`（正文清洗与词形还原）、`d_output_result.py`（汇总为表格）。 |
| **`Literature/`** | 课程/项目相关参考文献（如 PDF）。 |

> 说明：根目录下若仍有旧版 `processed_data_outpout.*`，可能是改输出路径前的遗留文件，以 **`processed_data/`** 内版本为准。

## 汇总表：`processed_data_outpout.xlsx` 与 `processed_data_outpout.csv`

两份表**列结构完全相同**，仅格式不同（Excel / CSV，CSV 为 UTF-8 带 BOM，便于 Excel 打开）。

| 列名（英文） | 含义 |
|--------------|------|
| **Speaker** | 演讲人（如 Biden、Trump、Clinton、Harris）。 |
| **Year** | 演讲所属年份（四位数字，来自标准化文件名）。 |
| **SpeechIndex** | **该自然年内**的演讲序号：由文件名中紧挨年份后的**小写字母**推导，`a`=1，`b`=2，…，`z`=26。 |
| **Month** | 月份（三字母英文缩写，如 Jan、Feb）。 |
| **Text** | 预处理后的**正文**：小写、去 URL/标点/数字、去停用词、按文档平均词长过滤异常长度词、词形还原（lemmatization）后的空格分词串。 |
| **SlidingWindow2gram** | 对 **Text** 按空白分词后做**相邻滑动二元组**（2-gram），形式为 `词1 词2;词2 词3;…`（分号分隔）。 |

生成方式：在仓库根目录执行（需已安装 `pandas`、`openpyxl`）：

```bash
python Code/01_preprocessing/d_output_result.py
```

默认从 `processed_data/*.txt` 读取，并将两张表写入 **`processed_data/processed_data_outpout.xlsx`** 与 **`processed_data/processed_data_outpout.csv`**。
