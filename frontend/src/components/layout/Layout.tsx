import React from 'react';
import { Box, Container } from '@mui/material';
import { Header } from './Header';

interface Props {
    children: React.ReactNode;
}

export const Layout: React.FC<Props> = ({ children }) => {
    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Header />
            <Box component="main" sx={{ flexGrow: 1, py: 3 }}>
                {children}
            </Box>
            <Box
                component="footer"
                sx={{
                    py: 3,
                    px: 2,
                    mt: 'auto',
                    backgroundColor: (theme) =>
                        theme.palette.mode === 'light'
                            ? theme.palette.grey[200]
                            : theme.palette.grey[800],
                }}
            >
                <Container maxWidth="sm">
                    <Box sx={{ textAlign: 'center' }}>
                        <small>
                            © 2026 Cancer Recurrence Predictor. For research and educational purposes only.
                            Not a substitute for professional medical advice.
                        </small>
                    </Box>
                </Container>
            </Box>
        </Box>
    );
};


