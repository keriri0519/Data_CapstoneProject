"""COVID-19 case explorer. / COVID-19病例查询应用。

Run from this directory: streamlit run capstone.py
在本目录运行：streamlit run capstone.py
"""

# 中文：pandas读取和处理表格，Streamlit提供界面与图表。
# English: pandas reads and processes tables; Streamlit provides the interface and charts.
import pandas as pd
import streamlit as st

# 中文：直接读取老师指定的JHU全球确诊病例网址，不读取本地CSV或使用本地回退。
# English: Read the assigned JHU global confirmed-case URL directly, without local CSV input or fallback.
DATA_URL = (
    'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/'
    'csse_covid_19_data/csse_covid_19_time_series/'
    'time_series_covid19_confirmed_global.csv'
)

# 中文：用户同意将这些特殊统计条目移出主选择框，但在说明表保留。
# English: The user approved removing these special reporting entries from the main selector while retaining their notes.
SPECIAL_ENTRIES = {
    'Diamond Princess': 'Cruise ship',
    'MS Zaandam': 'Cruise ship',
    'Summer Olympics 2020': 'Sporting event',
    'Winter Olympics 2022': 'Sporting event',
    'Antarctica': 'Continent',
}

# 中文：只调整已约定的显示名称，内部匹配和统计仍使用源标签。
# English: Apply the agreed display label only; matching and aggregation retain the source label.
DISPLAY_NAMES = {'Taiwan*': 'China Taiwan'}


# 中文：这个短函数每次直接在线读取；不添加磁盘缓存或本地数据文件依赖。
# English: This short function reads online on each run, without disk caching or local data dependencies.
def load_covid_data():
    # 中文：read_csv直接接收HTTPS网址，返回原始宽表DataFrame。
    # English: read_csv accepts the HTTPS URL directly and returns the original wide DataFrame.
    covid_df = pd.read_csv(DATA_URL)

    # 中文：核对前四列布局，避免把地域信息误当病例或选错日期列。
    # English: Check the first four columns to avoid treating geographic fields as cases or selecting incorrect dates.
    expected_columns = ['Province/State', 'Country/Region', 'Lat', 'Long']
    if covid_df.empty or list(covid_df.columns[:4]) != expected_columns:
        raise ValueError('Unexpected source table structure.')

    # 中文：日期列从第五列开始；源日期格式为月/日/两位年份。
    # English: Date columns start at the fifth column and use month/day/two-digit-year labels.
    date_columns = covid_df.columns[4:]
    # 中文：按明确格式解析日期，无法解析时由调用方显示读取错误。
    # English: Parse the explicit date format; the caller displays an error if parsing fails.
    dates = pd.to_datetime(date_columns, format='%m/%d/%y')

    # 中文：需要至少两天且日期唯一、递增，才有明确的逐日差分顺序。
    # English: Require at least two unique, increasing dates for an unambiguous differencing order.
    if len(dates) < 2 or dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError('Source dates are missing, duplicated, or unordered.')

    # 中文：拒绝缺失的国家标签或病例值，不把未知数据自动填零。
    # English: Reject missing country labels or case values rather than automatically filling unknowns with zero.
    if covid_df['Country/Region'].isna().any() or covid_df[date_columns].isna().any().any():
        raise ValueError('The source contains missing labels or case values.')

    # 中文：负的累计值与负的每日差分不同；源累计值若为负应报告输入问题。
    # English: Negative cumulative values differ from negative daily changes; reject negative cumulative inputs.
    if (covid_df[date_columns] < 0).any().any():
        raise ValueError('The source contains negative cumulative values.')

    # 中文：返回已检查的在线表，不写入或覆盖任何原始文件。
    # English: Return the checked online table without writing or overwriting source files.
    return covid_df


# 中文：用基础国家筛选和求和取得时间序列，避免额外的宽长表转换。
# English: Use basic country filtering and summation without additional wide/long reshaping.
def country_cumulative(covid_df, country):
    # 中文：只选日期列，排除经纬度等非病例字段。
    # English: Select date columns only, excluding coordinates and other non-case fields.
    date_columns = covid_df.columns[4:]

    # 中文：选择国家全部省/州行，因此多地区国家不会遗漏其余行。
    # English: Select all province/state rows so multi-region countries do not lose rows.
    country_rows = covid_df.loc[covid_df['Country/Region'] == country, date_columns]

    # 中文：未知标签不能生成全零结果。
    # English: An unknown label must not produce an all-zero result.
    if country_rows.empty:
        raise ValueError('Country/region not found: ' + country)

    # 中文：axis=0沿行相加；min_count要求每个地区都有数值才返回合计。
    # English: axis=0 sums rows; min_count requires a value from every region before returning a total.
    cumulative_series = country_rows.sum(axis=0, min_count=len(country_rows))

    # 中文：日期转换为索引，绘图横轴使用真实日期而非字符串序号。
    # English: Convert date labels into an index so the chart uses real dates rather than string positions.
    cumulative_series.index = pd.to_datetime(date_columns, format='%m/%d/%y')

    # 中文：按时间排序后返回累计序列，不再次求累计和。
    # English: Sort chronologically and return cumulative counts without summing them cumulatively again.
    return cumulative_series.sort_index()


# 中文：为已选国家生成一列一个国家、索引为日期的图表数据。
# English: Build chart data with one column per selected country and dates as the index.
def build_chart_data(covid_df, countries, mode):
    # 中文：字典保存每个显示名称及其时间序列。
    # English: Store each display label and its time series in a dictionary.
    country_series = {}

    # 中文：逐国汇总，不把不同国家的病例相加。
    # English: Aggregate one country at a time without adding different countries together.
    for country in countries:
        # 中文：取得当前国家全部地区的累计合计。
        # English: Obtain cumulative totals across all regions for the current country.
        cumulative_series = country_cumulative(covid_df, country)

        # 中文：每日模式计算当天累计减前一天累计；第一天无前值，保留缺失。
        # English: Daily mode subtracts the preceding cumulative value; leave the first day missing because no baseline exists.
        if mode == 'Daily new cases':
            selected_series = cumulative_series.diff()
        else:
            # 中文：累计模式直接使用国家合计。
            # English: Cumulative mode uses the country totals directly.
            selected_series = cumulative_series

        # 中文：get在名称映射不存在时保留源标签，不修改源表。
        # English: get retains the source label when no display mapping exists, without changing the source table.
        display_name = DISPLAY_NAMES.get(country, country)
        # 中文：以显示名称保存当前模式的序列，作为图中的一个独立系列。
        # English: Save the selected-mode series under its display label as one independent chart series.
        country_series[display_name] = selected_series

    # 中文：按共同日期对齐各国家序列，并为横轴索引命名。
    # English: Align country series by their shared dates and name the index for the x-axis.
    chart_data = pd.DataFrame(country_series)
    # 中文：将日期索引命名为Date，供图表使用。
    # English: Name the date index Date for the chart.
    chart_data.index.name = 'Date'
    return chart_data


# 中文：构建源数据全部国家/地区的负差分清单；这些是待解释的记录，不自动判成错误。
# English: Build the negative-change list for all source countries/regions; these records need explanation and are not automatically errors.
def build_negative_changes(covid_df):
    # 中文：每条清单记录保存国家、日期、前后累计数和净变化。
    # English: Store the country, date, preceding/current cumulative counts, and net change for each record.
    records = []
    # 中文：遍历源表所有不同标签，清单涵盖整个来源而非仅当前选择。
    # English: Iterate through all distinct source labels so the list covers the full source, not only current selections.
    for country in covid_df['Country/Region'].unique():
        # 中文：对该标签的全部地区求累计合计。
        # English: Aggregate cumulative counts across all regions under this label.
        cumulative_series = country_cumulative(covid_df, country)
        # 中文：沿日期相减，得到报告净变化。
        # English: Difference consecutive dates to obtain net reporting changes.
        daily_series = cumulative_series.diff()

        # 中文：布尔筛选只保留小于零的差分，首日NaN不属于负值。
        # English: Keep differences below zero; the first-day NaN is not a negative value.
        negative_series = daily_series.loc[daily_series < 0]

        # 中文：items逐条提供日期及净变化，便于构建可核对的表格。
        # English: items provides each date and net change for a verifiable table.
        for date, change in negative_series.items():
            # 中文：按日期标签定位当日累计数。
            # English: Locate the current cumulative value by its date label.
            current_total = cumulative_series.loc[date]
            # 中文：由当日累计减净变化还原前日累计，便于检查两者差额。
            # English: Subtract the net change from the current total to reconstruct the previous total for reconciliation.
            previous_total = current_total - change

            # 中文：用整数展示真实计数；日期格式化为不易混淆的年-月-日。
            # English: Display actual counts as integers and dates in unambiguous year-month-day form.
            records.append({
                'Country / region': DISPLAY_NAMES.get(country, country),
                'Date': date.strftime('%Y-%m-%d'),
                'Previous cumulative': int(previous_total),
                'Current cumulative': int(current_total),
                'Daily net change': int(change),
            })

    # 中文：显式列名保证没有负记录时也返回结构一致的空表。
    # English: Explicit column names preserve the table structure even when no negatives exist.
    return pd.DataFrame(records, columns=[
        'Country / region', 'Date', 'Previous cumulative',
        'Current cumulative', 'Daily net change',
    ])


# 中文：界面按标题、使用说明、国家选择、模式和图表的顺序组织。
# English: Organize the interface as title, instructions, country selector, mode, and chart.
def main():
    # 中文：所有页面文字使用英文；注释保留逐处中英对照。
    # English: Keep all interface text in English and comments paired in Chinese and English.
    st.title('COVID-19 Cases')
    # 中文：页面上直接说明选择、比较和移除国家的操作。
    # English: Explain country selection, comparison, and removal directly on the page.
    st.write('Select one or more countries / regions, then switch between daily and cumulative reported cases. Add another selection to compare countries; use the × beside a selected name to remove it.')

    # 中文：读取失败时显示明确错误并结束本次显示，不使用本地CSV或遗留图表。
    # English: On loading failure, show a clear error and end this render without local CSV fallback or stale charts.
    try:
        covid_df = load_covid_data()
    except (OSError, ValueError, TypeError):
        st.error('The JHU data could not be loaded or validated. Check your internet connection and the source URL, then reload this page. No local data fallback is used.')
        st.write('[Open the source CSV](' + DATA_URL + ')')
        return

    # 中文：由源表实际日期生成范围提示，不把历史数据标成当前实时疫情。
    # English: Derive the date range from the source rather than presenting historical data as live information.
    dates = pd.to_datetime(covid_df.columns[4:], format='%m/%d/%y')
    st.write('Historical data: ' + dates[0].strftime('%Y-%m-%d') + ' to ' + dates[-1].strftime('%Y-%m-%d') + '. Source: [Johns Hopkins CSSE](' + DATA_URL + ').')

    # 中文：显示名称映射回源标签，排除用户确认的五项，保留其余源分组口径。
    # English: Map display labels back to source labels, exclude the five approved entries, and retain all other source groupings.
    country_options = {}
    # 中文：逐个检查来源中的不同国家/地区标签。
    # English: Check each distinct country/region label in the source.
    for country in covid_df['Country/Region'].unique():
        # 中文：只有不属于已确认五项排除列表的标签才进入选择框。
        # English: Include a label only when it is outside the five approved exclusions.
        if country not in SPECIAL_ENTRIES:
            # 中文：取得面向用户的显示名称；未映射的标签保持原名。
            # English: Obtain the display name, retaining unchanged labels when unmapped.
            display_name = DISPLAY_NAMES.get(country, country)
            # 中文：保存显示名称到源标签的对应关系。
            # English: Store the mapping from display name to source label.
            country_options[display_name] = country

    # 中文：将选项排序；default=[]落实“不预选国家”的要求。
    # English: Sort the options; default=[] implements the empty initial selection.
    selected_labels = st.multiselect('Countries / regions', sorted(country_options), default=[])

    # 中文：第一个选项为默认每日新增，radio允许随时切换累计模式。
    # English: The first option makes daily changes the default; radio allows switching to cumulative mode.
    mode = st.radio('Case count', ('Daily new cases', 'Cumulative cases'))

    # 中文：只有选择国家后才生成图表，空选择时只给操作提示。
    # English: Build the chart only after selection; otherwise show an instruction.
    if selected_labels:
        # 中文：建立当前所选国家的源标签列表。
        # English: Build the source-label list for the current country selection.
        selected_countries = []
        for label in selected_labels:
            # 中文：使用源标签筛选，显示名称不会破坏数据连接。
            # English: Filter with source labels so display names do not break data matching.
            selected_countries.append(country_options[label])

        # 中文：传入已选国家和当前模式，控件变化后按新选择重新计算。
        # English: Pass selected countries and mode so widget changes recompute the corresponding series.
        chart_data = build_chart_data(covid_df, selected_countries, mode)

        # 中文：原生折线图按日期索引绘制；轴名明确区分每日报告净变化与累计病例。
        # English: Use the native line chart with the date index and axis labels distinguishing daily net changes from cumulative cases.
        if mode == 'Daily new cases':
            st.line_chart(chart_data, x_label='Date', y_label='Reported cases: daily net change')
            st.write('Daily values are changes in reported cumulative counts, not infections occurring that day. Negative values indicate downward changes in the reported totals; no values are clipped. The first date has no daily value because the preceding total is unavailable.')
        else:
            st.line_chart(chart_data, x_label='Date', y_label='Cumulative reported cases')
    else:
        st.write('Choose at least one country / region above to display the chart.')

    # 中文：用课内checkbox按需显示用户要求的异常清单，避免始终铺开长表。
    # English: Use the course-taught checkbox to reveal the requested exception list without displaying a long table permanently.
    show_notes = st.checkbox('Show data notes and exceptions')
    if show_notes:
        st.subheader('Downward changes in cumulative reports')
        st.write('These records have data: the current cumulative total is lower than the preceding day. They may reflect corrections, reclassification, or other source changes. The specific cause of each record has not been individually verified. Negative cumulative counts and missing data are different issues.')

        # 中文：只有展开时才计算完整负值清单，不改变主图中的任何数值。
        # English: Calculate the full negative-change list only when requested, without changing chart values.
        negative_changes = build_negative_changes(covid_df)
        st.write('Records in the entire source dataset: ' + str(len(negative_changes)))
        st.write(negative_changes)

        # 中文：五个特殊条目仅从选择框移出，源行并没有删除、改名或合并给其他国家。
        # English: Remove the five special entries only from the selector; do not delete, rename, or reassign their source rows.
        st.subheader('Special source entries excluded from the selector')
        # 中文：用普通列表逐条收集五个特殊条目的说明。
        # English: Collect the five special-entry descriptions in a plain list.
        special_rows = []
        # 中文：items同时取得每个源名称及其条目类型。
        # English: items returns each source name together with its entry type.
        for entry, entry_type in SPECIAL_ENTRIES.items():
            # 中文：说明只从选择框排除，不改动来源记录。
            # English: Document selector-only exclusion without changing source records.
            special_rows.append({'Source entry': entry, 'Type': entry_type, 'Treatment': 'Excluded from country selector; source unchanged'})
        # 中文：把说明列表转成表格显示。
        # English: Display the description list as a table.
        st.write(pd.DataFrame(special_rows))
        st.write('Country / region totals follow the source labels and include all province / state rows under each label. The Confirmed field includes probable cases where the source reports them. A zero daily change can reflect no change in reporting, rather than proof of no new infections. No preceding observation is available for the first date.')


# 中文：直接运行时显示界面；导入进行独立计算检查时不启动页面。
# English: Display the app when run directly; imports for independent checks do not start the interface.
if __name__ == '__main__':
    main()
