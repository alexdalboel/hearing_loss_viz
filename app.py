import dash
from dash import html, dcc, Input, Output
import geopandas as gpd
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

gdf_kommune = gpd.read_file('kommuner.geojson')
gdf_kommune['geometry'] = gdf_kommune['geometry'].simplify(tolerance=0.02)
gdf_kommune = gdf_kommune.groupby('KOMNAVN').geometry.apply(lambda x: x.unary_union)
df_kom = pd.read_csv('df_kom.csv')
df_combined = pd.read_csv('combined_data.csv')
gdf_kommune = gdf_kommune.reset_index()
gdf_kommune = gdf_kommune.merge(df_kom, left_on='KOMNAVN', right_on='Kommune', how='left')
gdf_kommune['geometry'] = gdf_kommune['geometry'].apply(lambda x: x if x.is_valid else x.buffer(0))

min_value = df_kom[df_kom['\u00c5r'] == 2010]['Andel_tinitus'].min()
max_value = df_kom[df_kom['\u00c5r'] == 2021]['Andel_tinitus'].max()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], assets_folder='assets')
app.title = "Tinnitus Map"

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([html.H3("Tinnitus Udvikling i Danmark, 2010-2021", style={'textAlign': 'center'})])
    ]),

    dbc.Row([
        dbc.Col([dcc.Slider(id='year-slider', min=2010, max=2021, step=None, value=2010,
                            marks={2010: '2010', 2013: '2013', 2017: '2017', 2021: '2021'}),
                 dcc.Graph(id='map', style={"height": "80vh", "width": "100%"})], width=7),
        dbc.Col([dcc.Graph(id='tinnitus-area-chart', style={"height": "80vh", "width": "100%"})], width=5),

    ], className="g-0"),

    dbc.Row([
        dbc.Col([dcc.Graph(id='strip-plot', style={"height": "80vh", "width": "100%"})], width=12),
    ], className="g-0"),
])

@app.callback(
    [Output('map', 'figure'),
     Output('tinnitus-area-chart', 'figure'),
     Output('strip-plot', 'figure')],
    [Input('year-slider', 'value'),
     Input('map', 'clickData')]
)
def update_map_and_area_chart(selected_year, clickData):
    filtered_df = df_kom[df_kom['\u00c5r'] == selected_year]
    average_tinnitus = filtered_df['Andel_tinitus'].mean()

    national_average_data = {2010: 10.5, 2013: 12.9, 2017: 13.7, 2021: 17.0}

    regional_average_data = [
        {"year": 2010, "region": "Region Hovedstaden", "value": 9.2},
        {"year": 2010, "region": "Region Syddanmark", "value": 12.2},
        {"year": 2010, "region": "Region Nordjylland", "value": 8.7},
        {"year": 2010, "region": "Region Midtjylland", "value": 11.6},
        {"year": 2010, "region": "Region Sjælland", "value": 10.6},
        {"year": 2013, "region": "Region Hovedstaden", "value": 12.7},
        {"year": 2013, "region": "Region Syddanmark", "value": 13.0},
        {"year": 2013, "region": "Region Nordjylland", "value": 12.9},
        {"year": 2013, "region": "Region Midtjylland", "value": 12.0},
        {"year": 2013, "region": "Region Sjælland", "value": 14.2},
        {"year": 2017, "region": "Region Hovedstaden", "value": 12.5},
        {"year": 2017, "region": "Region Syddanmark", "value": 13.6},
        {"year": 2017, "region": "Region Nordjylland", "value": 14.7},
        {"year": 2017, "region": "Region Midtjylland", "value": 13.9},
        {"year": 2017, "region": "Region Sjælland", "value": 14.9},
        {"year": 2021, "region": "Region Hovedstaden", "value": 15.9},
        {"year": 2021, "region": "Region Syddanmark", "value": 18.3},
        {"year": 2021, "region": "Region Nordjylland", "value": 16.9},
        {"year": 2021, "region": "Region Midtjylland", "value": 16.5},
        {"year": 2021, "region": "Region Sjælland", "value": 17.8},
    ]

    gdf_filtered = gdf_kommune.merge(filtered_df, left_on='KOMNAVN', right_on='Kommune', how='left')

    color_column = 'Andel_tinitus_y' if 'Andel_tinitus_y' in gdf_filtered.columns else 'Andel_tinitus_x'

    gdf_filtered[color_column] = gdf_filtered[color_column].round(1)

    map_fig = px.choropleth_mapbox(
        gdf_filtered,
        geojson=gdf_filtered.geometry.__geo_interface__,
        locations=gdf_filtered.index,
        color=color_column,
        mapbox_style="white-bg",
        center={"lat": 56.100, "lon": 11.700},
        zoom=5.2,
        color_continuous_scale=["#FEFE62", "#FF1AC8"],
        range_color=[min_value, max_value],
        hover_data={"KOMNAVN": True, color_column: True}
    )

    map_fig.update_traces(
        hovertemplate="<b>Kommune:</b> %{customdata[0]}<br>" +
                      "<b>Tinnitus Andel:</b> %{customdata[1]:.1f} %<extra></extra>"
    )

    map_fig.update_layout(
        coloraxis_colorbar_title="Tinnitus Andel (%)"
    )

    map_fig.update_layout(
        coloraxis_colorbar=dict(
            title=None,
            orientation="h",
            x=0.5,
            y=-0.3,
            xanchor="center",
            yanchor="bottom",
            ticks="inside",
            tickcolor="white",
            ticklen=30,
            tickwidth=2,
            tickvals=[min_value, average_tinnitus, max_value],
            ticktext=[f"{min_value:.1f}%", f"National average: {average_tinnitus:.1f}%", f"{max_value:.1f}%"],
            ticksuffix="%"
        ),
        margin={"r": 0, "t": 0, "b": 0, "l": 0},
    )
    

    if clickData:
        clicked_kommune_name = clickData['points'][0]['location']
        clicked_kommune_data = df_kom[df_kom['Kommune'] == gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN']]
        clicked_region = df_kom.loc[
            df_kom['Kommune'] == gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN'], 'Region'
        ].values[0]
        clicked_region_data = [d for d in regional_average_data if d['region'] == clicked_region]
        tinnitus_data = clicked_kommune_data[clicked_kommune_data['\u00c5r'].isin([2010, 2013, 2017, 2021])]

        area_chart_fig = {
            'data': [
                {'x': tinnitus_data['\u00c5r'], 'y': tinnitus_data['Andel_tinitus'], 'type': 'scatter', 'mode': 'lines',
                 'name': f"{gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN']}", 'line': {'color': '#009E73'}},
                {'x': [2010, 2013, 2017, 2021], 'y': [national_average_data[2010], national_average_data[2013],
                                                     national_average_data[2017], national_average_data[2021]], 'type': 'scatter',
                 'mode': 'lines', 'name': 'National Average', 'line': {'dash': 'dash', 'color': '#E69F00'}},
                {'x': [2010, 2013, 2017, 2021], 'y': [d['value'] for d in clicked_region_data], 'type': 'scatter',
                 'mode': 'lines', 'name': 'Regional Average', 'line': {'dash': 'dash', 'color': '#56B4E9'}},
            ],
            'layout': {
                'title': f"Tinnitus Development in {gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN']} municipality",
                'xaxis': {'title': None, 'tickvals': [2010, 2013, 2017, 2021], 'ticktext': ['2010', '2013', '2017', '2021']},
                'yaxis': {'title': '%', 'range': [7, 20]}
            }
        }

        specific_region = df_combined[df_combined['Region'] == clicked_region]
        strip_plot_fig = px.strip(
            specific_region, 
            x='Andel_tinitus', 
            y='Alder', 
            color='År', 
            facet_col='Køn',  # Separate by 
            category_orders={'Alder': ['18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75+']},
            title=f"Development by age-group and gender in {clicked_region} ",
            color_discrete_sequence=px.colors.qualitative.Safe  # Colorblind friendly colors
        )
        strip_plot_fig.update_xaxes(title_text='Tinnitus %')
        strip_plot_fig.update_yaxes(title_text ="Age-group",showgrid=True, gridwidth=2, gridcolor='#f53dbe', tickson='boundaries')


        return map_fig, area_chart_fig, strip_plot_fig

    area_chart_fig = {
        'data': [
            {'x': [2010, 2013, 2017, 2021], 'y': [national_average_data[2010], national_average_data[2013],
                                                 national_average_data[2017], national_average_data[2021]], 'type': 'scatter',
             'mode': 'lines', 'name': 'National Average', 'line': {'dash': 'dash', 'color': '#E69F00'}}
        ],
        'layout': {
            'title': "National average development",
            'xaxis': {'title': None, 'tickvals': [2010, 2013, 2017, 2021], 'ticktext': ['2010', '2013', '2017', '2021']},
            'yaxis': {'title': '%', 'range': [7, 20]}
        }
    }

    strip_plot_fig = {
        'data': [],
        'layout': {}
    }
    

    return map_fig, area_chart_fig, strip_plot_fig

if __name__ == '__main__':
    app.run_server(debug=True)
