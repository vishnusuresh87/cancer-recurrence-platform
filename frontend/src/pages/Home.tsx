import React from 'react';
import {
    Container,
    Typography,
    Button,
    Box,
    Grid,
    Card,
    CardContent,
    CardActions,
} from '@mui/material';
import {
    Analytics,
    Security,
    Science,
    TrendingUp,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';

export const Home: React.FC = () => {
    const navigate = useNavigate();
    const isAuthenticated = authService.isAuthenticated();

    const features = [
        {
            icon: <Science fontSize="large" color="primary" />,
            title: 'AI-Powered Predictions',
            description: 'Uses Random Survival Forest trained on 200,000+ SEER cancer cases',
        },
        {
            icon: <Analytics fontSize="large" color="primary" />,
            title: 'Personalized Risk Assessment',
            description: '28 clinical features analyzed for accurate recurrence probability',
        },
        {
            icon: <TrendingUp fontSize="large" color="primary" />,
            title: 'Survival Curve Visualization',
            description: 'View your risk over time with interactive charts',
        },
        {
            icon: <Security fontSize="large" color="primary" />,
            title: 'Secure & Private',
            description: 'Your health data is encrypted and never shared',
        },
    ];

    return (
        <Container maxWidth="lg">
            {/* Hero Section */}
            <Box sx={{ my: 8, textAlign: 'center' }}>
                <Typography variant="h2" component="h1" gutterBottom>
                    Cancer Recurrence Risk Assessment
                </Typography>
                <Typography variant="h5" color="text.secondary" paragraph>
                    Evidence-based predictions to support your cancer care journey
                </Typography>
                <Box sx={{ mt: 4 }}>
                    {isAuthenticated ? (
                        <Button
                            variant="contained"
                            size="large"
                            onClick={() => navigate('/predict')}
                            sx={{ mr: 2 }}
                        >
                            Get Prediction
                        </Button>
                    ) : (
                        <>
                            <Button
                                variant="contained"
                                size="large"
                                onClick={() => navigate('/register')}
                                sx={{ mr: 2 }}
                            >
                                Get Started
                            </Button>
                            <Button
                                variant="outlined"
                                size="large"
                                onClick={() => navigate('/login')}
                            >
                                Sign In
                            </Button>
                        </>
                    )}
                </Box>
            </Box>

            {/* Features Grid */}
            <Grid container spacing={4} sx={{ my: 4 }}>
                {features.map((feature, index) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                            <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                                <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                                <Typography variant="h6" component="h2" gutterBottom>
                                    {feature.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {feature.description}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {/* Disclaimer */}
            <Box sx={{ my: 8, p: 3, bgcolor: 'warning.light', borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Important Medical Disclaimer
                </Typography>
                <Typography variant="body2">
                    This tool provides statistical estimates based on historical cancer registry data.
                    Results should NOT be used as a substitute for professional medical advice, diagnosis,
                    or treatment. Always consult with qualified healthcare providers about your specific
                    medical condition and treatment options.
                </Typography>
            </Box>
        </Container>
    );
};

