import dash
from dash import dcc, html, Output, Input, State
import dash_bootstrap_components as dbc
import requests
import pandas as pd
from typing import List
from front_end.utils.trino_operator import TrinoDBOperator
from settings import settings

API_BASE_URL = "http://localhost:8000"

# ----------------------
# Load champions from Trino
# ----------------------
def load_champions() -> pd.DataFrame:
    try:
        with TrinoDBOperator(schema=settings.LAKE_SCHEMA) as trino_op:
            query = f"""
            SELECT DISTINCT champion_name, roles, icon_url
            FROM {settings.LAKE_SCHEMA}.{settings.CHAMPION_TABLE}
            ORDER BY champion_name
            """
            results = trino_op.execute_query(query)
            if results:
                return pd.DataFrame(results)
            return pd.DataFrame(columns=['champion_name', 'roles', 'icon_url'])
    except Exception:
        return pd.DataFrame(columns=['champion_name', 'roles', 'icon_url'])

# ----------------------
# Get champion image
# ----------------------
def get_champion_image(name, champions_df):
    row = champions_df[champions_df['champion_name'] == name]
    if not row.empty:
        return row.iloc[0]['icon_url']
    return None

# ----------------------
# Call API
# ----------------------
def call_predict_api(allies: List[str], opponents: List[str], choose_positions: List[str], bans: List[str], top_n: int = 5):
    payload = {
        "allies": allies,
        "opponents": opponents,
        "choose_positions": choose_positions,
        "bans": bans,
        "top_n": top_n,
        "model_name": "champion_recommender"
    }
    try:
        response = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except:
        return None

# ----------------------
# Dash App
# ----------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

champions_df = load_champions()
positions = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "SUPPORT"]

# Helper function for options
def get_champion_options(exclude=[]):
    return [{"label": c, "value": c} for c in sorted(champions_df['champion_name'].tolist()) if c not in exclude]
# ----------------------
# Layout (Optimized)
# ----------------------
app.layout = dbc.Container([
    html.H1("League of Legends Champion Recommender", style={"textAlign": "center", "marginBottom": "30px"}),

    # Teams Selection
    dbc.Row([
        # Allies
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Your Team"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(html.Label(pos, style={"fontWeight": "bold"}), width=3),
                        dbc.Col(dcc.Dropdown(
                            id=f"ally-{pos}",
                            options=get_champion_options(),
                            placeholder="Select Champion",
                            clearable=True
                        ), width=7),
                        dbc.Col(dbc.Button("×", id=f"clear-ally-{pos}", color="danger", size="sm", className="w-100"), width=2)
                    ], className="mb-2") for pos in positions
                ])
            ])
        ], width=6),

        # Enemies
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Enemy Team"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(html.Label(pos, style={"fontWeight": "bold"}), width=3),
                        dbc.Col(dcc.Dropdown(
                            id=f"enemy-{pos}",
                            options=get_champion_options(),
                            placeholder="Select Champion",
                            clearable=True
                        ), width=7),
                        dbc.Col(dbc.Button("×", id=f"clear-enemy-{pos}", color="danger", size="sm", className="w-100"), width=2)
                    ], className="mb-2") for pos in positions
                ])
            ])
        ], width=6)
    ], style={"marginBottom": "30px"}),

    # Positions, Bans, Top-N
    dbc.Row([
        dbc.Col([
            html.H5("Positions to Recommend"),
            dcc.Checklist(
                id="choose-positions",
                options=[{"label": pos, "value": pos} for pos in positions],
                value=["TOP"],
                labelStyle={"display": "inline-block", "marginRight": "10px"}
            )
        ], width=4),

        dbc.Col([
            html.H5("Banned Champions"),
            dcc.Dropdown(
                id="bans",
                options=get_champion_options(),
                multi=True,
                placeholder="Select banned champions",
                clearable=True
            )
        ], width=4),

        dbc.Col([
            html.H5("Top N Recommendations"),
            dcc.Slider(1, 10, 5, id="top-n", marks={i: str(i) for i in range(1, 11)})
        ], width=4)
    ], style={"marginBottom": "30px"}),

    # Buttons
    dbc.Row([
        dbc.Col(dbc.Button("Get Recommendations", id="get-recommendations", color="primary", size="lg", className="w-100"), width=10),
        dbc.Col(dbc.Button("Clear All", id="clear-all", color="secondary", size="lg", className="w-100"), width=2)
    ], style={"marginBottom": "20px"}),

    html.Hr(),

    # Recommendations
    dbc.Row([
        dbc.Col(html.Div(id="recommendations"))
    ])
], fluid=True)
# ----------------------
# Callbacks
# ----------------------

# Clear individual ally position
for pos in positions:
    @app.callback(
        Output(f"ally-{pos}", "value"),
        Input(f"clear-ally-{pos}", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_ally(n_clicks):
        return None

# Clear individual enemy position
for pos in positions:
    @app.callback(
        Output(f"enemy-{pos}", "value"),
        Input(f"clear-enemy-{pos}", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_enemy(n_clicks):
        return None

# Clear all selections
@app.callback(
    [Output(f"ally-{pos}", "value", allow_duplicate=True) for pos in positions] +
    [Output(f"enemy-{pos}", "value", allow_duplicate=True) for pos in positions] +
    [Output("bans", "value"), Output("choose-positions", "value")],
    Input("clear-all", "n_clicks"),
    prevent_initial_call=True
)
def clear_all_selections(n_clicks):
    return [None] * 10 + [[], ["TOP"]]  # Clear all dropdowns, bans, and reset positions

# Update Positions to Recommend based on picked allies
@app.callback(
    Output("choose-positions", "options"),
    Output("choose-positions", "value", allow_duplicate=True),
    [Input(f"ally-{p}", "value") for p in positions],
    [State("choose-positions", "value")],
    prevent_initial_call=True
)
def update_positions_options(*args):
    selected_allies = args[:5]
    current_value = args[5] or []

    picked_positions = [positions[i] for i, val in enumerate(selected_allies) if val not in (None, '')]
    options = [{"label": pos, "value": pos} for pos in positions if pos not in picked_positions]
    new_value = [pos for pos in current_value if pos not in picked_positions]

    return options, new_value

# Prevent duplicate champions in allies and enemies
@app.callback(
    [Output(f"ally-{pos}", "options") for pos in positions],
    [Input(f"ally-{p}", "value") for p in positions] +
    [Input(f"enemy-{p}", "value") for p in positions]
)
def update_ally_options(*selected):
    allies_selected = selected[:5]
    enemies_selected = selected[5:]
    all_selected = [c for c in allies_selected + enemies_selected if c]
    return [
        get_champion_options(exclude=[c for c in all_selected if c != val])
        for val in allies_selected
    ]

@app.callback(
    [Output(f"enemy-{pos}", "options") for pos in positions],
    [Input(f"ally-{p}", "value") for p in positions] +
    [Input(f"enemy-{p}", "value") for p in positions]
)
def update_enemy_options(*selected):
    allies_selected = selected[:5]
    enemies_selected = selected[5:]
    all_selected = [c for c in allies_selected + enemies_selected if c]
    return [
        get_champion_options(exclude=[c for c in all_selected if c != val])
        for val in enemies_selected
    ]

# Generate recommendations
@app.callback(
    Output("recommendations", "children"),
    Input("get-recommendations", "n_clicks"),
    [State(f"ally-{p}", "value") for p in positions] +
    [State(f"enemy-{p}", "value") for p in positions] +
    [State("choose-positions", "value"),
     State("bans", "value"),
     State("top-n", "value")]
)
def generate_recommendations(n_clicks, *states):
    if n_clicks == 0:
        return ""

    allies = [c for c in states[:5] if c]
    opponents = [c for c in states[5:10] if c]
    choose_positions = states[10] or []
    bans = states[11] or []
    top_n = states[12] or 5

    result = call_predict_api(allies, opponents, choose_positions, bans, top_n)
    if not result:
        return dbc.Alert("Some champions don't have any data.", color="warning")

    recs = result["result"]["recommendations"]
    output = []

    for pos in choose_positions:
        filtered = [r for r in recs if pos in r["positions"]]
        if filtered:
            output.append(html.H4(f"Recommendations for {pos}:"))
            cards = []
            for item in filtered[:top_n]:
                img_url = get_champion_image(item["champion_name"], champions_df)
                cards.append(
                    dbc.Card([
                        dbc.CardImg(src=img_url, top=True, style={"height": "80px", "width": "80px"}),
                        dbc.CardBody([
                            html.H5(item["champion_name"], className="card-title"),
                            html.P(f"Score: {item['score']:.2f}", className="card-text")
                        ])
                    ], style={"width": "120px", "display": "inline-block", "margin": "5px"})
                )
            output.append(html.Div(cards, style={"display": "flex", "flex-wrap": "wrap"}))

    return output

# ----------------------
# Run server
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
