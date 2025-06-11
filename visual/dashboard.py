import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.graph_objs as go
from db.database import get_connection
import tempfile

SIMULATION_HOURS = 1500

def get_objects_from_db():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM objects ORDER BY id", conn)
    conn.close()
    return df

def get_events_from_db(object_id):
    conn = get_connection()
    df = pd.read_sql(f"""
        SELECT * FROM events
        WHERE object_id = {object_id}
        ORDER BY time
    """, conn)
    conn.close()
    return df

def run_dashboard():
    app = dash.Dash(__name__)
    app.title = "СППР: Надёжность объектов"

    df_objects = get_objects_from_db()

    app.layout = html.Div([
        html.H1("СППР по надёжности объектов транспорта", style={'textAlign': 'center'}),

        html.H2("Выбор объекта", style={'marginTop': '20px'}),
        dash_table.DataTable(
            id='object-table',
            columns=[
                {"name": "ID", "id": "id"},
                {"name": "Тип", "id": "type"},
                {"name": "MTBF", "id": "mtbf"},
                {"name": "MTTR", "id": "mttr"},
                {"name": "Готовность", "id": "availability"}
            ],
            data=df_objects.to_dict('records'),
            row_selectable='single',
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center'},
            style_header={'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'}
        ),

        html.H3("Выберите объекты для сравнения:", style={'marginTop': '30px'}),
        dcc.Checklist(
            id='compare-selector',
            options=[{'label': str(obj_id), 'value': obj_id} for obj_id in df_objects["id"]],
            value=[],
            inputStyle={"marginRight": "5px", "marginLeft": "10px"},
            labelStyle={"display": "inline-block", "marginRight": "15px"}
        ),

        html.Button("📥 Скачать отчёт", id="download-btn", style={'marginTop': '20px'}),
        dcc.Download(id="download-data"),

        html.Button("📥 Скачать все события", id="download-all-btn", style={'marginTop': '10px'}),
        dcc.Download(id="download-all-data"),

        dcc.Graph(id='summary-graph'),

        html.Div(id='object-info', style={'marginTop': '30px'}),
        dcc.Graph(id='event-graph')
    ])

    @app.callback(
        Output('object-info', 'children'),
        Output('event-graph', 'figure'),
        Input('object-table', 'selected_rows')
    )
    def update_output(selected_rows):
        if not selected_rows:
            return html.Div("Выберите объект."), go.Figure()

        selected_id = df_objects.iloc[selected_rows[0]]["id"]
        obj_type = df_objects.iloc[selected_rows[0]]["type"]
        g = df_objects.iloc[selected_rows[0]]["availability"]

        df_events = get_events_from_db(selected_id)
        failures = df_events[df_events["event_type"] == "failure"]["time"]
        repairs = df_events[df_events["event_type"] == "repair"]["time"]

        info = html.Div([
            html.H4(f"Объект {selected_id} ({obj_type})"),
            html.H5(f"Готовность G = {g}")
        ])

        fig = go.Figure([
            go.Scatter(x=failures, y=[1]*len(failures), mode='markers', name='Отказы', marker=dict(color='red')),
            go.Scatter(x=repairs, y=[0]*len(repairs), mode='markers', name='ППР', marker=dict(color='green'))
        ])
        fig.update_layout(
            title="График событий объекта",
            xaxis_title="Время (часы)",
            yaxis=dict(tickvals=[0, 1], ticktext=['ППР', 'Отказ']),
            height=450
        )

        return info, fig

    @app.callback(
        Output("download-data", "data"),
        Input("download-btn", "n_clicks"),
        Input("object-table", "selected_rows"),
        prevent_initial_call=True
    )
    def download_report(n_clicks, selected_rows):
        if not n_clicks or not selected_rows:
            return None

        selected_id = df_objects.iloc[selected_rows[0]]["id"]
        df_events = get_events_from_db(selected_id)

        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".csv") as tmpfile:
            df_events.to_csv(tmpfile.name, index=False)
            tmp_path = tmpfile.name

        return dcc.send_file(tmp_path, filename=f"object_{selected_id}_report.csv")

    @app.callback(
        Output("download-all-data", "data"),
        Input("download-all-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def download_all_events(n_clicks):
        if not n_clicks:
            return None

        conn = get_connection()
        df = pd.read_sql("SELECT * FROM events ORDER BY object_id, time", conn)
        conn.close()

        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".csv") as tmpfile:
            df.to_csv(tmpfile.name, index=False)
            tmp_path = tmpfile.name

        return dcc.send_file(tmp_path, filename="all_events.csv")

    @app.callback(
        Output('summary-graph', 'figure'),
        Input('compare-selector', 'value')
    )
    def update_comparison(selected_ids):
        conn = get_connection()
        df = pd.read_sql("""
            SELECT object_id, event_type, COUNT(*) AS count
            FROM events
            GROUP BY object_id, event_type
            ORDER BY object_id;
        """, conn)
        conn.close()

        all_ids = selected_ids if selected_ids else df["object_id"].unique().tolist()
        df_all_ids = pd.DataFrame({"object_id": all_ids})

        df_pivot = df.pivot(index='object_id', columns='event_type', values='count').reset_index()
        df_pivot = df_all_ids.merge(df_pivot, on='object_id', how='left').fillna(0)

        object_ids = df_pivot["object_id"].astype(str).tolist()

        fig = go.Figure(data=[
            go.Bar(name='Отказы', x=object_ids, y=df_pivot.get("failure", 0), marker_color='red'),
            go.Bar(name='ППР', x=object_ids, y=df_pivot.get("repair", 0), marker_color='green')
        ])
        fig.update_layout(
            barmode='group',
            title='Сравнение выбранных объектов по отказам и ППР',
            xaxis_title='ID объекта',
            xaxis=dict(tickmode='array', tickvals=object_ids, ticktext=object_ids),
            yaxis_title='Количество событий',
            height=450
        )
        return fig

    app.run(debug=True)
