import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaHome, FaBook, FaChartBar, FaChevronRight, FaQuestionCircle, FaTimes } from 'react-icons/fa';
import { FaPersonCircleQuestion } from "react-icons/fa6";
import Logo from '../ui/Logo';

const TeacherSidebar = () => {
    const location = useLocation();
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    const navItems = [
        { path: '/teacher/dashboard', label: 'Dashboard', icon: FaHome },
        { path: '/teacher/quizzes', label: 'Quizzes', icon: FaQuestionCircle },
        { path: '/teacher/courses', label: 'Courses', icon: FaBook },
        { path: '/teacher/questions', label: 'Questions', icon: FaPersonCircleQuestion },
    ];

    // Helper to determine if a nav item is active
    const isActive = (path) => {
        if (path === '/teacher/dashboard') {
            return location.pathname === path;
        }
        if (path === '/teacher/courses') {
            return (
                location.pathname === path ||
                location.pathname.startsWith('/teacher/course/') ||
                location.pathname.startsWith('/teacher/courses') ||
                location.pathname === '/teacher/add-course' ||
                location.pathname === '/teacher/grading-systems'
            );
        }
        if (path === '/teacher/questions') {
            return (
                location.pathname === path ||
                location.pathname.startsWith('/teacher/question/') ||
                location.pathname === '/teacher/add-question' ||
                location.pathname === '/teacher/upload-question' ||
                location.pathname.startsWith('/teacher/test-question/')
            );
        }
        return location.pathname === path || location.pathname.startsWith(path + '/');
    };



    const handleLinkClick = () => {
        setIsMobileOpen(false);
    };

    return (
        <>
            {/* Mobile Overlay */}
            {isMobileOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => setIsMobileOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
                    fixed lg:sticky top-0 left-0 h-screen z-50
                    w-64 app-sidebar flex flex-col border-r border-white/5
                    transition-transform duration-300 ease-in-out
                    ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                `}
            >
                {/* Logo Section */}
                <div className="h-16 lg:h-20 px-4 sm:px-6 lg:px-8 border-b-1 border-[var(--border-strong)] bg-[var(--header-bg)] backdrop-blur-xl shadow-[var(--shadow-strong)] flex items-center justify-between flex-shrink-0">
                    <Logo />
                    <button
                        onClick={() => setIsMobileOpen(false)}
                        className="lg:hidden text-muted hover:text-white transition"
                    >
                        <FaTimes className="w-5 h-5" />
                    </button>

                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 sm:p-6 lg:p-8 space-y-2 overflow-y-auto">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const active = isActive(item.path);
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                onClick={handleLinkClick}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition ${active
                                    ? 'bg-blue-600 text-white'
                                    : 'text-soft hover:bg-white/3'
                                    }`}
                            >
                                <Icon className="w-5 h-5" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
            </aside>

            {/* Mobile Menu Toggle Button */}
            <button
                onClick={() => setIsMobileOpen(true)}
                className="lg:hidden fixed bottom-6 right-6 z-30 w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center shadow-2xl hover:scale-110 active:scale-95 transition-all duration-200"
                aria-label="Open menu"
            >
                <svg
                    className="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
            </button>
        </>
    );
};

export default TeacherSidebar;