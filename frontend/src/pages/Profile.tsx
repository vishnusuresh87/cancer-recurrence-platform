import React from 'react';
import { Container, Paper, Typography, Box, Grid, Avatar, Divider } from '@mui/material';
import { AccountCircle, Mail, Shield, CalendarToday } from '@mui/icons-material';

export const Profile: React.FC = () => {
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;

    if (!user) {
        return (
            <Container maxWidth="sm" sx={{ mt: 8, textAlign: 'center' }}>
                <Typography variant="h6">No user profile found. Please sign in.</Typography>
            </Container>
        );
    }

    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch {
            return dateStr;
        }
    };

    return (
        <Container maxWidth="sm">
            <Paper elevation={3} sx={{ p: 4, mt: 8, borderRadius: 2 }}>
                <Box display="flex" flexDirection="column" alignItems="center" sx={{ mb: 4 }}>
                    <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main', mb: 2 }}>
                        <AccountCircle sx={{ fontSize: 60 }} />
                    </Avatar>
                    <Typography variant="h4" gutterBottom>
                        My Profile
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Patient Account Information
                    </Typography>
                </Box>
                <Divider sx={{ mb: 3 }} />
                <Grid container spacing={3}>
                    <Grid item xs={12} display="flex" alignItems="center">
                        <Mail color="action" sx={{ mr: 2 }} />
                        <Box>
                            <Typography variant="caption" color="text.secondary">
                                Email Address
                            </Typography>
                            <Typography variant="body1">{user.email}</Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} display="flex" alignItems="center">
                        <Shield color="action" sx={{ mr: 2 }} />
                        <Box>
                            <Typography variant="caption" color="text.secondary">
                                Role / Permissions
                            </Typography>
                            <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
                                {user.role}
                            </Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} display="flex" alignItems="center">
                        <CalendarToday color="action" sx={{ mr: 2 }} />
                        <Box>
                            <Typography variant="caption" color="text.secondary">
                                Registered On
                            </Typography>
                            <Typography variant="body1">{formatDate(user.created_at)}</Typography>
                        </Box>
                    </Grid>
                    <Grid item xs={12} display="flex" alignItems="center">
                        <AccountCircle color="action" sx={{ mr: 2 }} />
                        <Box>
                            <Typography variant="caption" color="text.secondary">
                                User ID
                            </Typography>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                                {user.user_id}
                            </Typography>
                        </Box>
                    </Grid>
                </Grid>
            </Paper>
        </Container>
    );
};
