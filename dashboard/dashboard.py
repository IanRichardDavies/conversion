"""Module containing utility functions."""

import logging
import numpy as np
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from pandas.errors import SettingWithCopyWarning
from typing import Any

import warnings
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)

load_dotenv()

PROJECT_ID = os.getenv("BQ_KEY")["project_id"]


class Dashboard:
    """TODO"""
    def __init__(
        self,
        underwriting_profit: float = 0.03,
        discount_rate: float = 0.1,
        ltv_cac_ratio: float = 3.0,
    ):
        self.underwriting_margin = underwriting_profit
        self.discount_rate = discount_rate
        self.ltv_cac_ratio = ltv_cac_ratio
        self.non_null_cols = [
            "Record ID",
            "Application Start Date",
            "Product Type",
            "User Age",
            "User Gender",
        ]
        self.required_cols = [
            "Application Complete Date",
            "Application Approval Decision",
            "Policy Purchase Date",
            "Policy Length (Years)",
            "Policy Monthly Premiums",
            "Lead Source",
            "Premium Class",
        ]

    def import_data(self, data: pd.DataFrame) -> None:
        """Validate and clean raw data"""
        if self._validate_input(data):
            self.data = data[self.non_null_cols + self.required_cols].copy()
            self._add_indicator_cols()
            self._clean_lead_source()
            self._clean_user_age()
            self._calculate_underwriting_profit()
            self._calculate_pv()
        else:
            logging.error("Input dataframe is missing required data.")

    def _validate_input(self, data: pd.DataFrame) -> bool:
        try:
            for col in self.non_null_cols:
                assert col in data.columns
                assert not data[col].isnull().values.any()
        except AssertionError as e:
            logging.error(f"Input data failed validation for column: {col}", exc_info=True)
        try:
            for col in self.required_cols:
                assert col in data.columns
        except AssertionError as e:
            logging.error("Input data failed validation", exc_info=True)
        return True
    
    def _add_indicator_cols(self) -> None:
        """Creating indicator cols to enable downstream calculations."""
        self.data["overall portfolio"] = "overall"
        self.data["application_started"] = 1
        self.data["application_completed"] = np.where(~self.data["Application Complete Date"].isnull(), 1, 0)
        self.data["application_approved"] = np.where(self.data["Application Approval Decision"] == 'Approved', 1, 0)
        self.data["policy_purchased"] = np.where(~self.data["Policy Purchase Date"].isnull(), 1, 0)
        self.data["number_of_premiums"] = np.where(
            self.data["application_completed"] == 1,
            self.data["Policy Length (Years)"] * 12,
            0
        ).astype(int)

    def _clean_lead_source(self) -> None:
        """Bin lead source values."""
        self.data["Lead Source"] = np.where(~self.data["Lead Source"].isin(
            [
                "Facebook Paid",
                "Google Paid",
                "SEO",
                "Affiliate",
                "Direct",
            ]
            ), "Other", self.data["Lead Source"]
        )

    def _clean_user_age(self) -> None:
        """Bin user age."""
        bins = [0, 30, 35, 40, 50, 60, 100]
        labels = ["<30", "31-35", "36-40", "41-50", "51-60", "61+"]
        self.data["User Age"] = pd.cut(self.data["User Age"], bins=bins, labels=labels)

    def _calculate_underwriting_profit(self) -> None:
        """Calculate underwriting profit."""
        self.data["gross_premiums"] = np.where(
            self.data["application_completed"] == 1,
            self.data["Policy Length (Years)"] * self.data["Policy Monthly Premiums"] * 12,
            0
        )
        self.data["underwriting_profit"] = self.data["gross_premiums"] * self.underwriting_margin
        self.data["monthly_underwriting_profit"] = self.data["Policy Monthly Premiums"] * self.underwriting_margin

    def _calculate_pv(self) -> None:
        """Discount underwriting cash flow to calculate present value."""
        def pv_helper(row)-> Any:
            return sum(
                row["monthly_underwriting_profit"] / ((1 + self.discount_rate / 12) ** i) 
                for i in range(1, row["number_of_premiums"] + 1)
            )

        self.data["pv"] = np.where(
            self.data["application_completed"] == 1,
            self.data.apply(lambda x: pv_helper(x), axis = 1),
            0
        )

    def display_conversion(
        self,
        segment: str = "overall portfolio",
    ) -> None:
        """Render and display plotly visualizations for app customer conversion."""
        df = self._create_conversion_df(self.data, segment)
        df = self._calculate_conversion_metrics(df)
        self._plot_conversion(df, segment)

    @staticmethod
    def _create_conversion_df(data: pd.DataFrame, category: str) -> pd.DataFrame:
        """Aggregate key stages in application journey by category."""
        filtered = data[
            [
                category,
                "application_started",
                "application_completed",
                "application_approved",
                "policy_purchased",
            ]
        ]
        grouped = filtered.groupby(category).sum()
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
    def _calculate_conversion_metrics(data: pd.DataFrame) -> pd.DataFrame:
        """Calculate conversion metrics."""
        data["app_completion_rate"] = data["application_completed"] / data["application_started"] * 100
        data["approval_rate"] = data["application_approved"] / data["application_completed"] * 100
        data["purchase_rate"] = data["policy_purchased"] / data["application_approved"] * 100
        data["conversion_rate"] = data["policy_purchased"] / data["application_started"] * 100
        return data

    @staticmethod
    def _plot_conversion(df: pd.DataFrame, category: str) -> None:
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
            title=f"Conversion decomposition by {category}",
            xaxis_title=f"{category}",
            yaxis_title="Step completion (%)",
            legend_title="Conversion step",
            font=dict(
                family="Courier New, monospace",
                size=16,
            )
        )
        fig.show()

    def display_profitability(
        self,
        segment: str = "overall portfolio",
    ) -> Any:
        """Render and display plotly visualizations for profitability."""
        df = self._calculate_expected_pv(self.data, segment)
        self._plot_expected_pv(df, segment)


    @staticmethod
    def _calculate_expected_pv(data: pd.DataFrame, category: str) -> pd.DataFrame: 
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

    @staticmethod
    def _plot_expected_pv(df: pd.DataFrame, category: str) -> None:
        fig = px.bar(
            df,
            x=df.index,
            y=df['expected_pv_per_app'],
        )
        fig.update_layout(
            title=f"Expected present value of applications by {category}",
            xaxis_title=f"{category}",
            yaxis_title="Present value per application ($)",
            font=dict(
                family="Courier New, monospace",
                size=16,
            )
        )
        fig.show()

    def calculate_optimal_cac(self, segment: str = "overall portfolio") -> pd.DataFrame:
        df = self._calculate_expected_pv(self.data, segment)
        df = self._format_output(df)
        return df

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
        