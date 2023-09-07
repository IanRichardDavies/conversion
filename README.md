Customer Conversion Analysis
============================

Quick Start
-----------

- Clone repo
- Install environment using conda: `conda env create -f environment.yml`
- Activate environment: `conda activate conversion`
- Open template notebook: `dashboard_template.ipynb`


Assumptions Used
----------------

**underwriting_profit** 
Estimated a profit margin of 3% on monthly premiums.

**discount_rate**
Discount rate of 10% was used to calculate the present value of a stream of future cash flows.

**ltv_cac_ratio**
This is ratio of lifetive customer value (calculated by expected present value of) cash flows to customer acquisition costs. As a guidelines to ensure an adequate return on investment, a 3.0 ratio was used.


Methodology
-----------

The data transformation, calculation and visualisation logic is housed in `dashboard/dashboard.py`.

The first method called by a user is `import_data()`, which performs the following steps:
- Check that columns containing segmentation variables and primary keys do not contain nulls.  Errors are logged back to user.
- Use existing data to create columns that will better enable segment-level aggregation.
- Bucket values in "User Age" and "Lead Source" for more practical analysis.
- Estimate underwriting profit and present value.

The second method called by a user is `display_conversion(segment)`, which performs the following steps:
- Aggregate the cleaned input dataframe by segment (using "overall portfolio" if segment argument is left blank) to calculate the various intermediary customer conversion metrics: application completion rate, policy approval rate, policy purchase rate, and overall customer conversion rate.
- Create a dynamic plotly chart that illustrates each of the four rates for each segment.

The third method called by a user is `display_profitability(segment)`, which performs the following steps:
- Aggregate the cleaned input dataframe by segment (using "overall portfolio" if segment argument is left blank) to calculate various profitablity metrics: customer conversion rate, present value (the average present value of profits on premiums for a purchased policy), total present value (the present value of profits on premiums for all purchased policies in the segment), and expected present value (present value multipled by customer conversion rate).
- Create a dynamic plotly chart that illustrates the profitablity metrics for each segment.

The fourth method called by a user is `calculate_optimal_cac(segment)`, which performs the following steps:
- Performs the same aggregations and profitability calculations as `display_profitability(segment)`.
- Calculate the maximum customer acquisition cost for each segments and formats the output into a readable dataframe.


Future Enhancements
-------------------

This analysis can be improved with the following enhancements:

- Unit test suite to verify that implementation properly reflects intent.
- Improved repo structure to enable easier distribution, installation, and use.
- Ground assumptions on historical company data.
- Increased sample size over a longer time period to understand the difference in behavior between vintages.
- Change visualization from plotly to Dash app to better enable filtering and the combination of several segments within a view.
- If available, include more fields in the dataset.
- Understand the payment structure in each channel (for example: do we pay affiliates a bounty per policy purchased?  Or application submitted?)
