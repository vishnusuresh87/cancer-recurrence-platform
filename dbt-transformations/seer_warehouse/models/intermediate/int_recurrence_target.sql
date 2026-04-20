{{
    config(
        materialized='ephemeral'
    )
}}

-- Intermediate: Create recurrence target variable
-- first_primaries: seq=0 (one primary only) + seq=1 (1st of multiple)
-- subsequent_cancers: seq>=2 (2nd primary and beyond)
-- Recurrence = patient gets same-site cancer again within 240 months

WITH first_primaries AS (
    SELECT *
    FROM {{ ref('int_features') }}
    WHERE sequence_number IN (0, 1)   -- "One primary only" OR "1st of 2 or more"
),

subsequent_cancers AS (
    SELECT *
    FROM {{ ref('int_features') }}
    WHERE sequence_number >= 2        -- "2nd of 2 or more primaries" and beyond
),

matched_recurrences AS (
    SELECT
        f.patient_id,
        f.year_dx as year_dx_first,
        f.cancer_site as site_first,
        s.year_dx as year_dx_second,
        s.cancer_site as site_second,
        (s.year_dx - f.year_dx) * 12 as gap_months,
        CASE
            WHEN f.cancer_site = s.cancer_site THEN 1
            ELSE 0
        END as same_site
    FROM first_primaries f
    LEFT JOIN subsequent_cancers s
        ON f.patient_id = s.patient_id
        AND s.year_dx > f.year_dx
),

recurrence_flags AS (
    -- GROUP BY patient to handle patients with multiple subsequent cancers
    SELECT
        patient_id,
        MAX(CASE
            WHEN same_site = 1 AND gap_months >= 3 THEN 1
            ELSE 0
        END) as recurred,
        -- Use NULL (not 999) so COALESCE falls back to survival_months
        MIN(CASE
            WHEN same_site = 1 AND gap_months >= 3 THEN gap_months
            ELSE NULL
        END) as time_to_recurrence_months
    FROM matched_recurrences
    GROUP BY patient_id
)

SELECT
    f.*,
    COALESCE(r.recurred, 0) as recurred,
    -- For non-recurrent: time = survival_months (how long they survived without recurrence)
    -- For recurrent: time = months until recurrence
    COALESCE(r.time_to_recurrence_months::NUMERIC, f.survival_months) as time_to_recurrence_months
FROM first_primaries f
LEFT JOIN recurrence_flags r ON f.patient_id = r.patient_id
