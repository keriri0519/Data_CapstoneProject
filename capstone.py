##COVID-19 case explorer

import pandas as pd
import streamlit as st

DATA_URL = ('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')

#special reporting entries
SPECIAL_ENTRIES = {
    'Diamond Princess': 'Cruise ship',
    'MS Zaandam': 'Cruise ship',
    'Summer Olympics 2020': 'Sporting event',
    'Winter Olympics 2022': 'Sporting event',
    'Antarctica': 'Continent',
}


##reads online on each run
def load_covid_data():
    covid_df = pd.read_csv(DATA_URL)

    #check the first columns
    expected_columns = [
        'Province/State', 
        'Country/Region', 
        'Lat', 
        'Long'
        ]
    date_columns = covid_df.columns[4:]



    ##Validation check
    #check the sturcture
    if covid_df.empty or list(covid_df.columns[:4]) != expected_columns:
        raise ValueError('Unexpected source table structure.')

    #check the dates
    dates = pd.to_datetime(date_columns, format='%m/%d/%y')
    if len(dates) < 2:
        raise ValueError('At least two dates are required.')    
    # starting from the second date, compare each date with preceding.
    for i in range(1, len(dates)):
        if dates[i] <= dates[i - 1]:
            raise ValueError('Source dates are unordered.')

    #check missing country labels
    if covid_df['Country/Region'].isna().any() or covid_df[date_columns].isna().any().any():
        raise ValueError('The source contains missing labels or case values.')

    #check negative cumulative values
    if (covid_df[date_columns] < 0).any().any():
        raise ValueError('The source contains negative cumulative values.')



    #pass all the checkpoint
    covid_df['Country/Region'] = covid_df['Country/Region'].replace({'Taiwan*': 'China Taiwan'})
    return covid_df




#use basic country filtering and summation
def country_cumulative(covid_df, country):
    date_columns = covid_df.columns[4:]
    country_rows = covid_df.loc[covid_df['Country/Region'] == country, date_columns]

    if country_rows.empty:
        raise ValueError('Country/region not found: ' + country)

    #sum rows to retrun a total
    cumulative_series = country_rows.sum(axis=0, min_count=len(country_rows))

    cumulative_series.index = pd.to_datetime(date_columns, format='%m/%d/%y')
    return cumulative_series.sort_index()




##build chart data with one column/selected country and dates as index
def build_chart_data(covid_df, countries, mode):
    country_series = {}

    for country in countries:
        cumulative_series = country_cumulative(covid_df, country)

        #Daily mode: substrates the preceding cumulative value, leave the first dat missing
        if mode == 'Daily new cases':
            selected_series = cumulative_series.diff()
        else:
            selected_series = cumulative_series

        country_series[country] = selected_series

    #align country series by shared dates and name the index for xaxis
    chart_data = pd.DataFrame(country_series)
    return chart_data




##build negative-change list
def build_negative_changes(covid_df):
    records = []

    for country in covid_df['Country/Region'].unique():
        cumulative_series = country_cumulative(covid_df, country)
        daily_series = cumulative_series.diff()

        #keep differences below 0
        negative_series = daily_series.loc[daily_series < 0]

        for date, change in negative_series.items():
            current_total = cumulative_series.loc[date]
            previous_total = current_total - change
            #display actual counts as int and dates
            records.append(
                {
                    'Country / region': country,
                    'Date': date.strftime('%Y-%m-%d'),
                    'Previous cumulative': int(previous_total),
                    'Current cumulative': int(current_total),
                    'Daily net change': int(change),
                }
            )

    return pd.DataFrame(
        records, 
        columns = 
        [
        'Country / region', 'Date', 'Previous cumulative',
        'Current cumulative', 'Daily net change',
        ]
    )




##Organization: title, instructions, country selector, mode and chart
def main():
    st.set_page_config(
        page_title = 'COVID-19 Cases',
        layout = 'wide'
    )

    st.markdown(
        """
        <style>
        .stApp,
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp p,
        .stApp label,
        .stApp input,
        .stApp button,
        [data-testid="stMultiSelect"] {
            font-family: "Times New Roman", Times, serif;
            color: #000080;
        }

        .block-container {
            max-width: 1080px;
            padding-top: 4.5rem;
            padding-bottom: 3rem;
        }

        .lake-header {
            border-bottom: 3px solid #B0C4DE;
            padding: 0.8rem 1rem 1.8rem;
            margin-bottom: 0.5rem;
            text-align: center;
        }

        .lake-header h1 {
            color: #000080;
            font-size: 2.5rem;
            font-weight: 600;
            line-height: 1.2;
            margin: 0 0 1rem;
            padding: 0;
        }

        .lake-header p {
            color: #000080;
            font-size: 1.05rem;
            line-height: 1.6;
            max-width: 680px;
            margin: 0 auto;
        }

        .st-key-controls {
            background-color: #FFFFFF;
            border-radius: 12px;
        }

        .lake-empty {
            background-color: #FFFFFF;
            border: 1px solid #B0C4DE;
            border-top: 3px solid #87CEEB;
            border-radius: 10px;
            min-height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 1.5rem;
            margin: 0.6rem 0;
        }

        .lake-empty h3 {
            color: #000080;
            font-size: 1.25rem;
            font-weight: 400;
            margin: 0 0 0.5rem;
            padding: 0;
        }

        .lake-empty p {
            color: #000080;
            font-size: 1rem;
            margin: 0;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-top: 2.5rem;
            }

            .lake-header h1 {
                font-size: 2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html = True
    )

    st.markdown(
        """
        <div class="lake-header">
            <h1>COVID-19 Cases</h1>
            <p>
                Compare historical daily and cumulative reported cases across countries and regions.
            </p>
        </div>
        """,
        unsafe_allow_html = True
    )

    #loading failure
    try:
        covid_df = load_covid_data()
    except (OSError, ValueError, TypeError):
        st.error('The data could not be loaded or validated. Check your internet connection and the source URL, then reload this page. No local data fallback is used.')
        st.write('[Open the source CSV](' + DATA_URL + ')')
        return

    #derive the date range from the source
    dates = pd.to_datetime(covid_df.columns[4:], format = '%m/%d/%y')
    st.caption(
        'Historical data: ' +
        dates[0].strftime('%Y-%m-%d') +
        ' to ' + dates[-1].strftime('%Y-%m-%d') +
        '. Source: [Original dataset](' + DATA_URL + ').'
    )

    #build options
    country_options = []
    for country in covid_df['Country/Region'].unique():
        if country not in SPECIAL_ENTRIES:
            country_options.append(country)

    #Create two columns, giving more width to country selection.
    with st.container(border = True, key = 'controls'):
        country_column, mode_column = st.columns(
            [2, 1],
            gap = 'large'
        )

        selected_countries = country_column.multiselect(
            'Countries / regions',
            sorted(country_options),
            default = [],
            placeholder = 'Select countries to compare'
        )

        mode = mode_column.radio(
            'Case count',
            ('Daily new cases', 'Cumulative cases'),
            horizontal = True
        )


    #build the chart
    if selected_countries:
        chart_data = build_chart_data(
            covid_df, 
            selected_countries, 
            mode
            )

        #use native line chart with the date index, axis labels distinguishing daily net changes from cumulative cases
        if mode == 'Daily new cases':
                st.line_chart(
                    chart_data, 
                    x_label = 'Date', 
                    y_label = 'Reported cases: daily net change'
                    )
                st.caption('Daily values are changes in reported cumulative counts, not infections occurring that day. Negative values indicate downward changes in the reported totals; no values are clipped. The first date has no daily value because the preceding total is unavailable.')
        else:
            st.line_chart(
                chart_data, 
                x_label = 'Date', 
                y_label = 'Cumulative reported cases'
                )
    else:

        st.markdown(
            """
            <div class="lake-empty">
            <h3>Select countries to explore the data</h3>
            <p>Add countries above to compare their reported case trends.</p>
            </div>
            """,
            unsafe_allow_html = True
        )


    #exception list:
    show_notes = st.checkbox('Show data notes and exceptions')
    if show_notes:
        st.markdown('#### Downward changes in cumulative reports')
        st.caption('These records have data: the current cumulative total is lower than the preceding day. They may reflect corrections, reclassification, or other source changes. The specific cause of each record has not been individually verified. Negative cumulative counts and missing data are different issues.')

        negative_changes = build_negative_changes(covid_df)
        st.write('Records in the entire source dataset: ' + str(len(negative_changes)))
        st.write(negative_changes)

        #remove the five special entries only
        #donot delete, or reassign source rows
        st.markdown('#### Special source entries excluded from the selector')
        st.caption(
            'These five entries are excluded from the country selector. '
            'Their original source records remain unchanged.'
        )
        special_rows = []
        for entry, entry_type in SPECIAL_ENTRIES.items():
             special_rows.append(
                {
                    'Source entry': entry, 
                    'Type': entry_type
                    }
                )

        st.write(pd.DataFrame(special_rows))
        st.caption('Country / region totals follow the source labels and include all province / state rows under each label. The Confirmed field includes probable cases where the source reports them. A zero daily change can reflect no change in reporting, rather than proof of no new infections. No preceding observation is available for the first date.')



#display the app when run directly. imports for independenct checks
if __name__ == '__main__':
    main()
