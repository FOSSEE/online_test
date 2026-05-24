import React, { useState } from 'react';
import { requestPasswordChange, confirmPasswordChange } from '../../api/api';
import { FaLock, FaKey, FaArrowRight } from 'react-icons/fa';

const ChangePassword = () => {
    const [step, setStep] = useState('initial'); // 'initial', 'form', 'success'
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        otp: '',
        newPassword: '',
        confirmNewPassword: ''
    });

    const handleRequestChange = async () => {
        setIsLoading(true);
        setError('');
        try {
            await requestPasswordChange();
            setStep('form');
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to request password change. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirmChange = async (e) => {
        e.preventDefault();
        if (formData.newPassword !== formData.confirmNewPassword) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);
        setError('');
        try {
            await confirmPasswordChange(formData.otp, formData.newPassword);
            setStep('success');
            setFormData({ otp: '', newPassword: '', confirmNewPassword: '' });
        } catch (err) {
            setError(err.response?.data?.message || 'Failed to change password. Please check your OTP.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    return (
        <div className="bg-[var(--bg-secondary)] rounded-2xl p-6 border border-[var(--border-subtle)] shadow-sm">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-500/10 rounded-lg text-purple-500">
                    <FaLock className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">Password Security</h2>
            </div>

            {error && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                    {error}
                </div>
            )}

            {step === 'initial' && (
                <div>
                    <p className="text-[var(--text-secondary)] mb-6">
                        To change your password, we'll send a One-Time Password (OTP) to your registered email address for verification.
                    </p>
                    <button
                        onClick={handleRequestChange}
                        disabled={isLoading}
                        className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-xl font-medium transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? 'Sending...' : 'Change Password'}
                        {!isLoading && <FaArrowRight className="w-3 h-3" />}
                    </button>
                </div>
            )}

            {step === 'form' && (
                <form onSubmit={handleConfirmChange} className="space-y-4 max-w-md">
                    <p className="text-sm text-[var(--text-secondary)] mb-4">
                        An OTP has been sent to your email. Please enter it below along with your new password.
                    </p>

                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                            One-Time Password (OTP)
                        </label>
                        <div className="relative">
                            <FaKey className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
                            <input
                                type="text"
                                name="otp"
                                value={formData.otp}
                                onChange={handleChange}
                                required
                                className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 text-[var(--text-primary)] transition-all"
                                placeholder="Enter OTP"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                            New Password
                        </label>
                        <div className="relative">
                            <FaLock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
                            <input
                                type="password"
                                name="newPassword"
                                value={formData.newPassword}
                                onChange={handleChange}
                                required
                                minLength={8}
                                className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 text-[var(--text-primary)] transition-all"
                                placeholder="Min. 8 characters"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
                            Confirm New Password
                        </label>
                        <div className="relative">
                            <FaLock className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
                            <input
                                type="password"
                                name="confirmNewPassword"
                                value={formData.confirmNewPassword}
                                onChange={handleChange}
                                required
                                className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 text-[var(--text-primary)] transition-all"
                                placeholder="Re-enter new password"
                            />
                        </div>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={() => setStep('initial')}
                            className="px-5 py-2.5 bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-xl font-medium transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="flex-1 px-5 py-2.5 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white rounded-xl font-medium transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/25"
                        >
                            {isLoading ? 'Updating...' : 'Update Password'}
                        </button>
                    </div>
                </form>
            )}

            {step === 'success' && (
                <div className="text-center py-6">
                    <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <FaLock className="w-8 h-8" />
                    </div>
                    <h3 className="text-xl font-bold text-[var(--text-primary)] mb-2">Password Updated!</h3>
                    <p className="text-[var(--text-secondary)] mb-6">
                        Your password has been successfully changed.
                    </p>
                    <button
                        onClick={() => setStep('initial')}
                        className="px-6 py-2.5 bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-xl font-medium hover:bg-[var(--bg-tertiary)] transition-colors"
                    >
                        Done
                    </button>
                </div>
            )}
        </div>
    );
};

export default ChangePassword;
