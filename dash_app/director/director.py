"""Director Module

Module which houses the class responsible for automated conversion analytics
"""

# Python libraries
from typing import Type

# First Party Imports
from dash_app.data.data_importer import DataImporter
from dash_app.transformer.transformer import DataTransformer
from dash_app.dashviz.dashviz import DashViz


class Director:
    """Director Class
    Object responsibile for exposing functionality of worker objects to the user
    through interfaces.
    """

    def __init__(
        self,
        source: str = "bigquery",
        location: str = "conversion-398901.dbt_idavies.conversion_models",
        underwriting_margin: float = 0.03,
        discount_rate: float = 0.1,
        ltv_cac_ratio: float = 3.0,
        importer: Type[DataImporter] = DataImporter,
        transformer: Type[DataTransformer] = DataTransformer,
        dashviz: Type[DashViz] = DashViz,
    ):
        self.underwriting_margin = underwriting_margin
        self.discount_rate = discount_rate
        self.ltv_cac_ratio = ltv_cac_ratio
        self.importer = importer(source, location)
        self.transformer = transformer(
            underwriting_margin,
            discount_rate,
            ltv_cac_ratio,
        )
        self.dashviz = dashviz()

    def import_data(self):
        self.data = self.importer.import_data()

    def transform(self):
        self.data = self.transformer.transform(self.data)

    def visualize(self):
        # return self.dashviz.visualize(self.data)
        self.dashviz.visualize(data=self.data)