"""
Feature encoding functions
"""

def encode_age_group(age_group_label: str) -> int:
    """
    Convert age group label to numeric
    PDF: age_group (Ordinal)
    """
    mapping = {
        "Under 20": 0,
        "20-24": 1,
        "25-29": 2,
        "30-34": 3,
        "35-39": 4,
        "40-44": 5,
        "45-49": 6,
        "50-54": 7,  # User example from earlier
        "55-59": 8,
        "60-64": 9,
        "65-69": 10,
        "70-74": 11,
        "75-79": 12,
        "80-84": 13,
        "85+": 14,
        "Unknown": -1,
    }
    return mapping.get(age_group_label, -1)


def encode_grade(grade_label: str) -> int:
    """
    Harmonize grade to 1-4 scale
    """
    mapping = {
        "Grade I": 1,
        "Grade II": 2,
        "Grade III": 3,
        "Grade IV": 4,
        "Well differentiated": 1,
        "Moderately differentiated": 2,
        "Poorly differentiated": 3,
        "Undifferentiated": 4,
        "Unknown": -1,
    }
    return mapping.get(grade_label, -1)


def encode_stage(stage_label: str) -> int:
    """
    Summary Stage 2000
    """
    mapping = {
        "In situ": 0,
        "Localized": 1,
        "Regional": 2,
        "Distant": 3,
        "Unknown": -1,
    }
    return mapping.get(stage_label, -1)


def encode_cancer_site(site_label: str) -> int:
    """
    Map cancer type to category index
    """
    # Top 20 cancer sites 
    mapping = {
        "Breast": 1,
        "Lung": 2,
        "Prostate": 3,
        "Colon": 4,
        "Rectum": 5,
        "Melanoma": 6,
        "Bladder": 7,
        "Non-Hodgkin Lymphoma": 8,
        "Kidney": 9,
        "Leukemia": 10,
        "Pancreas": 11,
        "Thyroid": 12,
        "Liver": 13,
        "Ovary": 14,
        "Stomach": 15,
        "Esophagus": 16,
        "Brain": 17,
        "Cervix": 18,
        "Uterus": 19,
        "Other": 99,
    }
    return mapping.get(site_label, 99)