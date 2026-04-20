{{
    config(
        materialized='view'
    )
}}

-- Staging: Clean and standardize raw SEER data
-- NOTE: SEER exports use text labels (not numeric codes) for many fields.
-- All CASTs below are written defensively to handle this.

SELECT
    -- IDs
    "Patient ID" as patient_id,

    -- Sequence number: SEER exports as text labels
    -- 'One primary only' → 0, '1st of 2...' → 1, '2nd of 2...' → 2, etc.
    CASE
        WHEN "Sequence number" = 'One primary only' THEN 0
        WHEN "Sequence number" ~ '^\d'
            THEN CAST(REGEXP_REPLACE("Sequence number", '^(\d+).*', '\1') AS INTEGER)
        ELSE NULL
    END as sequence_number,

    "First malignant primary indicator" as first_primary,

    -- Demographics
    "Age recode with <1 year olds and 90+" as age_group,
    "Sex" as sex,
    "Marital status at diagnosis" as marital_status,
    "Median household income inflation adj to 2023" as income_level,
    "Rural-Urban Continuum Code" as rural_urban,

    -- Cancer characteristics
    "Site recode ICD-O-3/WHO 2008" as cancer_site,
    CAST("Histologic Type ICD-O-3" AS TEXT) as histology_code,
    "Behavior recode for analysis" as behavior,
    "Grade Recode (thru 2017)" as tumor_grade,
    "Summary stage 2000 (1998-2017)" as summary_stage,
    "Laterality" as laterality,

    -- Tumor details
    -- tumor_size is TEXT in DB (has labels like 'Tumor Size Not Consistent...')
    CASE
        WHEN "Tumor Size Over Time Recode (1988+)" ~ '^[0-9]+(\.[0-9]+)?$'
        THEN CAST("Tumor Size Over Time Recode (1988+)" AS NUMERIC)
        ELSE NULL
    END as tumor_size_mm,
    CAST("Regional nodes examined (1988+)" AS INTEGER) as nodes_examined,
    CAST("Regional nodes positive (1988+)" AS INTEGER) as nodes_positive,

    -- Metastasis
    "SEER Combined Mets at DX-bone (2010+)" as mets_bone,
    "SEER Combined Mets at DX-brain (2010+)" as mets_brain,
    "SEER Combined Mets at DX-liver (2010+)" as mets_liver,
    "SEER Combined Mets at DX-lung (2010+)" as mets_lung,
    "Lymph-vascular Invasion (2004+ varying by schema)" as lvi,

    -- Treatment
    CAST("RX Summ--Surg Prim Site (1998+)" AS TEXT) as surgery_code,
    "Radiation recode" as radiation_type,
    "Chemotherapy recode (yes, no/unk)" as chemotherapy,
    CAST("RX Summ--Surg/Rad Seq" AS TEXT) as surgery_radiation_sequence,
    CAST("Time from diagnosis to treatment in days recode" AS TEXT) as days_to_treatment,

    -- Breast cancer specific
    "ER Status Recode Breast Cancer (1990+)" as er_status,
    "PR Status Recode Breast Cancer (1990+)" as pr_status,
    "Derived HER2 Recode (2010+)" as her2_status,

    -- Outcomes
    CAST("Year of diagnosis" AS INTEGER) as year_dx,

    -- Survival months: safe cast in case of text labels
    CASE
        WHEN CAST("Survival months" AS TEXT) ~ '^[0-9]+(\.[0-9]+)?$'
        THEN CAST("Survival months" AS NUMERIC)
        ELSE NULL
    END as survival_months,

    "Vital status recode (study cutoff used)" as vital_status

FROM {{ source('seer', 'raw_seer') }}
WHERE "Behavior recode for analysis" = 'Malignant'  -- Only malignant tumors
