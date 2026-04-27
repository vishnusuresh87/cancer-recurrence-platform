import React from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Chip,
    Alert,
    LinearProgress,
} from '@mui/material';
import { PredictionResponse } from '../../types';
import { SurvivalCurveChart } from './SurvivalCurveChart';

interface Props {
    result: PredictionResponse;
}

export const PredictionResult: React.FC<Props> = ({ result }) => {
    const getRiskColor = (level: string) => {
        switch (level) {
            case 'Low':
                return 'success';
            case 'Moderate':
                return 'warning';
            case 'High':
                return 'error';
            case 'Very High':
                return 'error';
            default:
                return 'default';
        }
    };

    return (
        <Card elevation={3} sx={{ mt: 4, maxWidth: 800, mx: 'auto' }}>
            <CardContent>
                <Typography variant="h5" gutterBottom>
                    Recurrence Risk Estimate
                </Typography>

                {/* Probability Display */}
                <Box sx={{ textAlign: 'center', my: 4 }}>
                    <Typography variant="h1" color="primary" sx={{ fontSize: '4rem', fontWeight: 'bold' }}>
                        {result.probability_pct.toFixed(1)}%
                    </Typography>
                    <Chip
                        label={result.risk_level}
                        color={getRiskColor(result.risk_level)}
                        sx={{ mt: 2, fontSize: '1.2rem', px: 3, py: 2 }}
                    />
                </Box>

                {/* Progress Bar */}
                <Box sx={{ my: 3 }}>
                    <LinearProgress
                        variant="determinate"
                        value={result.probability_pct}
                        color={getRiskColor(result.risk_level) as any}
                        sx={{ height: 10, borderRadius: 5 }}
                    />
                </Box>

                {/* Interpretation */}
                <Alert severity="info" sx={{ my: 3 }}>
                    <Typography variant="body1">
                        {result.interpretation}
                    </Typography>
                </Alert>

                {/* Survival Curve */}
                <Box sx={{ my: 4 }}>
                    <Typography variant="h6" gutterBottom>
                        Risk Over Time
                    </Typography>
                    <SurvivalCurveChart data={result.survival_curve} />
                </Box>

                {/* Model Info */}
                <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #ddd' }}>
                    <Typography variant="caption" color="text.secondary">
                        Model Version: {result.model_version} |
                        Prediction ID: {result.prediction_id} |
                        Generated: {new Date(result.timestamp).toLocaleString()}
                    </Typography>
                </Box>
            </CardContent>
        </Card>
    );
};

