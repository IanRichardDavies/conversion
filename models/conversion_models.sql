WITH apps AS (
    SELECT
    record_id
    ,policy_num
    ,product_type
    ,CASE
        WHEN app_start_date IS NOT NULL THEN 1
        ELSE 0
    END AS application_started
    ,CASE
        WHEN app_complete_date IS NOT NULL THEN 1
        ELSE 0
    END AS application_completed
    ,CASE
        WHEN app_decision = 'Approved' THEN 1
        ELSE 0
    END AS application_approved
    ,CASE
        WHEN lead_source IN (
            'Facebook Paid',
            'Google Paid',
            'SEO',
            'Affiliate',
            'Direct'
            ) THEN lead_source
        ELSE 'Other'
    END AS lead_source
    ,'Overall' AS overall
    FROM conversion-398901.google_drive_data.apps
),
policies AS (
    SELECT
    policy_num
    ,CASE
        WHEN purcase_date IS NOT NULL THEN 1
        ELSE 0
    END AS policy_purchased
    ,policy_length * 12 AS num_premiums
    ,monthly_premiums
    ,policy_length * 12 * monthly_premiums AS gross_premiums
    ,coverage
    ,premium_class
    FROM conversion-398901.google_drive_data.policies
),
users AS (
    SELECT
    record_id
    ,user_gender
    ,CASE
        WHEN user_age IS NULL THEN 'Null'
        WHEN user_age <= 30 THEN '<=30'
        WHEN user_age BETWEEN 31 AND 35 THEN '31-35'
        WHEN user_age BETWEEN 36 AND 40 THEN '36-40'
        WHEN user_age BETWEEN 41 AND 50 THEN '41-50'
        WHEN user_age BETWEEN 51 AND 60 THEN '51-60'
        ELSE '61+'
    END AS user_age
    ,CASE
        WHEN user_income IS NULL THEN 'Null'
        WHEN user_income < 30000 THEN '<=30k'
        WHEN user_income BETWEEN 30000 AND 60000 THEN '30-60k'
        WHEN user_income BETWEEN 60001 AND 90000 THEN '60-90k'
        WHEN user_income BETWEEN 90001 AND 120000 THEN '90-120k'
        ELSE '120k+'
    END AS user_income
    FROM conversion-398901.google_drive_data.users
),
conversion AS (
    SELECT 
    apps.*
    ,policies.policy_purchased
    ,policies.num_premiums
    ,policies.gross_premiums
    ,policies.coverage
    ,policies.premium_class
    ,users.user_gender
    ,users.user_age
    ,users.user_income
    FROM apps
    LEFT JOIN policies ON apps.policy_num = policies.policy_num
    LEFT JOIN users ON apps.record_id = users.record_id
)

SELECT * FROM conversion
