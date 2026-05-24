import React, { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import Dashboard from './student/Dashboard';
import { getModeratorStatus } from '../api/api';

const DashboardHome = () => {
    const { user } = useAuthStore();
    const navigate = useNavigate();
    const [isModeratorActive, setIsModeratorActive] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkModeratorStatus = async () => {
            // Only check if user has moderator designation
            if (user?.is_moderator) {
                try {
                    const status = await getModeratorStatus();
                    setIsModeratorActive(status.is_moderator_active);
                    
                    // If in student mode but on teacher route, redirect immediately
                    if (!status.is_moderator_active && window.location.pathname.startsWith('/teacher')) {
                        window.location.href = '/dashboard';
                        return;
                    }
                } catch (error) {
                    console.error('Failed to check moderator status:', error);
                    // Default to student view on error
                    setIsModeratorActive(false);
                }
            } else {
                setIsModeratorActive(false);
            }
            setLoading(false);
        };

        if (user) {
            checkModeratorStatus();
        } else {
            setLoading(false);
        }
    }, [user]);

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-400">Loading...</p>
                </div>
            </div>
        );
    }

    // Check actual active moderator state, not just permanent designation
    // Only show teacher dashboard if user has moderator designation AND is actively in moderator group
    if (user?.is_moderator && isModeratorActive) {
        return <Navigate to="/teacher/dashboard" replace />;
    }

    // Otherwise, show Student Dashboard
    return <Dashboard />;
};

export default DashboardHome;
