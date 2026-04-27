import React from 'react';
import { Container } from '@mui/material';
import { RegisterForm } from '../components/auth/RegisterForm';

export const Register: React.FC = () => {
    return (
        <Container maxWidth="sm">
            <RegisterForm />
        </Container>
    );
};

