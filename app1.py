import pandas as pd
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

def load_data():
    data = pd.read_csv("assets\healthcare_dataset.csv")
    data["Billing Amount"] = pd.to_numeric(data["Billing Amount"], errors='coerce')
    data["Date of Admission"] = pd.to_datetime(data["Date of Admission"])
    data["YearMonth"] = data["Date of Admission"].dt.to_period("M")
    return data

data = load_data()

num_records = len(data)
avg_billing = data["Billing Amount"].mean()

# Create a web app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Healthcare Dashboard", className="text-center my-5"), width=12)
    ]),
    # Hospital statistics
    dbc.Row([
        dbc.Col(html.Div(f"Total Patient Records: {num_records}", className="text-center my-3 top-text"), width=6),
        dbc.Col(html.Div(f"Average Billing Amount: {avg_billing:.2f}", className="text-center my-3 top-text"), width=6)
    ], className="mb-5"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Patient Demographics", className="card-title"),
                    dcc.Dropdown(
                        id="gender-filter", 
                        options=[{"label": gender, "value": gender} for gender in data["Gender"].unique()], 
                        value=None,
                        placeholder="Select Gender"
                    ),
                    dcc.Graph(id="age-distribution")
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Medical Condition", className="card-title"),
                    dcc.Graph(id="medical-condition")
                ])
            ])
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Insurance Provider Comparison", className="card-title"),
                    dcc.Graph(id="insurance-comparison")
                ])
            ])
        ], width=12)
    ]),
    
    # Billing distribution
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Billing Amount Distribution", className="card-title"),
                    dcc.Slider(
                        id="billing-slider", 
                        min=data["Billing Amount"].min(),
                        max=data["Billing Amount"].max(),
                        value=data["Billing Amount"].median(),
                        marks={int(value): f"${int(value)}" for value in data["Billing Amount"].quantile([0, 0.25, 0.5, 0.75, 1]).unique()}
                    ),
                    dcc.Graph(id="billing-distributor")
                ])
            ])
        ], width=12)
    ]),
    
    # Trends in admission
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Trends in Admission", className="card-title"),
                    dcc.RadioItems(
                        id="chart-type",
                        options=[
                            {'label': 'Bar', 'value': 'bar'},
                            {'label': 'Line', 'value': 'line'}
                        ],
                        value='bar'
                    ),
                    dcc.Dropdown(
                        id="condition-filter", 
                        options=[{"label": condition, "value": condition} for condition in data["Medical Condition"].unique()],
                        value=None,
                        placeholder="Select Condition"
                    ),
                    dcc.Graph(id="admission-trends")
                ])
            ])
        ], width=12)
    ])
])

# Callbacks for gender demographics
@app.callback(
    Output('age-distribution', 'figure'),
    Input('gender-filter', 'value')
)
def update_distribution(selected_gender):
    if selected_gender:
        filtered_df = data[data["Gender"] == selected_gender]
    else:
        filtered_df = data
    
    if filtered_df.empty:
        return {}

    fig = px.histogram(
        filtered_df, 
        x="Age", 
        nbins=10,
        color="Gender",
        title="Age Distribution by Gender"
    )
    return fig


#medical-condition callback
@app.callback(
    Output('medical-condition', 'figure'),
    Input('gender-filter', 'value')
)
def update_medical_condition(selected_gender):
    filtered_df = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px.pie(
        filtered_df,
        names = "Medical Condition", 
        title = "Medical Condition Distribution")

    return fig

#insurance provider comparison
@app.callback(
    Output('insurance-comparison','figure' ),
    Input('gender-filter','value')
)

def update_insurance(selected_gender):
    filtered_df = data[data["Gender"] == selected_gender] if selected_gender else data
    fig = px. bar(
        filtered_df, 
        x = 'Insurance Provider',
        y = 'Billing Amount',
        color = 'Medical Condition',
        barmode = 'group',
        title = "Insurance provider price comparison",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    return fig

#biling distribution
@app.callback(
    Output('billing-distributor', 'figure'),
    [Input('gender-filter', 'value'),
     Input('billing-slider', 'value')]
)

def update_billing(selected_gender, slider_value):
    filtered_df = data[data["Gender"] == selected_gender] if selected_gender else data
    filtered_df = filtered_df[filtered_df["Billing Amount"] <= slider_value]
    
    # Debugging: print the filtered DataFrame and slider value
    print(f"Filtered DataFrame:\n{filtered_df}")
    print(f"Slider Value: {slider_value}")
    
    # Handle case when filtered_df is empty
    if filtered_df.empty:
        return {
            "data": [],
            "layout": {
                "title": "Billing Amount Distribution",
                "xaxis": {"title": "Billing Amount"},
                "yaxis": {"title": "Count"}
            }
        }
    
    fig = px.histogram(
        filtered_df, 
        x='Billing Amount', 
        nbins=10,
        title="Billing Amount Distribution"
    )
    return fig




#admission trends callback
@app.callback(
    Output('admission-trends', 'figure'),
    [Input('chart-type', 'value'), Input('condition-filter', 'value')]
)

def update_admission(chart_type, selected_condition):
    
    filtered_df = data[data["Medical Condition"] == selected_condition] if selected_condition else data

    trend_df = filtered_df.groupby("YearMonth").size().reset_index(name = 'Count')
    trend_df["YearMonth"]= trend_df["YearMonth"].astype(str)
    if chart_type == 'line':
        fig = px.line(trend_df, x ='YearMonth', y = 'Count',
                      title = 'admission trend over time'
                      )
    else:
        fig = px.bar(trend_df, x ='YearMonth', y = 'Count',
                      title = 'admission trend over time')
    return fig
    




if __name__ == '__main__':
    app.run_server(debug=True)
