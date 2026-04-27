{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['patient_id']},
            {'columns': ['recurred']},
        ]
    )
}}

-- Marts: Final training dataset with RAW STRING features + target for Scikit-Learn Pipeline

SELECT
    patient_id,
    
    -- Target variables
    recurred,
    time_to_recurrence_months,

    -- RAW text fields that mirror the frontend
    cancer_site,
    age_group,
    sex,
    tumor_grade,
    summary_stage as harmonized_stage,
    tumor_size_mm,
    histology_code as histology_broad,
    laterality,
    nodes_positive,
    nodes_examined,
    
    -- DB has strings for metastasis, cast to boolean to match frontend
    CASE WHEN mets_bone LIKE '%Yes%' THEN TRUE ELSE FALSE END as mets_bone,
    CASE WHEN mets_liver LIKE '%Yes%' THEN TRUE ELSE FALSE END as mets_liver,
    CASE WHEN mets_lung LIKE '%Yes%' THEN TRUE ELSE FALSE END as mets_lung,
    CASE WHEN mets_brain LIKE '%Yes%' THEN TRUE ELSE FALSE END as mets_brain,
    lvi,
    
    -- Treatment: cast to match frontend
    CASE WHEN surgery_code IS NOT NULL AND surgery_code != '0' THEN TRUE ELSE FALSE END as surgery_performed,
    radiation_type,
    CASE WHEN chemotherapy LIKE '%Yes%' THEN TRUE ELSE FALSE END as chemotherapy,
    surgery_radiation_sequence,
    days_to_treatment,
    
    -- Breast
    er_status,
    pr_status,
    her2_status,
    
    -- Socioeconomic
    marital_status,
    income_level,
    rural_urban

FROM {{ ref('int_recurrence_target') }}

WHERE
    time_to_recurrence_months > 0
    AND time_to_recurrence_months <= 240
