import React from 'react';
import { Container } from '@mui/material';
import { LoginForm } from '../components/auth/LoginForm';

export const Login: React.FC = () => {
    return (
        <Container maxWidth="sm">
            <LoginForm />
        </Container>
    );
};

