export interface User {
    user_id: string;
    email: string;
    role: string;
    created_at: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    expires_in: number;
    user: User;
}

export interface PredictionRequest {
    cancer_site: string;
    age_group: string;
    sex: string;
    tumor_grade: string;
    harmonized_stage: string;
    tumor_size_mm: number;
    histology_broad: string;
    laterality: string;
    nodes_positive: number;
    nodes_examined: number;
    mets_bone: boolean;
    mets_liver: boolean;
    mets_lung: boolean;
    mets_brain: boolean;
    lvi: string;
    surgery_performed: boolean;
    radiation_type: string;
    chemotherapy: boolean;
    surgery_radiation_sequence: string;
    days_to_treatment: string;
    er_status: string;
    pr_status: string;
    her2_status: string;
    marital_status: string;
    income_level: string;
    rural_urban: string;
    query_years: number;
}

export interface PredictionResponse {
    prediction_id: string;
    probability_pct: number;
    risk_level: string;
    interpretation: string;
    model_version: string;
    survival_curve: Array<{
        months: number;
        years: number;
        recurrence_probability_pct: number;
    }>;
    timestamp: string;
}

export interface PredictionHistoryItem {
    prediction_id: string;
    created_at: string;
    probability_pct: number;
    risk_level: string;
    model_version: string;
}
