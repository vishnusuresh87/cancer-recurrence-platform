{{
    config(
        materialized='ephemeral'
    )
}}

-- Intermediate: Engineer features

WITH base AS (
    SELECT * FROM {{ ref('stg_seer_raw') }}
),

engineered AS (
    SELECT
        *,
        
        -- age_numeric (midpoint of age group)
        CASE age_group
            WHEN '00 years' THEN 0
            WHEN '01-04 years' THEN 2.5
            WHEN '05-09 years' THEN 7
            WHEN '10-14 years' THEN 12
            WHEN '15-19 years' THEN 17
            WHEN '20-24 years' THEN 22
            WHEN '25-29 years' THEN 27
            WHEN '30-34 years' THEN 32
            WHEN '35-39 years' THEN 37
            WHEN '40-44 years' THEN 42
            WHEN '45-49 years' THEN 47
            WHEN '50-54 years' THEN 52
            WHEN '55-59 years' THEN 57
            WHEN '60-64 years' THEN 62
            WHEN '65-69 years' THEN 67
            WHEN '70-74 years' THEN 72
            WHEN '75-79 years' THEN 77
            WHEN '80-84 years' THEN 82
            WHEN '85+ years' THEN 87
            ELSE 50
        END as age_numeric,
        
        -- node_ratio
        CASE
            WHEN nodes_examined > 0 THEN nodes_positive::NUMERIC / nodes_examined::NUMERIC
            ELSE -1
        END as node_ratio,
        
        -- harmonized_grade (1-4)
        CASE
            WHEN tumor_grade LIKE '%Grade I%' OR tumor_grade LIKE '%Well%' THEN 1
            WHEN tumor_grade LIKE '%Grade II%' OR tumor_grade LIKE '%Moderately%' THEN 2
            WHEN tumor_grade LIKE '%Grade III%' OR tumor_grade LIKE '%Poorly%' THEN 3
            WHEN tumor_grade LIKE '%Grade IV%' OR tumor_grade LIKE '%Undifferentiated%' THEN 4
            ELSE -1
        END as harmonized_grade,
        
        -- harmonized_stage (Summary Stage 2000)
        CASE summary_stage
            WHEN 'In situ' THEN 0
            WHEN 'Localized' THEN 1
            WHEN 'Regional' THEN 2
            WHEN 'Distant' THEN 3
            ELSE -1
        END as harmonized_stage,
        
        -- surgery_performed (SEER code 0 = no surgery)
        CASE
            WHEN surgery_code IS NOT NULL AND surgery_code != '0' THEN TRUE
            ELSE FALSE
        END as surgery_performed,
        
        -- chemotherapy_binary
        CASE
            WHEN chemotherapy LIKE '%Yes%' THEN TRUE
            ELSE FALSE
        END as chemotherapy_binary,
        
        -- radiation_binary
        CASE
            WHEN radiation_type IS NOT NULL AND radiation_type != 'None' THEN TRUE
            ELSE FALSE
        END as radiation_binary,
        
        -- any_metastasis_at_dx
        CASE
            WHEN mets_bone LIKE '%Yes%'
              OR mets_brain LIKE '%Yes%'
              OR mets_liver LIKE '%Yes%'
              OR mets_lung LIKE '%Yes%'
            THEN TRUE
            ELSE FALSE
        END as any_metastasis_at_dx,
        
        -- breast_receptor_subtype
        CASE
            WHEN cancer_site NOT LIKE '%Breast%' THEN 'Not Breast Cancer'
            WHEN (er_status LIKE '%Positive%' OR pr_status LIKE '%Positive%')
              AND her2_status LIKE '%Positive%' THEN 'HR+/HER2+'
            WHEN (er_status LIKE '%Positive%' OR pr_status LIKE '%Positive%')
              AND her2_status LIKE '%Negative%' THEN 'HR+/HER2-'
            WHEN (er_status LIKE '%Negative%' AND pr_status LIKE '%Negative%')
              AND her2_status LIKE '%Positive%' THEN 'HR-/HER2+'
            WHEN (er_status LIKE '%Negative%' AND pr_status LIKE '%Negative%')
              AND her2_status LIKE '%Negative%' THEN 'Triple Negative'
            ELSE 'Unknown'
        END as breast_receptor_subtype
        
    FROM base
),

treatment_intensity AS (
    SELECT
        *,
        -- treatment_intensity (0-3)
        (surgery_performed::INTEGER +
         chemotherapy_binary::INTEGER +
         radiation_binary::INTEGER) as treatment_intensity
    FROM engineered
)

SELECT * FROM treatment_intensity


