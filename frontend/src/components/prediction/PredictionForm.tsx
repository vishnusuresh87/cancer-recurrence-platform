import React, { useState } from 'react';
import {
    Box,
    Button,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    Slider,
    Typography,
    Grid,
    Paper,
    FormControlLabel,
    Checkbox,
    TextField,
    Divider,
} from '@mui/material';
import { PredictionRequest } from '../../types';

interface Props {
    onSubmit: (data: PredictionRequest) => void;
    loading: boolean;
}

export const PredictionForm: React.FC<Props> = ({ onSubmit, loading }) => {
    const [formData, setFormData] = useState<PredictionRequest>({
        cancer_site: '',
        age_group: '',
        sex: '',
        tumor_grade: '',
        harmonized_stage: '',
        tumor_size_mm: 20,
        histology_broad: '',
        laterality: '',
        nodes_positive: 0,
        nodes_examined: 0,
        mets_bone: false,
        mets_liver: false,
        mets_lung: false,
        mets_brain: false,
        lvi: '',
        surgery_performed: false,
        radiation_type: '',
        chemotherapy: false,
        surgery_radiation_sequence: '',
        days_to_treatment: '',
        er_status: '',
        pr_status: '',
        her2_status: '',
        marital_status: '',
        income_level: '',
        rural_urban: '',
        query_years: 5,
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    const isBreastCancer = formData.cancer_site === 'Breast';

    return (
        <Paper elevation={3} sx={{ p: 4, maxWidth: 900, mx: 'auto' }}>
            <Typography variant="h4" gutterBottom align="center" color="primary">
                Cancer Recurrence Risk Assessment
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 4 }}>
                Complete the form below to get your personalized risk estimate
            </Typography>

            <form onSubmit={handleSubmit}>
                <Grid container spacing={3}>

                    {/* ========== DEMOGRAPHICS ========== */}
                    <Grid item xs={12}>
                        <Typography variant="h6" color="primary">
                            Demographics
                        </Typography>
                        <Divider sx={{ mt: 1 }} />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Cancer Type</InputLabel>
                            <Select
                                label="Cancer Type"
                                value={formData.cancer_site}
                                onChange={(e) => setFormData({ ...formData, cancer_site: e.target.value })}
                            >
                                <MenuItem value="Breast">Breast</MenuItem>
                                <MenuItem value="Lung and Bronchus">Lung</MenuItem>
                                <MenuItem value="Prostate">Prostate</MenuItem>
                                <MenuItem value="Colon and Rectum">Colon/Rectum</MenuItem>
                                <MenuItem value="Melanoma of the Skin">Melanoma</MenuItem>
                                <MenuItem value="Urinary Bladder">Bladder</MenuItem>
                                <MenuItem value="Non-Hodgkin Lymphoma">Non-Hodgkin Lymphoma</MenuItem>
                                <MenuItem value="Kidney and Renal Pelvis">Kidney</MenuItem>
                                <MenuItem value="Pancreas">Pancreas</MenuItem>
                                <MenuItem value="Thyroid">Thyroid</MenuItem>
                                <MenuItem value="Liver and Intrahepatic Bile Duct">Liver</MenuItem>
                                <MenuItem value="Ovary">Ovary</MenuItem>
                                <MenuItem value="Stomach">Stomach</MenuItem>
                                <MenuItem value="Esophagus">Esophagus</MenuItem>
                                <MenuItem value="Brain and Other Nervous System">Brain</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Age at Diagnosis</InputLabel>
                            <Select
                                label="Age at Diagnosis"
                                value={formData.age_group}
                                onChange={(e) => setFormData({ ...formData, age_group: e.target.value })}
                            >
                                <MenuItem value="20-24 years">20-24 years</MenuItem>
                                <MenuItem value="25-29 years">25-29 years</MenuItem>
                                <MenuItem value="30-34 years">30-34 years</MenuItem>
                                <MenuItem value="35-39 years">35-39 years</MenuItem>
                                <MenuItem value="40-44 years">40-44 years</MenuItem>
                                <MenuItem value="45-49 years">45-49 years</MenuItem>
                                <MenuItem value="50-54 years">50-54 years</MenuItem>
                                <MenuItem value="55-59 years">55-59 years</MenuItem>
                                <MenuItem value="60-64 years">60-64 years</MenuItem>
                                <MenuItem value="65-69 years">65-69 years</MenuItem>
                                <MenuItem value="70-74 years">70-74 years</MenuItem>
                                <MenuItem value="75-79 years">75-79 years</MenuItem>
                                <MenuItem value="80-84 years">80-84 years</MenuItem>
                                <MenuItem value="85+ years">85+ years</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Sex</InputLabel>
                            <Select
                                label="Sex"
                                value={formData.sex}
                                onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
                            >
                                <MenuItem value="Male">Male</MenuItem>
                                <MenuItem value="Female">Female</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Marital Status</InputLabel>
                            <Select
                                label="Marital Status"
                                value={formData.marital_status}
                                onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                            >
                                <MenuItem value="Single">Single</MenuItem>
                                <MenuItem value="Married">Married</MenuItem>
                                <MenuItem value="Separated">Separated</MenuItem>
                                <MenuItem value="Divorced">Divorced</MenuItem>
                                <MenuItem value="Widowed">Widowed</MenuItem>
                                <MenuItem value="Unknown">Unknown</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Income Level</InputLabel>
                            <Select
                                label="Income Level"
                                value={formData.income_level}
                                onChange={(e) => setFormData({ ...formData, income_level: e.target.value })}
                            >
                                <MenuItem value="Low">Low (under $50k)</MenuItem>
                                <MenuItem value="Medium">Medium ($50k - $100k)</MenuItem>
                                <MenuItem value="High">High ($100k+)</MenuItem>
                                <MenuItem value="Unknown">Unknown</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Location Type</InputLabel>
                            <Select
                                label="Location Type"
                                value={formData.rural_urban}
                                onChange={(e) => setFormData({ ...formData, rural_urban: e.target.value })}
                            >
                                <MenuItem value="Urban">Urban area</MenuItem>
                                <MenuItem value="Rural">Rural area</MenuItem>
                                <MenuItem value="Unknown">Unknown</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    {/* ========== TUMOR CHARACTERISTICS ========== */}
                    <Grid item xs={12} sx={{ mt: 2 }}>
                        <Typography variant="h6" color="primary">
                            Tumor Characteristics
                        </Typography>
                        <Divider sx={{ mt: 1 }} />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Tumor Grade</InputLabel>
                            <Select
                                label="Tumor Grade"
                                value={formData.tumor_grade}
                                onChange={(e) => setFormData({ ...formData, tumor_grade: e.target.value })}
                            >
                                <MenuItem value="Grade I">Grade I (Well differentiated)</MenuItem>
                                <MenuItem value="Grade II">Grade II (Moderately differentiated)</MenuItem>
                                <MenuItem value="Grade III">Grade III (Poorly differentiated)</MenuItem>
                                <MenuItem value="Grade IV">Grade IV (Undifferentiated)</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Stage at Diagnosis</InputLabel>
                            <Select
                                label="Stage at Diagnosis"
                                value={formData.harmonized_stage}
                                onChange={(e) => setFormData({ ...formData, harmonized_stage: e.target.value })}
                            >
                                <MenuItem value="In situ">In situ (Very early, pre-invasive)</MenuItem>
                                <MenuItem value="Localized">Localized (Confined to organ)</MenuItem>
                                <MenuItem value="Regional">Regional (Spread to nearby lymph nodes/tissue)</MenuItem>
                                <MenuItem value="Distant">Distant (Metastatic disease)</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Tumor Size (mm)"
                            type="number"
                            value={formData.tumor_size_mm}
                            onChange={(e) => setFormData({ ...formData, tumor_size_mm: parseInt(e.target.value) || 0 })}
                            inputProps={{ min: 0, max: 999 }}
                            required
                            helperText="Enter tumor size in millimeters"
                        />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Histology Type</InputLabel>
                            <Select
                                label="Histology Type"
                                value={formData.histology_broad}
                                onChange={(e) => setFormData({ ...formData, histology_broad: e.target.value })}
                            >
                                <MenuItem value="Adenocarcinoma">Adenocarcinoma</MenuItem>
                                <MenuItem value="Squamous cell carcinoma">Squamous cell carcinoma</MenuItem>
                                <MenuItem value="Ductal carcinoma">Ductal carcinoma</MenuItem>
                                <MenuItem value="Lobular carcinoma">Lobular carcinoma</MenuItem>
                                <MenuItem value="Small cell carcinoma">Small cell carcinoma</MenuItem>
                                <MenuItem value="Large cell carcinoma">Large cell carcinoma</MenuItem>
                                <MenuItem value="Other">Other/Unknown</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Laterality</InputLabel>
                            <Select
                                label="Laterality"
                                value={formData.laterality}
                                onChange={(e) => setFormData({ ...formData, laterality: e.target.value })}
                            >
                                <MenuItem value="Right">Right</MenuItem>
                                <MenuItem value="Left">Left</MenuItem>
                                <MenuItem value="Bilateral">Bilateral</MenuItem>
                                <MenuItem value="Not a paired site">Not applicable</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Lymphovascular Invasion</InputLabel>
                            <Select
                                label="Lymphovascular Invasion"
                                value={formData.lvi}
                                onChange={(e) => setFormData({ ...formData, lvi: e.target.value })}
                            >
                                <MenuItem value="Present">Present</MenuItem>
                                <MenuItem value="Absent">Not present</MenuItem>
                                <MenuItem value="Unknown">Unknown</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    {/* ========== LYMPH NODES ========== */}
                    <Grid item xs={12} sx={{ mt: 2 }}>
                        <Typography variant="h6" color="primary">
                            Lymph Node Status
                        </Typography>
                        <Divider sx={{ mt: 1 }} />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Lymph Nodes Examined"
                            type="number"
                            value={formData.nodes_examined}
                            onChange={(e) => setFormData({ ...formData, nodes_examined: parseInt(e.target.value) || 0 })}
                            inputProps={{ min: 0, max: 90 }}
                            required
                            helperText="Total nodes removed and examined"
                        />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <TextField
                            fullWidth
                            label="Positive Lymph Nodes"
                            type="number"
                            value={formData.nodes_positive}
                            onChange={(e) => setFormData({ ...formData, nodes_positive: parseInt(e.target.value) || 0 })}
                            inputProps={{ min: 0, max: formData.nodes_examined }}
                            required
                            helperText="Number of nodes with cancer"
                        />
                    </Grid>

                    {/* ========== METASTASIS ========== */}
                    <Grid item xs={12} sx={{ mt: 2 }}>
                        <Typography variant="h6" color="primary">
                            Metastasis at Diagnosis
                        </Typography>
                        <Divider sx={{ mt: 1 }} />
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={formData.mets_bone}
                                    onChange={(e) => setFormData({ ...formData, mets_bone: e.target.checked })}
                                />
                            }
                            label="Bone metastasis"
                        />
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={formData.mets_liver}
                                    onChange={(e) => setFormData({ ...formData, mets_liver: e.target.checked })}
                                />
                            }
                            label="Liver metastasis"
                        />
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={formData.mets_lung}
                                    onChange={(e) => setFormData({ ...formData, mets_lung: e.target.checked })}
                                />
                            }
                            label="Lung metastasis"
                        />
                    </Grid>

                    <Grid item xs={12} sm={6} md={3}>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={formData.mets_brain}
                                    onChange={(e) => setFormData({ ...formData, mets_brain: e.target.checked })}
                                />
                            }
                            label="Brain metastasis"
                        />
                    </Grid>

                    {/* ========== TREATMENT ========== */}
                    <Grid item xs={12} sx={{ mt: 2 }}>
                        <Typography variant="h6" color="primary">
                            Treatment Received
                        </Typography>
                        <Divider sx={{ mt: 1 }} />
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={formData.surgery_performed}
                                    onChange={(e) => setFormData({ ...formData, surgery_performed: e.target.checked })}
                                />
                            }
                            label="Surgery performed"
                        />
                    </Grid>

                    <Grid item xs={12} sm={4}>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={formData.chemotherapy}
                                    onChange={(e) => setFormData({ ...formData, chemotherapy: e.target.checked })}
                                />
                            }
                            label="Chemotherapy"
                        />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Radiation Type</InputLabel>
                            <Select
                                label="Radiation Type"
                                value={formData.radiation_type}
                                onChange={(e) => setFormData({ ...formData, radiation_type: e.target.value })}
                            >
                                <MenuItem value="None">None</MenuItem>
                                <MenuItem value="External Beam">Beam radiation</MenuItem>
                                <MenuItem value="Brachytherapy">Radioactive implants (Brachytherapy)</MenuItem>
                                <MenuItem value="Combined">Combination</MenuItem>
                                <MenuItem value="Other">Other</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Surgery & Radiation Sequence</InputLabel>
                            <Select
                                label="Surgery & Radiation Sequence"
                                value={formData.surgery_radiation_sequence}
                                onChange={(e) => setFormData({ ...formData, surgery_radiation_sequence: e.target.value })}
                            >
                                <MenuItem value="No radiation and/or no surgery">No radiation/surgery</MenuItem>
                                <MenuItem value="Radiation before surgery">Radiation before surgery</MenuItem>
                                <MenuItem value="Surgery before radiation">Surgery before radiation</MenuItem>
                                <MenuItem value="Radiation before and after surgery">Radiation before and after surgery</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                        <FormControl fullWidth required>
                            <InputLabel>Time to Treatment</InputLabel>
                            <Select
                                label="Time to Treatment"
                                value={formData.days_to_treatment}
                                onChange={(e) => setFormData({ ...formData, days_to_treatment: e.target.value })}
                            >
                                <MenuItem value="0-30 days">0-30 days</MenuItem>
                                <MenuItem value="31-90 days">31-90 days</MenuItem>
                                <MenuItem value="91+ days">91+ days</MenuItem>
                                <MenuItem value="Unknown">Unknown</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>

                    {/* ========== BREAST CANCER SPECIFIC ========== */}
                    {isBreastCancer && (
                        <>
                            <Grid item xs={12} sx={{ mt: 2 }}>
                                <Typography variant="h6" color="primary">
                                    Breast Cancer Biomarkers
                                </Typography>
                                <Divider sx={{ mt: 1 }} />
                            </Grid>

                            <Grid item xs={12} sm={4}>
                                <FormControl fullWidth required>
                                    <InputLabel>ER Status</InputLabel>
                                    <Select
                                        label="ER Status"
                                        value={formData.er_status}
                                        onChange={(e) => setFormData({ ...formData, er_status: e.target.value })}
                                    >
                                        <MenuItem value="Positive">Positive</MenuItem>
                                        <MenuItem value="Negative">Negative</MenuItem>
                                        <MenuItem value="Borderline">Borderline</MenuItem>
                                        <MenuItem value="Unknown">Unknown</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid item xs={12} sm={4}>
                                <FormControl fullWidth required>
                                    <InputLabel>PR Status</InputLabel>
                                    <Select
                                        label="PR Status"
                                        value={formData.pr_status}
                                        onChange={(e) => setFormData({ ...formData, pr_status: e.target.value })}
                                    >
                                        <MenuItem value="Positive">Positive</MenuItem>
                                        <MenuItem value="Negative">Negative</MenuItem>
                                        <MenuItem value="Borderline">Borderline</MenuItem>
                                        <MenuItem value="Unknown">Unknown</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            <Grid item xs={12} sm={4}>
                                <FormControl fullWidth required>
                                    <InputLabel>HER2 Status</InputLabel>
                                    <Select
                                        label="HER2 Status"
                                        value={formData.her2_status}
                                        onChange={(e) => setFormData({ ...formData, her2_status: e.target.value })}
                                    >
                                        <MenuItem value="Positive">Positive</MenuItem>
                                        <MenuItem value="Negative">Negative</MenuItem>
                                        <MenuItem value="Borderline">Borderline</MenuItem>
                                        <MenuItem value="Unknown">Unknown</MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>
                        </>
                    )}

                    {!isBreastCancer && (
                        <>
                            <Grid item xs={12} sm={4} sx={{ display: 'none' }}>
                                <input type="hidden" value="N/A" />
                            </Grid>
                        </>
                    )}

                    {/* ========== PREDICTION TIMEFRAME ========== */}
                    <Grid item xs={12} sx={{ mt: 3 }}>
                        <Typography variant="h6" color="primary">
                            Prediction Timeframe
                        </Typography>
                        <Divider sx={{ mt: 1 }} />
                    </Grid>

                    <Grid item xs={12}>
                        <Typography gutterBottom>
                            Predict recurrence risk within: <strong>{formData.query_years} years</strong>
                        </Typography>
                        <Slider
                            value={formData.query_years}
                            onChange={(_, value) => setFormData({ ...formData, query_years: value as number })}
                            min={1}
                            max={20}
                            marks={[
                                { value: 1, label: '1yr' },
                                { value: 5, label: '5yr' },
                                { value: 10, label: '10yr' },
                                { value: 15, label: '15yr' },
                                { value: 20, label: '20yr' },
                            ]}
                            valueLabelDisplay="auto"
                            sx={{ mt: 2 }}
                        />
                    </Grid>

                    {/* ========== SUBMIT BUTTON ========== */}
                    <Grid item xs={12}>
                        <Button
                            type="submit"
                            variant="contained"
                            size="large"
                            fullWidth
                            disabled={loading}
                            sx={{ mt: 3, py: 1.5, fontSize: '1.1rem' }}
                        >
                            {loading ? 'Calculating Risk...' : 'Get Prediction'}
                        </Button>
                    </Grid>

                    {/* Disclaimer */}
                    <Grid item xs={12}>
                        <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                                This prediction is based on statistical models and should not replace professional medical advice.
                                Consult with your healthcare provider to interpret these results in the context of your specific situation.
                            </Typography>
                        </Box>
                    </Grid>
                </Grid>
            </form>
        </Paper>
    );
};


