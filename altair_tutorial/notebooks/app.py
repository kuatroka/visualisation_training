import altair as alt
import pandas as pd
import panel as pn

pn.extension("vega", sizing_mode="stretch_width")

data = pd.read_json(
    "https://raw.githubusercontent.com/vega/vega/master/docs/data/penguins.json"
)

theme = pn.state.session_args.get("theme", [b"default"])[0].decode()
if theme == "dark":
    alt.themes.enable("dark")
else:
    alt.themes.enable("default")

brush = alt.selection_interval(name="brush")

chart = (
    alt.Chart(data)
    .mark_point()
    .encode(
        x=alt.X("Beak Length (mm):Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Beak Depth (mm):Q", scale=alt.Scale(zero=False)),
        color=alt.condition(brush, "Species:N", alt.value("lightgray")),
    )
    .properties(width="container", height="container")
    .add_selection(brush)
)

vega_pane = pn.pane.Vega(chart, debounce=10, height=800)

@pn.depends(vega_pane.selection.param.brush)
def filtered_table(selection):
    if not selection:
        return "## No selection"
    query = " & ".join(
        f"{crange[0]:.3f} <= `{col}` <= {crange[1]:.3f}"
        for col, crange in selection.items()
    )
    return pn.pane.DataFrame(data.query(query))


table = pn.Row(filtered_table, height=300, scroll=True)
component = pn.Column(vega_pane, table)


template = pn.template.FastListTemplate(
    site="Awesome Panel",
    title="Panel supports Vega and Altair Selections",
    accent="#F08080",
    main=[component],
).servable()