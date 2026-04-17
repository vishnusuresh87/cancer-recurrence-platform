"""Derived feature calculation helpers used by feature-service."""


def calculate_node_ratio(nodes_positive: int, nodes_examined: int) -> float:
    """Return positive/examined node ratio; -1.0 when denominator is invalid."""
    if nodes_examined <= 0:
        return -1.0
    return nodes_positive / nodes_examined


def calculate_treatment_intensity(
    surgery_performed: bool,
    chemotherapy: bool,
    radiation_type: str,
) -> int:
    """Composite 0-3 treatment intensity score."""
    intensity = 0
    if surgery_performed:
        intensity += 1
    if chemotherapy:
        intensity += 1
    if radiation_type not in ["None", "Unknown"]:
        intensity += 1
    return intensity


def derive_breast_receptor_subtype(
    er_status: str,
    pr_status: str,
    her2_status: str,
) -> str:
    """Derive breast receptor subtype from ER/PR/HER2 status."""
    if er_status == "N/A" or pr_status == "N/A" or her2_status == "N/A":
        return "Not Breast Cancer"

    er = er_status == "Positive"
    pr = pr_status == "Positive"
    her2 = her2_status == "Positive"

    if (er or pr) and her2:
        return "HR+/HER2+"
    if (er or pr) and not her2:
        return "HR+/HER2-"
    if not (er or pr) and her2:
        return "HR-/HER2+"
    return "Triple Negative"


def check_any_metastasis(
    mets_bone: bool,
    mets_liver: bool,
    mets_lung: bool,
    mets_brain: bool,
) -> bool:
    """Return True if any metastatic site is present at diagnosis."""
    return any([mets_bone, mets_liver, mets_lung, mets_brain])