import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/layout/Header';
import StudentSidebar from '../components/layout/Sidebar';
import TeacherSidebar from '../components/layout/TeacherSidebar';
import ChangePassword from '../components/auth/ChangePassword';
import { useAuthStore } from '../store/authStore';
import { FaUserCircle, FaEnvelope, FaIdBadge } from 'react-icons/fa';

const Settings = () => {
    const { user, isAuthenticated } = useAuthStore();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Determine if user is moderator/teacher
    const isTeacher = user?.is_moderator || false;

    if (!isAuthenticated || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
                <div className="text-center">
                    <div className="text-2xl text-gray-300 mb-4">Please log in to view settings</div>
                    <Link to="/signin" className="text-indigo-400 hover:text-indigo-300">
                        Go to Login
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen relative grid-texture">
            {/* Sidebar - Conditional based on role */}
            {isTeacher ? (
                <TeacherSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
            ) : (
                <StudentSidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
            )}

            {/* Main Content */}
            <main className="flex-1 ">
                <Header isAuth
                />

                <div className="p-4 sm:p-6 lg:p-8">
                    <div className="max-w-4xl mx-auto space-y-8">

                        {/* Page Header */}
                        <div>
                            <h1 className="text-2xl sm:text-3xl font-bold text-[var(--text-primary)]">Account Settings</h1>
                            <p className="text-[var(--text-secondary)] mt-2">Manage your account profile and security preferences.</p>
                        </div>

                        {/* Profile Section */}
                        <div className="bg-[var(--bg-secondary)] rounded-2xl p-6 border border-[var(--border-subtle)] shadow-sm">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
                                    <FaUserCircle className="w-5 h-5" />
                                </div>
                                <h2 className="text-xl font-semibold text-[var(--text-primary)]">Profile Information</h2>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Full Name</label>
                                    <div className="flex items-center gap-3 px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl text-[var(--text-primary)]">
                                        <FaIdBadge className="text-[var(--text-tertiary)]" />
                                        <span>{user?.first_name} {user?.last_name}</span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Email Address</label>
                                    <div className="flex items-center gap-3 px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl text-[var(--text-primary)] opacity-75 cursor-not-allowed">
                                        <FaEnvelope className="text-[var(--text-tertiary)]" />
                                        <span>{user?.email}</span>
                                    </div>
                                    <p className="text-xs text-[var(--text-secondary)] mt-1 ml-1">Email cannot be changed directly.</p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">User Role</label>
                                    <div className="flex items-center gap-3 px-4 py-3 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl text-[var(--text-primary)] opacity-75 cursor-not-allowed">
                                        <div className={`w-2 h-2 rounded-full ${user?.is_moderator ? 'bg-indigo-500' : 'bg-emerald-500'}`}></div>
                                        <span>{user?.is_moderator ? 'Teacher / Moderator' : 'Student'}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Security Section */}
                        <ChangePassword />

                    </div>
                </div>
            </main>
        </div>
    );
};

export default Settings;
