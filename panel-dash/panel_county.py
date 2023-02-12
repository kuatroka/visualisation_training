#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import altair as alt
import panel as pn


# In[2]:


# standardizing state and county column names

apple_counties = pd.read_csv('data/apple_clean_counties.csv', parse_dates = ['date'])
google_counties = pd.read_csv('data/google_clean_counties.csv', parse_dates = ['date'])

apple_counties['state'] = apple_counties['sub_region']
apple_counties['county'] = apple_counties['region']

google_counties['state'] = google_counties['sub_region_1']
google_counties['county'] = google_counties['sub_region_2']

state_county_combinations = []
for i in list(zip(apple_counties.state, apple_counties.county)):
    state_county_combinations.append(', '.join(i))

state_county_combinations = set(state_county_combinations)   

case_data = pd.read_csv('data/jhu-case-data.csv', parse_dates= ['date'])


# In[3]:


state_input = pn.widgets.AutocompleteInput(name = 'Select a state, county',
                                        options = list(state_county_combinations),
                                       placeholder = 'ex: Maryland, Calvert County',
                                          value = 'Maryland, Calvert County')

@pn.depends(state_input.param.value)
def state_county_plot(state_input):
    state, county = state_input.split(', ')

    apple_to_plot_sc = apple_counties[(apple_counties.state == state) & (apple_counties.county == county)]
    google_to_plot_sc = google_counties[(google_counties.state == state) & (google_counties.county == county)]

    apple_to_plot_sc = apple_to_plot_sc.melt(
        id_vars='date',
        value_vars = ['driving', 'transit', 'walking'],
        var_name = 'type',
        value_name = 'volume'
    )

    google_cols_to_melt_sc = google_to_plot_sc.columns[4:]
    google_to_plot_sc = google_to_plot_sc.melt(
        id_vars = 'date',
        value_vars = google_cols_to_melt_sc,
        var_name = 'type',
        value_name = 'volume'
    )


    brush = alt.selection_interval(encodings=['x'])

    color = alt.condition(brush,
                          alt.Color('type:Q', legend=None),
                          alt.value('lightgray'))


    apple_sc = apple = alt.Chart(apple_to_plot_sc).mark_line().encode(
        x = 'date:T',
        y = 'volume:Q',
        color = 'type:N'
    ).add_selection(brush).properties(title = 'Apple mobility data')

    google_sc = google = alt.Chart(google_to_plot_sc).mark_line().encode(
        x = alt.X('date:T', scale = alt.Scale(domain = brush)),
        y = 'volume:Q',
        color = 'type:N'
    ).properties(title = 'Google mobility data')
    
    subtitle = f"### Mobility and case data for {state}, {county}"
    
    
    county_to_plot = pd.DataFrame(
        case_data[(case_data.Province_State == state) & (case_data.Admin2 == county.split()[0])]
    )
    county_to_plot['new_cases'] = county_to_plot['cases'].rolling(window=2).apply(lambda x: x[1] - x[0], raw = True)
    
    
    county_cum_cases = alt.Chart(county_to_plot).mark_line().encode(
        x = alt.X('date:T', scale = alt.Scale(domain = brush), title = 'Cumulative Cases'),
        y = 'cases:Q'
    ).properties(
        title = {'text': 'Daily New Cases', 
                    'subtitle': 'Source: JHU'}
    )

    county_new_cases = alt.Chart(county_to_plot).mark_line().encode(
        x = alt.X('date:T', scale = alt.Scale(domain = brush), title = 'Daily New Cases'),
        y = 'new_cases:Q'
    ).properties(
        title = {'text': 'Daily New Cases', 
                    'subtitle': 'Source: JHU'}
    )


    county_plots_set = alt.vconcat(apple_sc | google_sc, county_cum_cases | county_new_cases)
    
    return pn.Column(subtitle, county_plots_set)



state_county_dash = pn.Row(
    pn.Column(state_input,state_county_plot)
)


# In[ ]:




