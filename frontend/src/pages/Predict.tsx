import React, { useState } from 'react';
import { Container, Box, Alert } from '@mui/material';
import { PredictionForm } from '../components/prediction/PredictionForm';
import { PredictionResult } from '../components/prediction/PredictionResult';
import { predictApi } from '../services/api';
import { PredictionRequest, PredictionResponse } from '../types';

export const Predict: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PredictionResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (rawFormData: PredictionRequest) => {
        setLoading(true);
        setError(null);

        try {
            // Never mutate the caller's object – spread first
            const formData: PredictionRequest = { ...rawFormData };

            // If not breast cancer, default biomarkers to Unknown
            if (formData.cancer_site !== 'Breast') {
                formData.er_status = 'Unknown';
                formData.pr_status = 'Unknown';
                formData.her2_status = 'Unknown';
            }

            // Send raw payload directly to prediction service
            // The scikit-learn Pipeline inside the prediction service handles all transformations
            console.log('Sending data to prediction service...');
            const predictionResponse = await predictApi.post<PredictionResponse>('/api/predict', formData);

            setResult(predictionResponse.data);
        } catch (err: any) {
            console.error('Prediction error:', err);
            const errorData = err.response?.data?.detail;
            const errorMessage = errorData 
                ? (typeof errorData === 'object' ? JSON.stringify(errorData) : errorData)
                : (err.message || 'Prediction failed');
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="lg">
            <Box sx={{ py: 4 }}>
                <PredictionForm onSubmit={handleSubmit} loading={loading} />

                {error && (
                    <Alert severity="error" sx={{ mt: 3, maxWidth: 900, mx: 'auto' }}>
                        <strong>Error:</strong> {error}
                    </Alert>
                )}

                {result && <PredictionResult result={result} />}
            </Box>
        </Container>
    );
};

