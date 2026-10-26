# COVID-19 Cases

An individual Python/Streamlit coursework app using the assigned Johns Hopkins CSSE time series. The app interface is in English; key source-code operations have paired Chinese and English comments.

这是使用指定JHU CSSE时间序列的个人Python/Streamlit课程应用。界面使用英文，关键源码操作逐处配有中英文注释。

## Run / 运行

Use Python 3.12 with the dependencies listed in `requirements.txt`. Validation used Python 3.12.14, pandas 2.3.3, and Streamlit 1.55.0. Install dependencies into your chosen environment only if needed; the commands below are instructions, not a claim that a new environment was installed.

使用Python 3.12和`requirements.txt`中的依赖。实际核验环境为Python 3.12.14、pandas 2.3.3、Streamlit 1.55.0。只有需要时才在选定环境安装依赖；以下是运行说明，不表示本次安装过新环境。

```text
python -m pip install -r requirements.txt
python -m streamlit run capstone.py
```

Run from the folder containing `capstone.py` and `.streamlit/` so the dark-theme configuration is loaded. Stop the local server with Ctrl+C in its terminal.

在同时包含`capstone.py`和`.streamlit/`的目录中运行，才能读取深色主题配置。在启动终端按Ctrl+C停止本机服务。

In the existing `D:\AI_Workspace` development workspace, `scripts/run_local.ps1` reuses packages already present under Data_Week08 and Data_Week07. It does not install packages or change the system PATH. That helper is specific to this workspace; it is not required for another computer or the submission ZIP.

当前`D:\AI_Workspace`开发环境可用`scripts/run_local.ps1`复用Data_Week08和Data_Week07已有依赖，不安装软件或修改系统PATH。该辅助脚本仅供此工作区使用，其他电脑或提交ZIP不依赖它。

## Use / 使用

1. Select one or more entries in **Countries / regions**. Nothing is preselected. Add another country to compare it; click the × next to a selected name to remove it.

   在**Countries / regions**下拉框选择一个或多个国家/地区，初始不预选。增加国家即可比较；点击已选名称旁的×移除。

2. **Daily new cases** is the default mode. Switch to **Cumulative cases** to view the source cumulative totals. The chart updates after each selection.

   默认模式为**Daily new cases**，可切换**Cumulative cases**查看源累计数。每次选择变化后图表重新计算。

3. Check **Show data notes and exceptions** to inspect all downward cumulative changes, the five excluded special entries, and interpretation notes. This is a reporting-quality list, not an assertion that every flagged record is erroneous.

   勾选**Show data notes and exceptions**查看累计下调记录、五个排除的特殊条目和解释说明。这是报告质量说明清单，不表示每条标记都是错误数据。

## Data and definitions / 数据与口径

The app reads this CSV **directly from its URL** on every run:

应用每次运行均**直接从以下网址**读取CSV：

[JHU global confirmed-case time series](https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv)

No local CSV, bundled dataset, disk cache, or offline fallback is used. An internet connection is required. If online loading or input checks fail, the app displays an error rather than a chart. The earlier `input/` snapshot is retained separately for provenance and is neither read by the app nor included in its ZIP.

不使用本地CSV、内置数据、磁盘缓存或离线回退，需要联网。在线读取或输入核验失败时显示错误，不展示图表。此前`input/`中的快照仅保留来源记录用途，应用不会读取，ZIP也不会包含它。

The inspected dataset has 289 rows, 1,143 dates from 2020-01-22 through 2023-03-09, and 201 source country/region labels. Five special entries are excluded from the main selector, leaving 196 selectable labels: Diamond Princess, MS Zaandam, Summer Olympics 2020, Winter Olympics 2022, and Antarctica. Source rows are not deleted or reassigned. Country/region aggregation follows JHU labels, including all province/state rows within each label. The agreed `China Taiwan` display label maps to the unchanged source matching key.

本次数据核验为289行，1143个日期，覆盖2020-01-22至2023-03-09，共201个源国家/地区标签。主选择框排除Diamond Princess、MS Zaandam、Summer Olympics 2020、Winter Olympics 2022和Antarctica，剩196项。源行不删除或转加给其他国家。国家/地区按JHU源标签分组，包含该标签下所有省/州行。约定的`China Taiwan`仅作显示名称，内部匹配键保持源值。

Daily values equal the current cumulative total minus the preceding day's total. The first daily value is undefined because the source has no preceding-day baseline. Negative daily changes are preserved: the inspected source has 171 such country-date records and no negative cumulative values. A downward adjustment may reflect revisions, reclassification, or other source changes; individual causes have not all been verified. A zero daily difference can also reflect no reporting update, rather than proof of no new infections. The source Confirmed field includes probable cases where reported.

每日值为当日累计减前日累计。首日无前日基线，因此每日值不可计算。负差分保留原样：本次源表有171个国家-日期负差分，累计病例值本身没有负数。下调可能源于修订、分类调整或其他来源变化，未逐一验证各条原因。零差分也可能只是报告未更新，不代表当天一定没有新感染。来源Confirmed字段在有报告时包含probable cases。

References / 参考： [JHU data documentation](https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/README.md), [time-series documentation](https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series).

## Deployment and submission scope / 部署与交付边界

The intended host is **Posit Connect Cloud**, chosen by the user. The portable application needs `capstone.py`, `requirements.txt`, and `.streamlit/config.toml`. Publish from a repository or a supported Posit publishing workflow, using `capstone.py` as the primary file. A requirements file provides dependencies. Localhost is a local preview, not the running public application link required for the eventual submission.

用户已选择**Posit Connect Cloud**。可移植应用需要`capstone.py`、`requirements.txt`和`.streamlit/config.toml`，通过仓库或Posit支持的流程发布，以`capstone.py`为入口，依赖由requirements文件提供。localhost只是本地预览，不能作为最终要求的公开运行链接。

See the [official Posit Streamlit publishing guide](https://docs.posit.co/connect-cloud/how-to/python/streamlit.html). Account access and the repository/publication choices still require user participation. No public deployment or public URL is claimed until publishing succeeds.

参见[Posit官方Streamlit发布教程](https://docs.posit.co/connect-cloud/how-to/python/streamlit.html)。账号操作和仓库/发布选择仍需用户参与；成功发布前不声称已有公开部署或公开链接。

The presentation and `capstone.docx` are deliberately deferred at the user's request. The code ZIP is the application component, not a complete final-project submission.

按用户要求，演示与`capstone.docx`暂缓，后续一起制作。代码ZIP仅为应用部分，不表示整个final project已经可以完整提交。
