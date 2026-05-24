import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaEnvelope, FaLock, FaKey, FaArrowRight, FaCheckCircle } from 'react-icons/fa';
import { useAuthStore } from '../store/authStore';

const ForgotPassword = () => {
    const navigate = useNavigate();
    const { requestPasswordReset, confirmPasswordReset, isLoading, error } = useAuthStore();

    const [step, setStep] = useState(1); // 1: Email, 2: OTP & New Password
    const [email, setEmail] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmNewPassword, setConfirmNewPassword] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});

    const validateEmail = () => {
        if (!email) {
            setFieldErrors({ email: 'Email is required' });
            return false;
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setFieldErrors({ email: 'Invalid email format' });
            return false;
        }
        return true;
    };

    const validateResetForm = () => {
        const errors = {};
        if (!otp) errors.otp = 'OTP is required';
        if (!newPassword) errors.newPassword = 'New password is required';
        if (newPassword.length < 6) errors.newPassword = 'Password must be at least 6 characters';
        if (newPassword !== confirmNewPassword) errors.confirmNewPassword = 'Passwords do not match';

        setFieldErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleRequestOtp = async (e) => {
        e.preventDefault();
        setFieldErrors({});
        if (!validateEmail()) {
            return;
        }

        const result = await requestPasswordReset(email);

        if (result.success) {
            setStep(2);
            setSuccessMessage('OTP sent successfully to ' + email);
        }
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        setFieldErrors({});
        if (!validateResetForm()) return;

        const result = await confirmPasswordReset(email, otp, newPassword);
        if (result.success) {
            setSuccessMessage('Password reset successfully!');
            setTimeout(() => navigate('/signin'), 2000);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0e0e14] to-[#1a1a2e] px-4">
            <div className="w-full max-w-md bg-[var(--bg-1)] border border-[var(--border-color)] rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
                {/* Decorative background elements */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl -mr-16 -mt-16 pointer-events-none"></div>
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/10 rounded-full blur-2xl -ml-16 -mb-16 pointer-events-none"></div>

                <div className="text-center mb-8 relative z-10">
                    <div className="mx-auto w-16 h-16 bg-indigo-500/10 rounded-full flex items-center justify-center mb-4">
                        <FaLock className="w-8 h-8 text-indigo-500" />
                    </div>
                    <h2 className="text-2xl font-bold text-[var(--text-primary)]">Reset Password</h2>
                    <p className="text-[var(--text-muted)] text-sm mt-2">
                        {step === 1 ? "Enter your email to receive an OTP" : "Enter the OTP sent to your email"}
                    </p>
                </div>

                {(error || successMessage) && (
                    <div className={`mb-6 p-3 rounded-lg text-sm border ${successMessage
                        ? 'bg-green-500/20 border-green-500/50 text-green-400'
                        : 'bg-red-500/20 border-red-500/50 text-red-400'
                        }`}>
                        {successMessage || error}
                    </div>
                )}

                {step === 1 ? (
                    <form onSubmit={handleRequestOtp} className="space-y-5 relative z-10">
                        <div>
                            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2 uppercase tracking-wide">Email Address</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <FaEnvelope className="text-gray-500" />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className={`w-full pl-10 pr-4 py-3 bg-[var(--input-bg)] border ${fieldErrors.email ? 'border-red-500' : 'border-[var(--border-color)]'
                                        } rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-[var(--text-primary)] transition-all`}
                                    placeholder="name@example.com"
                                    disabled={isLoading}
                                />
                            </div>
                            {fieldErrors.email && <p className="text-red-500 text-xs mt-1">{fieldErrors.email}</p>}
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 rounded-xl transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 group disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {isLoading ? 'Sending...' : 'Send OTP'}
                            {!isLoading && <FaArrowRight className="group-hover:translate-x-1 transition-transform" />}
                        </button>
                    </form>
                ) : (
                    <form onSubmit={handleResetPassword} className="space-y-5 relative z-10">
                        <div>
                            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2 uppercase tracking-wide">OTP Code</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <FaKey className="text-gray-500" />
                                </div>
                                <input
                                    type="text"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    className={`w-full pl-10 pr-4 py-3 bg-[var(--input-bg)] border ${fieldErrors.otp ? 'border-red-500' : 'border-[var(--border-color)]'
                                        } rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-[var(--text-primary)] transition-all`}
                                    placeholder="Enter 6-digit OTP"
                                    disabled={isLoading}
                                />
                            </div>
                            {fieldErrors.otp && <p className="text-red-500 text-xs mt-1">{fieldErrors.otp}</p>}
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2 uppercase tracking-wide">New Password</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <FaLock className="text-gray-500" />
                                </div>
                                <input
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className={`w-full pl-10 pr-4 py-3 bg-[var(--input-bg)] border ${fieldErrors.newPassword ? 'border-red-500' : 'border-[var(--border-color)]'
                                        } rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-[var(--text-primary)] transition-all`}
                                    placeholder="New password"
                                    disabled={isLoading}
                                />
                            </div>
                            {fieldErrors.newPassword && <p className="text-red-500 text-xs mt-1">{fieldErrors.newPassword}</p>}
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2 uppercase tracking-wide">Confirm Password</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <FaCheckCircle className="text-gray-500" />
                                </div>
                                <input
                                    type="password"
                                    value={confirmNewPassword}
                                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                                    className={`w-full pl-10 pr-4 py-3 bg-[var(--input-bg)] border ${fieldErrors.confirmNewPassword ? 'border-red-500' : 'border-[var(--border-color)]'
                                        } rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 text-[var(--text-primary)] transition-all`}
                                    placeholder="Confirm new password"
                                    disabled={isLoading}
                                />
                            </div>
                            {fieldErrors.confirmNewPassword && <p className="text-red-500 text-xs mt-1">{fieldErrors.confirmNewPassword}</p>}
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 rounded-xl transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 group disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {isLoading ? 'Resetting...' : 'Reset Password'}
                        </button>
                    </form>
                )}

                <div className="mt-8 text-center relative z-10">
                    <Link to="/signin" className="text-sm text-[var(--text-muted)] hover:text-indigo-400 transition-colors">
                        Back to Sign In
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
