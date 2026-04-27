from enum import Enum

class CancerSite(str, Enum):
    BREAST = "Breast"
    LUNG = "Lung and Bronchus"
    COLORECTAL = "Colon and Rectum"
    PROSTATE = "Prostate"
    MELANOMA = "Melanoma of the Skin"
    BLADDER = "Urinary Bladder"
    LYMPHOMA = "Non-Hodgkin Lymphoma"
    KIDNEY = "Kidney and Renal Pelvis"
    PANCREAS = "Pancreas"
    THYROID = "Thyroid"
    LIVER = "Liver and Intrahepatic Bile Duct"
    OVARY = "Ovary"
    STOMACH = "Stomach"
    ESOPHAGUS = "Esophagus"
    BRAIN = "Brain and Other Nervous System"
    OTHER = "Other"

class AgeGroup(str, Enum):
    YEARS_00 = "00 years"
    YEARS_01_04 = "01-04 years"
    YEARS_05_09 = "05-09 years"
    YEARS_10_14 = "10-14 years"
    YEARS_15_19 = "15-19 years"
    YEARS_20_24 = "20-24 years"
    YEARS_25_29 = "25-29 years"
    YEARS_30_34 = "30-34 years"
    YEARS_35_39 = "35-39 years"
    YEARS_40_44 = "40-44 years"
    YEARS_45_49 = "45-49 years"
    YEARS_50_54 = "50-54 years"
    YEARS_55_59 = "55-59 years"
    YEARS_60_64 = "60-64 years"
    YEARS_65_69 = "65-69 years"
    YEARS_70_74 = "70-74 years"
    YEARS_75_79 = "75-79 years"
    YEARS_80_84 = "80-84 years"
    YEARS_85_PLUS = "85+ years"

class Sex(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"

class TumorGrade(str, Enum):
    GRADE_1 = "Grade I"
    GRADE_2 = "Grade II"
    GRADE_3 = "Grade III"
    GRADE_4 = "Grade IV"
    UNKNOWN = "Unknown"

class HarmonizedStage(str, Enum):
    IN_SITU = "In situ"
    LOCALIZED = "Localized"
    REGIONAL = "Regional"
    DISTANT = "Distant"
    UNKNOWN = "Unknown"

class Laterality(str, Enum):
    LEFT = "Left"
    RIGHT = "Right"
    BILATERAL = "Bilateral"
    PAIRED_SITE = "Paired site"
    UNPAIRED_SITE = "Not a paired site"
    UNKNOWN = "Unknown"

class HistologyBroad(str, Enum):
    ADENOCARCINOMA = "Adenocarcinoma"
    SQUAMOUS = "Squamous cell carcinoma"
    DUCTAL = "Ductal carcinoma"
    LOBULAR = "Lobular carcinoma"
    SMALL_CELL = "Small cell carcinoma"
    LARGE_CELL = "Large cell carcinoma"
    OTHER = "Other"
    UNKNOWN = "Unknown"

class RadiationType(str, Enum):
    NONE = "None"
    EXTERNAL = "External Beam"
    BRACHYTHERAPY = "Brachytherapy"
    COMBINED = "Combined"
    OTHER = "Other"

class SurgRadSequence(str, Enum):
    NONE = "No radiation and/or no surgery"
    SURG_BEFORE_RAD = "Surgery before radiation"
    RAD_BEFORE_SURG = "Radiation before surgery"
    CONCURRENT = "Radiation before and after surgery"
    UNKNOWN = "Unknown"

class BiomarkerStatus(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    BORDERLINE = "Borderline"
    UNKNOWN = "Unknown"

class MaritalStatus(str, Enum):
    MARRIED = "Married"
    SINGLE = "Single"
    WIDOWED = "Widowed"
    DIVORCED = "Divorced"
    SEPARATED = "Separated"
    UNKNOWN = "Unknown"

class IncomeLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    UNKNOWN = "Unknown"

class RuralUrban(str, Enum):
    URBAN = "Urban"
    RURAL = "Rural"
    UNKNOWN = "Unknown"

class LVIStatus(str, Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    UNKNOWN = "Unknown"
