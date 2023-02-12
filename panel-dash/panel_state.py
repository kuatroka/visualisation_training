#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import altair as alt
import panel as pn


# In[2]:


apple_states = pd.read_csv('data/apple_clean_states.csv', parse_dates=['date'])
google_states = pd.read_csv('data/google_clean_states.csv', parse_dates= ['date'])

temp = apple_states[['region', 'date', "driving"]]
states_7_day = temp.groupby('region').rolling(7, on = 'date').mean().reset_index()
states_7_day.columns = ['region', 'drop', 'date', 'driving_7_day']

state_case_data = pd.read_csv('data/jhu-case-data.csv', parse_dates= ['date'])
state_case_data = state_case_data.groupby(['Province_State', 'date'])['cases'].sum().reset_index()


# In[3]:


# heatmap

states = list(set(apple_states.region))

state_only_input = pn.widgets.AutocompleteInput(value = "Maryland",
                            options = states,
                            placeholder = "Maryland",
                            name = "Select a state")

@pn.depends(state_only_input.param.value)
def state_heatmap(state_only_input):
    state_to_plot = states_7_day[states_7_day.region == state_only_input]

    plot = alt.Chart(
        state_to_plot
    ).mark_rect().encode(
        x='date(date):O',
        y='month(date):O',
        color=alt.Color('driving_7_day:Q', scale=alt.Scale(scheme="redyellowgreen"),
                       legend=alt.Legend(title="Driving volume")),
        tooltip=[
            alt.Tooltip('monthdate(date):T', title='Date'),
            alt.Tooltip('driving_7_day:Q', title='Requests vol', format = '.0f')
        ]
    ).properties(
        width=500,
        height = 200,
        title = {'text': f'Driving directions requests: {state_only_input}', 
                'subtitle': '7-day rolling average, indexed to Jan 13 requests'}
    )
    
    return plot

@pn.depends(state_only_input.param.value)
def state_cases(state_only_input):
    state_case_to_plot = pd.DataFrame(state_case_data[state_case_data.Province_State == state_only_input])
    state_case_to_plot['new_cases'] = state_case_to_plot['cases'].rolling(window=2).apply(lambda x: x[1] - x[0], raw = True)
    
    state_cum_cases = alt.Chart(state_case_to_plot).mark_bar().encode(
        x = 'date:T',
        y = 'cases:Q',
        tooltip = ['date', 'cases']
    ).properties(
        title = {'text': 'Cumulative Cases', 
                    'subtitle': 'Source: JHU'}
    )
    
    m = state_case_to_plot['new_cases'].max()
    state_new_cases = alt.Chart(state_case_to_plot).mark_bar().encode(
        x = 'date:T',
        y = alt.Y('new_cases:Q', scale = alt.Scale(domain = (0,m))),
        tooltip = ['date', 'new_cases']
    ).properties(
        title = {'text': 'Daily New Cases', 
                    'subtitle': 'Source: JHU'}
    )
    
    return pn.Row(state_cum_cases, state_new_cases)

@pn.depends(state_only_input.param.value)
def state_google(state_only_input):
    to_plot = google_states[google_states.sub_region_1 == state_only_input]
    id_vars = ['date']
    value_vars = to_plot.columns[4:]
    to_plot = to_plot.melt(id_vars, value_vars, var_name = 'type', value_name = 'volume')

    highlight = alt.selection(type='single', on='mouseover',
                              fields=['type'], nearest=True)

    base = alt.Chart(to_plot).mark_line().encode(
        x = 'date:T',
        y = alt.Y('volume:Q', title = 'Relative volume'),
        color = alt.Color('type:N', title = "Destination type")
    ).properties(
        title = {'text': 'Traffic by Destination Type',
                'subtitle': 'Source: Google mobility data'},
        height = 300
    )

    points = base.mark_circle().encode(
        opacity=alt.value(0)
    ).add_selection(
        highlight
    ).properties(
        width=600
    )

    lines = base.mark_line().encode(
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )

    return points + lines
    

single_state_plots = pn.Column(
    state_only_input, 
    state_heatmap,
    pn.Row(state_google, height = 400),
    state_cases
)


# In[4]:


#pn.extension('vega')
#single_state_plots.servable()


# In[ ]:




