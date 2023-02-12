#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import altair as alt
import panel as pn


# In[2]:


## Data import
apple_us = pd.read_csv('data/apple_clean_us.csv')
google_us = pd.read_csv('data/google_clean_us.csv')

apple_to_plot = apple_us.melt(
    id_vars='date',
    value_vars = ['driving', 'transit', 'walking'],
    var_name = 'type',
    value_name = 'volume'
)

google_cols_to_melt = google_us.columns[4:]
google_to_plot = google_us.melt(
    id_vars = 'date',
    value_vars = google_cols_to_melt,
    var_name = 'type',
    value_name = 'volume'
)


# In[3]:


def us_plot():
    
    apple_to_plot = apple_us.melt(
        id_vars='date',
        value_vars = ['driving', 'transit', 'walking'],
        var_name = 'type',
        value_name = 'volume'
    )

    google_cols_to_melt = google_us.columns[4:]
    google_to_plot = google_us.melt(
        id_vars = 'date',
        value_vars = google_cols_to_melt,
        var_name = 'type',
        value_name = 'volume'
    )

    brush = alt.selection_interval(encodings=['x'])

    color = alt.condition(brush,
                          alt.Color('type:Q', legend=None),
                          alt.value('lightgray'))



    a = apple = alt.Chart(apple_to_plot).mark_line().encode(
        x = 'date:T',
        y = alt.Y('volume:Q', title = 'Relative volume'),
        color = 'type:N'
    ).add_selection(brush).properties(title = 'Apple mobility data')

    # addding a multi line tooltip

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    line = alt.Chart(google_to_plot).mark_line().encode(
        x = alt.X('date:T', scale = alt.Scale(domain = brush)),
        y = alt.Y('volume:Q', title = 'Relative volume'),
        color = 'type:N'
    ).properties(title = 'Google mobility data')


    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(google_to_plot).mark_point().encode(
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
        text= alt.condition(nearest, 'volume:Q', alt.value(' '))
    )


    # Draw a rule at the location of the selection
    rules = alt.Chart(google_to_plot).mark_rule(color='gray').encode(
        x='date:T'
    ).transform_filter(
        nearest
    )

    b_with_rule = alt.layer(
        line,selectors, points, rules, text
    ).properties(
        width=400, height=300
    )

    return (a | b_with_rule)


# ## Adding case number plots 

# In[4]:


us_cases = pd.read_csv('data/jhu-us-cases.csv')


# In[5]:


def us_plot_set():    
    brush = alt.selection_interval(encodings=['x'])

    color = alt.condition(brush,
                          alt.Color('type:Q', legend=None),
                          alt.value('lightgray'))


    apple = alt.Chart(apple_to_plot).mark_line().encode(
        x = 'date:T',
        y = 'volume:Q',
        color = 'type:N'
    ).add_selection(
        brush
    ).properties(
        title = 'Apple mobility data',
        width = 405
    )

    # google plot with tooltip 

    # addding a multi line tooltip

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    line = alt.Chart(google_to_plot).mark_line().encode(
        x = alt.X('date:T', scale = alt.Scale(domain = brush)),
        y = 'volume:Q',
        color = 'type:N'
    ).properties(title = 'Google mobility data')


    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(google_to_plot).mark_point().encode(
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
        text= alt.condition(nearest, 'volume:Q', alt.value(' '))
    )


    # Draw a rule at the location of the selection
    rules = alt.Chart(google_to_plot).mark_rule(color='gray').encode(
        x='date:T'
    ).transform_filter(
        nearest
    )

    google_with_rule = alt.layer(
        line,selectors, points, rules, text
    ).properties(
        width=400, height=300
    )


    cum_cases_bar = alt.Chart(us_cases).mark_bar().encode(
        x = alt.X('date:T', scale = alt.Scale(domain = brush)),
        y = alt.Y('cases:Q', title = 'Cumulative Cases'),
        tooltip = ['date:T', 'cases:Q']
    ).properties(
        title = {'text': 'US: Cumulative Cases', 
                    'subtitle': 'Source: JHU'},
        width = 400
    )

    new_cases_bar = alt.Chart(us_cases).mark_bar().encode(
        x = alt.X('date:T', scale = alt.Scale(domain = brush)),
        y = alt.Y('new_cases:Q', title = 'Daily New Cases')
    ).properties(
        title = {'text': 'US:  Daily New Cases', 
                    'subtitle': 'Source: JHU'},
        width = 400
    )

    return alt.vconcat((apple | google_with_rule), cum_cases_bar | new_cases_bar)


# In[ ]:




