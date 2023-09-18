"""DashViz Module

Module which houses the class responsible for Dash visualization.

"""
# Python Libraries
from functools import lru_cache
from collections import defaultdict
from typing import Dict, List, Type, Tuple

# Package Imports
import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse as urllib
import warnings
from dash import html
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots
from jupyter_dash import JupyterDash

# First Party Imports
from .layout import build_layout

warnings.filterwarnings('ignore')

TEMPLATE = "simple_white"


class DashViz:
    def __init__(
        self,
        name: str = 'dash',
    ):
        self.name = name
        self.port = 8010
        self.title = "Conversion Analytics"
        self.app = None
            
    @staticmethod
    @lru_cache(maxsize=None)
    def create_conversion_df(data: pd.DataFrame, segment: str) -> pd.DataFrame:
        """Aggregate key stages in application journey by category."""
        filtered = data[
            [
                segment,
                "application_started",
                "application_completed",
                "application_approved",
                "policy_purchased",
            ]
        ]
        grouped = filtered.groupby(segment).sum()
        grouped = grouped[
            [
                "application_started",
                "application_completed",
                "application_approved", 
                "policy_purchased",
            ]
        ]
        return grouped

    @staticmethod
    @lru_cache(maxsize=None)
    def calculate_conversion_metrics(data: pd.DataFrame) -> pd.DataFrame:
        """Calculate conversion metrics."""
        data["app_completion_rate"] = data["application_completed"] / data["application_started"] * 100
        data["approval_rate"] = data["application_approved"] / data["application_completed"] * 100
        data["purchase_rate"] = data["policy_purchased"] / data["application_approved"] * 100
        data["conversion_rate"] = data["policy_purchased"] / data["application_started"] * 100
        return data

    @lru_cache(maxsize=None)
    def calculate_expected_pv(data: pd.DataFrame, category: str) -> pd.DataFrame: 
        '''Create dataframes with desired groupings'''
        data["total_pv"] = data["pv"].copy()
        df = data[[category, "pv", "total_pv", "application_started", "policy_purchased"]]
        group_df = df.groupby(category).agg(
            {
                "pv": np.mean,
                "total_pv": np.sum,
                "application_started": np.sum,
                "policy_purchased": np.sum
            }
        )
        group_df["conversion_rate"] = group_df["policy_purchased"] / group_df["application_started"]
        group_df["expected_pv_per_app"] = group_df["pv"] * group_df["conversion_rate"]
        group_df["expected_total_pv"] = group_df["total_pv"] * group_df["conversion_rate"]
        return group_df
    
    @lru_cache(maxsize=None)
    def _format_output(self, df: pd.DataFrame) -> None:
        df.drop(columns=["total_pv"], inplace=True)
        df["cac_per_app"] = df["expected_pv_per_app"] / self.ltv_cac_ratio
        df["total_cac"] = df["cac_per_app"] * df["application_started"]
        df["total_expected_profit"] = df["expected_total_pv"] - df["total_cac"]
        df.rename(columns={
            "application_started": "Number of Apps",
            "policy_purchased": "Policies Purchased",
            "conversion_rate": "Conversion Rate",
            "pv": "PV per Policy",
            "expected_pv_per_app": "Expected PV per App",
            "expected_total_pv": "Expected PV of Segment",
            "cac_per_app": "Optimal CAC per App",
            "total_cac": "Optimal CAC of Segment",
            "total_expected_profit": "Total Expected Profit of Segment",
            }, inplace=True
        )
        df.loc[:, "Conversion Rate"] = df["Conversion Rate"].map('{:.2%}'.format)
        df.loc[:, "PV per Policy"] = df["PV per Policy"].map('{:,.2f}'.format)
        df.loc[:, "Expected PV per App"] = df["Expected PV per App"].map('{:,.2f}'.format)
        df.loc[:, "Expected PV of Segment"] = df["Expected PV of Segment"].map('{:,.2f}'.format)
        df.loc[:, "Optimal CAC per App"] = df["Optimal CAC per App"].map('{:,.2f}'.format)
        df.loc[:, "Optimal CAC of Segment"] = df["Optimal CAC of Segment"].map('{:,.2f}'.format)
        df.loc[:, "Total Expected Profit of Segment"] = df["Total Expected Profit of Segment"].map('{:,.2f}'.format)
        return df
    
    @lru_cache(maxsize=None)
    def calculate_optimal_cac(self, segment: str = "overall portfolio") -> pd.DataFrame:
        df = self._calculate_expected_pv(self.data, segment)
        df = self._format_output(df)
        return df

    def build_app(self, data: pd.DataFrame, port: int) -> None:
        app = JupyterDash(__name__, external_stylesheets=[dbc.themes.UNITED], suppress_callback_exceptions=True)
        app.layout = build_layout()

        @app.callback(
            Output('conversion', 'figure'),
            [Input("segment_dropdown", "value")],
        )
        def plot_conversion(data, segment):
            df = self.create_conversion_df(data, segment)
            df = self.calculate_conversion_metrics(df)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df.index,
                y=df["app_completion_rate"],
                name="App completion rate")
            )
            fig.add_trace(go.Bar(
                x=df.index,
                y=df["approval_rate"],
                name="Approval rate")
            )
            fig.add_trace(go.Bar(
                x=df.index,
                y=df["purchase_rate"],
                name="Purchase rate")
            )
            fig.add_trace(go.Bar(   
                x=df.index,
                y=df["conversion_rate"],
                name="Conversion rate")
            )
            fig.update_layout(
                barmode='group',
                title=f"Conversion decomposition by {segment}",
                xaxis_title=f"{segment}",
                yaxis_title="Step completion (%)",
                legend_title="Conversion step",
                font=dict(
                    family="Courier New, monospace",
                    size=16,
                )
            )
            return fig

        @app.callback(
            Output('pv', 'figure'),
            Input("segment_dropdown", "value"),
        )
        def plot_expected_pv(data: pd.DataFrame, segment: str):
            df = self.calculate_expected_pv(data, segment)
            fig = px.bar(
                df,
                x=df.index,
                y=df['expected_pv_per_app'],
            )
            fig.update_layout(
                title=f"Expected present value of applications by {segment}",
                xaxis_title=f"{segment}",
                yaxis_title="Present value per application ($)",
                font=dict(
                    family="Courier New, monospace",
                    size=16,
                )
            )
            return fig
        
        self.app = app

    def visualize(
        self,
        data: pd.DataFrame,
        title: str = "Conversion Analytics",
    ) -> None:
        self.build_app(data, self.port)
        self.app.title = title
        self.app.run_server(port=self.port, jupyter_mode="tab", debug=True)
        # return self.app