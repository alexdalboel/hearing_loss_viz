import dash
from dash import html, dcc, Input, Output
import geopandas as gpd
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objs as go


# Load GeoJSON data for kommune
gdf_kommune = gpd.read_file('kommuner.geojson')
gdf_kommune['geometry'] = gdf_kommune['geometry'].simplify(tolerance=0.005)

# Merge all geometries for municipalities with multiple shapes (e.g., islands)
gdf_kommune = gdf_kommune.groupby('KOMNAVN').geometry.apply(lambda x: x.unary_union)

# Load the CSV data
df_kom = pd.read_csv('df_kom.csv')
df_combined = pd.read_csv('combined_data.csv')

# Merge GeoDataFrame with the CSV data on 'Kommune'
gdf_kommune = gdf_kommune.reset_index()
gdf_kommune = gdf_kommune.merge(df_kom, left_on='KOMNAVN', right_on='Kommune', how='left')

# Ensure the GeoDataFrame has a valid GeoJSON representation
gdf_kommune['geometry'] = gdf_kommune['geometry'].apply(lambda x: x if x.is_valid else x.buffer(0))

# Calculate the fixed min and max for the color scale
min_value = df_kom[df_kom['\u00c5r'] == 2010]['Andel_tinitus'].min()
max_value = df_kom[df_kom['\u00c5r'] == 2021]['Andel_tinitus'].max()

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], assets_folder='assets')
app.title = "Tinnitus Map"

# Define the layout using Bootstrap grid system
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("Tinnitus Development in Denmark", style={'textAlign': 'center'}),
        ])
    ]),

    dbc.Row([
        dbc.Col([
            

            dcc.Slider(
                id='year-slider',
                min=2010,
                max=2021,
                step=None,
                value=2010,
                marks={2010: '2010', 2013: '2013', 2017: '2017', 2021: '2021'},
            ),

            # Map to display the geographical data
            dcc.Graph(
                id='map',
                style={
                    "height": "80vh",  # 80% of the viewport height for the map
                    "width": "90%"  # Make the map width responsive to the container
                }
            ),
        ], width=5),  # Map takes up 8 parts of the screen

        dbc.Col([
            # Add the area chart for tinnitus development over the years
            dcc.Graph(
                id='tinnitus-area-chart',
                style={"height": "50vh", "width": "100%", "margin-bottom": "0px"}
            ),
            dcc.Graph(
                id='gender-chart',
                style={"height": "50vh", "width": "100%"}
            ),
        ], width=7),  # Area chart takes up 4 parts of the screen
    ])
])


@app.callback(
    [Output('map', 'figure'),
     Output('tinnitus-area-chart', 'figure'),
     Output('gender-chart', 'figure')],
    [Input('year-slider', 'value'),
     Input('map', 'clickData')]  # Add clickData to the input
)
def update_map_and_area_chart(selected_year, clickData):
    # Filter data based on the selected year
    filtered_df = df_kom[df_kom['\u00c5r'] == selected_year]

    # Calculate the average tinnitus percentage for the selected year
    average_tinnitus = filtered_df['Andel_tinitus'].mean()

    # Define the national average tinnitus for the years 2010, 2013, 2017, and 2021
    national_average_data = {
        2010: 10.5,  # Example national averages for these years
        2013: 12.9,
        2017: 13.7,
        2021: 17.0,
    }

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



    # Merge filtered data with GeoDataFrame for Kommune
    gdf_filtered = gdf_kommune.merge(filtered_df, left_on='KOMNAVN', right_on='Kommune', how='left')

    # Determine the correct color column
    color_column = 'Andel_tinitus_y' if 'Andel_tinitus_y' in gdf_filtered.columns else 'Andel_tinitus_x'

    # Round the values in the color column for cleaner display
    gdf_filtered[color_column] = gdf_filtered[color_column].round(1)

    # Create the choropleth map
    fig = px.choropleth_mapbox(
        gdf_filtered,
        geojson=gdf_filtered.geometry.__geo_interface__,
        locations=gdf_filtered.index,
        color=color_column,
        mapbox_style="white-bg",
        center={"lat": 56.100, "lon": 11.700},
        zoom=5.2,
        color_continuous_scale=["#FEFE62", "#FF1AC8"],
        range_color=[min_value, max_value],
        hover_data={
            "KOMNAVN": True,  # Kommune name
            color_column: True,  # Rounded percentage
        }
    )

    # Update hover template
    fig.update_traces(
        hovertemplate="<b>Kommune:</b> %{customdata[0]}<br>" +
                        "<b>Tinnitus Andel:</b> %{customdata[1]:.1f} %<extra></extra>"
    )

    # Check for clickData and print the name of the clicked kommune
    if clickData:
        clicked_kommune_name = clickData['points'][0]['location']

        clicked_kommune_data = df_kom[df_kom['Kommune'] == gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN']]

        clicked_region = df_kom.loc[
            df_kom['Kommune'] == gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN'], 'Region'
        ].values[0]

        clicked_region_data = [d for d in regional_average_data if d['region'] == clicked_region]

        # Get tinnitus data for that kommune from 2010-2021
        tinnitus_data = clicked_kommune_data[clicked_kommune_data['\u00c5r'].isin([2010, 2013, 2017, 2021])]
    
        # Create the line plot with national average line
        area_chart_figure = {
            'data': [
                {
                    'x': tinnitus_data['\u00c5r'],
                    'y': tinnitus_data['Andel_tinitus'],
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': f"{gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN']}",
                    'line': {'color': '#009E73'},  # Blue line for the selected kommune
                },
                {
                    'x': [2010, 2013, 2017, 2021],
                    'y': [national_average_data[2010], national_average_data[2013], national_average_data[2017], national_average_data[2021]],
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': 'National Average',
                    'line': {'dash': 'dash', 'color': '#E69F00'},  # Dashed line for national average
                },
                {
                    'x': [2010, 2013, 2017, 2021],
                    'y': [d['value'] for d in clicked_region_data],
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': 'Regional Average',
                    'line': {'dash': 'dash', 'color': '#56B4E9'},  # Dashed line for regional average
                },

            ],
            'layout': {
                'title': f"Tinnitus Development in {gdf_filtered.loc[clicked_kommune_name, 'KOMNAVN']} municipality",
                'xaxis': {
                    'title': None,
                    'tickvals': [2010, 2013, 2017, 2021],
                    'ticktext': ['2010', '2013', '2017', '2021']
                },
                'yaxis': {
                    'title': '%',
                    'range': [7, 20]  # Set y-axis range to start from 5%
                }
            }
        }

        gender_data = pd.read_csv('combined_data.csv')

        men_data = gender_data[(gender_data['Region'] == clicked_region) & (gender_data['Køn'] == 'Mænd')]
        female_data = gender_data[(gender_data['Region'] == clicked_region) & (gender_data['Køn'] == 'Kvinder')]
        
        gender_chart_figure = {
            'data': [
                # Male data traces
                go.Bar(
                    x=men_data[men_data['År'] == 2010]['Alder'],  # Age groups for the year 2010 (Males)
                    y=men_data[men_data['År'] == 2010]['Andel_tinitus'],
                    name='2010 Mænd',
                    visible=True  # Set visible to True so the data is shown initially
                ),
                go.Bar(
                    x=men_data[men_data['År'] == 2013]['Alder'],  # Age groups for the year 2013 (Males)
                    y=men_data[men_data['År'] == 2013]['Andel_tinitus'],
                    name='2013 Mænd',
                    visible=True
                ),
                go.Bar(
                    x=men_data[men_data['År'] == 2017]['Alder'],  # Age groups for the year 2017 (Males)
                    y=men_data[men_data['År'] == 2017]['Andel_tinitus'],
                    name='2017 Mænd',
                    visible=True
                ),
                go.Bar(
                    x=men_data[men_data['År'] == 2021]['Alder'],  # Age groups for the year 2021 (Males)
                    y=men_data[men_data['År'] == 2021]['Andel_tinitus'],
                    name='2021 Mænd',
                    visible=True
                ),
                
                # Female data traces
                go.Bar(
                    x=female_data[female_data['År'] == 2010]['Alder'],  # Age groups for the year 2010 (Females)
                    y=female_data[female_data['År'] == 2010]['Andel_tinitus'],
                    name='2010 Kvinder',
                    visible=False # Initially hide female data
                ),
                go.Bar(
                    x=female_data[female_data['År'] == 2013]['Alder'],  # Age groups for the year 2013 (Females)
                    y=female_data[female_data['År'] == 2013]['Andel_tinitus'],
                    name='2013 Kvinder',
                    visible=False
                ),
                go.Bar(
                    x=female_data[female_data['År'] == 2017]['Alder'],  # Age groups for the year 2017 (Females)
                    y=female_data[female_data['År'] == 2017]['Andel_tinitus'],
                    name='2017 Kvinder',
                    visible=False
                ),
                go.Bar(
                    x=female_data[female_data['År'] == 2021]['Alder'],  # Age groups for the year 2021 (Females)
                    y=female_data[female_data['År'] == 2021]['Andel_tinitus'],
                    name='2021 Kvinder',
                    visible=False
                ),
            ],
            'layout': {
                'title': f"Tinnitus development in {clicked_region}",
                'xaxis': {
                    'title': 'Age Group',
                    'tickvals': ['16-24 år', '25-34 år', '35-44 år', '45-54 år', '55-64 år', '65-74 år', '75+ år'],
                    'ticktext': ['16-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75+']
                },
                'yaxis': {
                    'title': 'Tinnitus Percentage',
                    'range': [0, 40]  # Adjust the range as needed
                },
                'barmode': 'group',  # Group bars for each year side by side
                'legend': {
                    'title': 'Gender',
                    'traceorder': 'normal',  # Ensure the legend is ordered properly
                    'itemsizing': 'constant'  # Keep item sizing constant in the legend
                }
            
        }
    }

    else:
        area_chart_figure = {}
        gender_chart_figure = {}

    # Update layout
    fig.update_layout(
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

    return fig, area_chart_figure, gender_chart_figure



# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
