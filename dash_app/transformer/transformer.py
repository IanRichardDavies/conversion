"""Module which contains the DataTransformer object, which is responsible for transforming the 
input dataframe.
"""

# package imports
import numpy as np
import pandas as pd
from typing import Any


class DataTransformer:
    def __init__(
        self,
        underwriting_margin: float = 0.03,
        discount_rate: float = 0.1,
        ltv_cac_ratio: float = 3.0,
    ):
        self.underwriting_margin = underwriting_margin
        self.discount_rate = discount_rate
        self.ltv_cac_ratio = ltv_cac_ratio

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        data = self._calculate_underwriting_profit(data)
        data = self._calculate_pv(data)
        return data

    def _calculate_underwriting_profit(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate underwriting profit."""
        data["underwriting_profit"] = data["gross_premiums"] * self.underwriting_margin
        data["monthly_underwriting_profit"] = data["monthly_premiums"] * self.underwriting_margin
        return data

    def _calculate_pv(self, data: pd.DataFrame) -> pd.DataFrame:
        """Discount underwriting cash flow to calculate present value."""
        def pv_helper(row)-> Any:
            return sum(
                row["monthly_underwriting_profit"] / ((1 + self.discount_rate / 12) ** i) 
                for i in range(1, int(row["num_premiums"]) + 1)
            )

        data["pv"] = np.where(
            ((data["application_completed"] == 1) & (~data["num_premiums"].isnull())),
            data.apply(lambda x: pv_helper(x), axis = 1),
            0
        )
        return data