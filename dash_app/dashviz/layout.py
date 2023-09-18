"""
Module which houses the layout for dash visualization.
"""
import plotly.express as px
import plotly.graph_objects as go
from jupyter_dash import JupyterDash
from dash import dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import urllib.parse as urllib

def build_layout(segments=[
    'overall',
    'lead_source',
    'user_income',
    'user_gender',
    'user_age',
]):
    elements_layout = html.Div([
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            dcc.Graph(id='conversion'),
                        ]
                    )
                    , width=6
            ),
            dbc.Col(
                html.Div(
                    [
                        dcc.Graph(id='level'),
                    ]
                ),
                width=6,
            ),
        ]

    )
    ])

    final_layout = html.Div([
        html.H1("Conversion Analytics"),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(html.Div(children="""Segments"""),
                    width=2),
            ]

        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id='splitter_dropdown',
                        value=[],
                        multi=False,
                        clearable=False,
                        options=[
                            {'label': segment, 'value': segment} for segment in segments
                        ]
                    )
                    , width=2
                ),

            ]
        ),
        html.Br(),
        elements_layout,
    ])
    return final_layout