#!/usr/bin/env python
# coding: utf-8

# In[2]:


import altair as alt
import pandas as pd
import panel as pn


# In[31]:


apple_states = pd.read_csv('data/apple_clean_states.csv', parse_dates=['date'])
#apple_states.head()

temp = apple_states[['region', 'date', "driving"]]
states_7_day = temp.groupby('region').rolling(7, on = 'date').mean().reset_index()
states_7_day.columns = ['region', 'drop', 'date', 'driving_7_day']

state_case_data = pd.read_csv('data/jhu-case-data.csv', parse_dates= ['date'])
state_case_data = state_case_data.groupby(['Province_State', 'date'])['cases'].sum().reset_index()

states = list(set(apple_states.region))


# In[86]:


state_checkbox_group = pn.widgets.CheckBoxGroup(
    name='Checkbox Group', 
    value=['New York', 'Maryland'], 
    options=sorted(states),
    sizing_mode="stretch_height",
    inline = False,
)

@pn.depends(state_checkbox_group.param.value)
def state_comparison_plot(state_checkbox_group):
    if len(state_checkbox_group) > 5:
        return "please select only 5"
        
    
    to_plot = states_7_day[states_7_day.region.isin(state_checkbox_group)]
    line = alt.Chart(to_plot).mark_line().encode(
        x = 'date:T',
        y = alt.Y('driving_7_day:Q', title = 'Driving directions requests'),
        color = alt.Color('region:N', legend=alt.Legend(title="State"))
    ).properties(
        title = {'text': 'Driving directions request volume (7-day average)', 
                        'subtitle': 'Source: Apple mobility data'},
        height = 400, 
        width = 500)
    
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')



    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(to_plot).mark_point().encode(
        x= 'date:T',
        opacity = alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text= alt.condition(nearest, alt.Text('driving_7_day:Q', format = "s"), alt.value(' '))

    )


    # Draw a rule at the location of the selection
    rules = alt.Chart(to_plot).mark_rule(color='gray').encode(
        x='date:T'
    ).transform_filter(
        nearest
    )
    
    return alt.layer(line, selectors, points, text, rules)

@pn.depends(state_checkbox_group.param.value)
def state_case_comparison_plot(state_checkbox_group):
    state_cases_to_plot = state_case_data[state_case_data.Province_State.isin(state_checkbox_group)]

    line = alt.Chart(state_cases_to_plot).mark_line().encode(
        x = 'date:T', 
        y = alt.Y('cases:Q', title = "Cumulative Cases"),
        color = alt.Color('Province_State:N', legend=alt.Legend(title="State"))
    ).properties(
            title = {'text': 'Cumulative Cases by State', 
                        'subtitle': 'Source: JHU'},
        height = 350, width = 480
        )


    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')



    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(state_cases_to_plot).mark_point().encode(
        x= 'date:T',
        opacity = alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text= alt.condition(nearest, alt.Text('cases:Q', format = "s"), alt.value(' '))

    )


    # Draw a rule at the location of the selection
    rules = alt.Chart(state_cases_to_plot).mark_rule(color='gray').encode(
        x='date:T'
    ).transform_filter(
        nearest
    )

    return alt.layer(line, selectors, points, text, rules)

    
state_comparison = pn.Column(
    "*Select up to 5 states to compare*",

        pn.Row(
            state_checkbox_group,
            pn.Column(
                pn.Row(state_comparison_plot, height = 500),
                pn.Row(state_case_comparison_plot, height = 500)
            )
        )  
    
)


# In[87]:


#pn.extension('vega')
#state_comparison.servable()


# In[ ]:




