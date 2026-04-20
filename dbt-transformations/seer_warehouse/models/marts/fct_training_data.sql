{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['patient_id']},
            {'columns': ['recurred']},
        ]
    )
}}

-- Marts: Final training dataset with all 28 features + target

SELECT
    -- IDs
    patient_id,
    
    -- 28 Model Features (in order)
    age_numeric,                    -- 1
    sex,                            -- 2
    cancer_site,                    -- 3
    harmonized_grade,               -- 4
    harmonized_stage,               -- 5
    tumor_size_mm,                  -- 6
    histology_code,                 -- 7
    laterality,                     -- 8
    nodes_positive,                 -- 9
    node_ratio,                     -- 10
    any_metastasis_at_dx,           -- 11
    mets_bone,                      -- 12
    mets_liver,                     -- 13
    mets_lung,                      -- 14
    mets_brain,                     -- 15
    lvi,                            -- 16
    surgery_performed,              -- 17
    radiation_type,                 -- 18
    chemotherapy_binary,            -- 19
    treatment_intensity,            -- 20
    surgery_radiation_sequence,     -- 21
    days_to_treatment,              -- 22
    er_status,                      -- 23
    pr_status,                      -- 24
    her2_status,                    -- 25
    breast_receptor_subtype,        -- 26
    marital_status,                 -- 27
    income_level,                   -- 28
    
    -- Target variables
    recurred,                       -- Binary: did recurrence happen?
    time_to_recurrence_months,      -- Survival time
    
    -- Metadata
    year_dx,
    vital_status

FROM {{ ref('int_recurrence_target') }}

WHERE
    -- Data quality filters
    age_numeric >= 0
    AND harmonized_stage >= 0
    AND time_to_recurrence_months > 0
    AND time_to_recurrence_months <= 240  -- Max 20 years


    