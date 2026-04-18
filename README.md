# MSDA7103 NLP Group Project

本仓库包含政治演讲原始语料、文本预处理脚本、词典法分析脚本，以及两套已经整理好的中间结果与图表结果。

## 当前项目结构

| 路径 | 内容 |
|------|------|
| `original_ data/` | 原始演讲文档，主要为 `.docx`。 |
| `Code/01_processing/` | 语料整理与预处理脚本。 |
| `Code/02_dictionary method/` | 词典打分与可视化脚本。 |
| `dict/` | 词典 CSV 文件。当前包含 `crime_gt`、`economy_gt`、`elites_gt`、`people_gt`、`service_gt`、`violence_gt`、`war_gt`、`we_gt`、`they_gt`。 |
| `processed_data/no_stopwords/` | 去除 stopwords 后的预处理文本与对应汇总表。 |
| `processed_data/with_stopwords/` | 保留 stopwords 的预处理文本与对应汇总表。 |
| `result/dictionary_method_results_no_stop_words/` | 基于 `processed_data/no_stopwords/processed_data_output.xlsx` 的词典法结果。 |
| `result/dictionary_method_results_with_stopwords/` | 基于 `processed_data/with_stopwords/processed_data_output.xlsx` 的词典法结果。 |
| `Literature/` | 参考文献与课程资料。 |

## 脚本说明

### `Code/01_processing/`

| 脚本 | 作用 |
|------|------|
| `a_rename_documents.py` | 将原始文件名中的下划线改为空格。 |
| `b_standardized_naming.py` | 将原始文件统一改为 `{YYYY}{letter} {Speaker} {Month}` 格式。 |
| `c_data_preprocessing.py` | 文本预处理版本 1：小写、去 URL、去标点、去数字、去 stopwords、异常长度过滤、lemmatization。 |
| `c1_data_preprocessing.py` | 文本预处理版本 2：流程与上面相同，但不移除 stopwords。 |
| `e_fix_name.py` | 按同一候选人在同一年内的时间顺序，重新校正文件名里的字母序号。 |
| `d_output_result.py` | 将一批 `.txt` 汇总为 `processed_data_output.xlsx/.csv`。 |

### `Code/02_dictionary method/`

| 脚本 | 作用 |
|------|------|
| `a_dicscore_calc.py` | 对每篇 speech 计算各词典分数，并把结果写回对应的 `processed_data_output.xlsx`。其中 `we_gt` 和 `they_gt` 直接从原始文档读取，避免受 stopword removal 影响。 |
| `b_dic_result.py` | 输出 cycle mean comparison、election-year comparison、monthly score CSV、各词典时序图、柱状图，以及 `they/we ratio` 时序图。 |

## 推荐运行顺序

如果要从原始语料重新生成一套数据，建议按下面顺序执行：

1. `a_rename_documents.py`
2. `b_standardized_naming.py`
3. 二选一：
   - `c_data_preprocessing.py` 生成“去 stopwords”版本
   - `c1_data_preprocessing.py` 生成“保留 stopwords”版本
4. `e_fix_name.py`
5. `d_output_result.py`
6. `a_dicscore_calc.py`
7. `b_dic_result.py`

## 当前两套数据流

### 1. `no_stopwords`

- 文本目录：`processed_data/no_stopwords/`
- 汇总表：`processed_data/no_stopwords/processed_data_output.xlsx`
- 分析结果：`result/dictionary_method_results_no_stop_words/`

### 2. `with_stopwords`

- 文本目录：`processed_data/with_stopwords/`
- 汇总表：`processed_data/with_stopwords/processed_data_output.xlsx`
- 分析结果：`result/dictionary_method_results_with_stopwords/`

## 汇总表字段

`processed_data_output.xlsx` 与 `processed_data_output.csv` 的基础列如下：

| 列名 | 含义 |
|------|------|
| `Speaker` | 演讲人，如 `Trump`、`Clinton`、`Biden`、`Harris`。 |
| `Year` | 演讲年份。 |
| `SpeechIndex` | 该演讲人在该年份中的序号，`a=1`、`b=2`、以此类推。 |
| `Month` | 月份英文三字母缩写，如 `Jan`、`Feb`。 |
| `Text` | 预处理后的正文。 |
| `SlidingWindow2gram` | 基于 `Text` 生成的相邻 2-gram，使用分号连接。 |

运行 `a_dicscore_calc.py` 后，还会新增以下列：

- `crime_gt_score`
- `economy_gt_score`
- `elites_gt_score`
- `people_gt_score`
- `service_gt_score`
- `they_gt_score`
- `violence_gt_score`
- `war_gt_score`
- `we_gt_score`

## 结果文件夹里有什么

每个 `dictionary_method_results_*` 文件夹目前都包含：

- `cycle_mean_comparison.csv`
- `election_year_mean_comparison.csv`
- `2015_2016_monthly_scores.csv`
- `2019_2020_monthly_scores.csv`
- `2023_2024_monthly_scores.csv`
- `full_timeline_monthly_scores.csv`
- `full_timeline_they_we_ratio.csv`
- `trend_plots/`
- `bar_charts/`

其中：

- `trend_plots/` 包含每个 dictionary score 的全时间线时序图，以及 `they_we_ratio__full_timeline_trend.png`
- `bar_charts/` 包含各词典在选举年的均值柱状图

## 常用运行命令

下面命令更符合当前仓库结构，因为当前项目把两套文本和结果分开放置了。

### 生成去 stopwords 版本

```bash
python Code/01_processing/c_data_preprocessing.py --output-dir processed_data/no_stopwords
python Code/01_processing/e_fix_name.py processed_data/no_stopwords
python Code/01_processing/d_output_result.py --input-dir processed_data/no_stopwords --xlsx processed_data/no_stopwords/processed_data_output.xlsx --csv processed_data/no_stopwords/processed_data_output.csv
python "Code/02_dictionary method/a_dicscore_calc.py" --xlsx processed_data/no_stopwords/processed_data_output.xlsx
python "Code/02_dictionary method/b_dic_result.py" --xlsx processed_data/no_stopwords/processed_data_output.xlsx --output-dir result/dictionary_method_results_no_stop_words
```

### 生成保留 stopwords 版本

```bash
python Code/01_processing/c1_data_preprocessing.py --output-dir processed_data/with_stopwords
python Code/01_processing/e_fix_name.py processed_data/with_stopwords
python Code/01_processing/d_output_result.py --input-dir processed_data/with_stopwords --xlsx processed_data/with_stopwords/processed_data_output.xlsx --csv processed_data/with_stopwords/processed_data_output.csv
python "Code/02_dictionary method/a_dicscore_calc.py" --xlsx processed_data/with_stopwords/processed_data_output.xlsx
python "Code/02_dictionary method/b_dic_result.py" --xlsx processed_data/with_stopwords/processed_data_output.xlsx --output-dir result/dictionary_method_results_with_stopwords
```

## 依赖

建议安装以下 Python 包：

```bash
pip install pandas openpyxl matplotlib numpy python-docx nltk
```

`nltk` 所需语料会在相关脚本首次运行时自动下载。
