import React from 'react';
import { Container, Typography, Paper, Box, CircularProgress, Alert, Card, CardContent, Grid, Chip } from '@mui/material';
import { useQuery } from 'react-query';
import { predictApi } from '../services/api';
import { PredictionHistoryItem } from '../types';

const fetchHistory = async (): Promise<PredictionHistoryItem[]> => {
    const response = await predictApi.get('/api/predict/history');
    return response.data;
};

export const History: React.FC = () => {
    const { data: history, isLoading, error } = useQuery<PredictionHistoryItem[]>('predictionHistory', fetchHistory, {
        retry: 1
    });

    const getRiskColor = (risk: string) => {
        switch (risk.toLowerCase()) {
            case 'high': return 'error';
            case 'medium': return 'warning';
            case 'low': return 'success';
            default: return 'default';
        }
    };

    return (
        <Container maxWidth="md">
            <Box sx={{ py: 4 }}>
                <>
                    <Typography variant="h4" gutterBottom>
                        Prediction History
                    </Typography>
                    
                    {isLoading && (
                        <Box display="flex" justifyContent="center" my={4}>
                            <CircularProgress />
                        </Box>
                    )}

                    {error && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                            Failed to fetch prediction history. Please try again.
                        </Alert>
                    )}

                    {!isLoading && !error && history?.length === 0 && (
                        <Paper sx={{ p: 4, mt: 4, textAlign: 'center' }}>
                            <Typography variant="body1" color="text.secondary">
                                You have no previous predictions.
                            </Typography>
                        </Paper>
                    )}

                    {!isLoading && !error && history && history.length > 0 && (
                        <Grid container spacing={3} sx={{ mt: 2 }}>
                            {history.map((record) => (
                                <Grid item xs={12} key={record.prediction_id}>
                                    <Card elevation={3}>
                                        <CardContent>
                                            <Box display="flex" justifyContent="space-between" alignItems="center">
                                                <Typography variant="h6" color="primary">
                                                    {new Date(record.created_at).toLocaleDateString()} {new Date(record.created_at).toLocaleTimeString()}
                                                </Typography>
                                                <Chip 
                                                    label={record.risk_level.toUpperCase()} 
                                                    color={getRiskColor(record.risk_level) as any} 
                                                    variant="filled" 
                                                />
                                            </Box>
                                            <Box sx={{ mt: 2 }}>
                                                <Typography variant="body1">
                                                    <strong>Recurrence Probability:</strong> {record.probability_pct.toFixed(2)}%
                                                </Typography>
                                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                                    Model Version: {record.model_version}
                                                </Typography>
                                            </Box>
                                        </CardContent>
                                    </Card>
                                </Grid>
                            ))}
                        </Grid>
                    )}
                </>
            </Box>
        </Container>
    );
};
