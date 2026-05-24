import React, { useState, useMemo } from 'react';
import useManageCourseStore from '../../store/manageCourseStore';
import { FaUserPlus, FaUserCheck, FaUserTimes, FaUsers } from 'react-icons/fa';

const CourseEnrollment = ({ courseId }) => {
    const {
        enrollments,
        loadingEnrollments,
        approveEnrollments,
        rejectEnrollments,
        removeEnrollments,
    } = useManageCourseStore();

    const [searchQuery, setSearchQuery] = useState('');

    // Single-user handlers for UI buttons
    const handleApprove = (userId, wasRejected = false) =>
        approveEnrollments(courseId, [userId], wasRejected);
    const handleReject = (userId, wasEnrolled = false) =>
        rejectEnrollments(courseId, [userId], wasEnrolled);
    const handleRemove = (userId) =>
        removeEnrollments(courseId, [userId]);

    // Filter helper — matches against name, username, and email
    const filterStudents = (list) => {
        if (!searchQuery.trim()) return list;
        const q = searchQuery.trim().toLowerCase();
        return list.filter((s) => {
            const fullName = `${s.first_name ?? ''} ${s.last_name ?? ''}`.toLowerCase();
            return (
                fullName.includes(q) ||
                (s.username && s.username.toLowerCase().includes(q)) ||
                (s.email && s.email.toLowerCase().includes(q))
            );
        });
    };

    const filteredPending = useMemo(() => filterStudents(enrollments.pending_requests), [enrollments.pending_requests, searchQuery]);
    const filteredEnrolled = useMemo(() => filterStudents(enrollments.enrolled), [enrollments.enrolled, searchQuery]);
    const filteredRejected = useMemo(() => filterStudents(enrollments.rejected), [enrollments.rejected, searchQuery]);

    const isSearching = searchQuery.trim().length > 0;

    const countLabel = (filtered, total) =>
        isSearching ? `${filtered} / ${total}` : `${total}`;

    return (
        <div className="px-1">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center ">
                    <FaUsers className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                    <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Course Enrollments</h3>
                    <p className="text-xs muted">Manage student access</p>
                </div>
                    </div>

                    {/* Search Input */}
                    <div className="mb-6">
                        <div className="relative">
                            <svg
                                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                />
                            </svg>
                            <input
                                id="enrollment-search"
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search by name, username, or email…"
                                className="w-full pl-10 pr-10 py-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200 transition"
                                    aria-label="Clear search"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    </div>

                    {loadingEnrollments ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        </div>
                    ) : (
                        <div className="space-y-8">
                            {/* Pending Requests */}
                            {enrollments.pending_requests.length > 0 && (
                                <div>
                                    <h3 className="text-base sm:text-lg font-bold mb-4 flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                                        Pending Requests ({countLabel(filteredPending.length, enrollments.pending_requests.length)})
                                    </h3>
                                    <div className="space-y-3">
                                        {filteredPending.map((student) => (
                                            <div
                                                key={student.user_id}
                                                className="card p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-2 hover:shadow-lg transition-all duration-300 group  bg-[var(--surface)] rounded-xl border-[var(--border-color)] hover:border-yellow-500/70 dark:hover:border-yellow-500/50"
                                            >
                                                <div>
                                                    <h4 className="font-semibold text-base sm:text-lg">{student.first_name} {student.last_name}</h4>
                                                    <p className="text-xs sm:text-sm muted">{student.username} • {student.email}</p>
                                                </div>
                                                <div className="flex gap-2 flex-wrap">
                                                    <button
                                                        onClick={() => handleApprove(student.id)}
                                                        className="px-4 py-2 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 text-white rounded-xl font-bold transition-all duration-300 shadow-lg shadow-green-500/20 text-xs sm:text-sm flex items-center gap-2"
                                                    >
                                                        <FaUserCheck /> Approve
                                                    </button>
                                                    <button
                                                        onClick={() => handleReject(student.id)}
                                                        className="px-4 py-2 border-2 border-red-500/50 hover:bg-red-500/10 text-red-500 rounded-xl font-bold transition-all duration-300 shadow-sm text-xs sm:text-sm flex items-center gap-2"
                                                    >
                                                        <FaUserTimes /> Reject
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Enrolled Students */}
                            <div>
                                <h3 className="text-base sm:text-lg font-bold mb-4 flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                    Enrolled Students ({countLabel(filteredEnrolled.length, enrollments.enrolled.length)})
                                </h3>
                                {filteredEnrolled.length > 0 ? (
                                    <div className="space-y-3">
                                        {filteredEnrolled.map((student) => (
                                            <div
                                                key={student.user_id}
                                                className="card p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-2 hover:shadow-lg transition-all duration-300 group  bg-[var(--surface)] rounded-xl border-[var(--border-color)] hover:border-green-500/70 dark:hover:border-green-500/50 "
                                            >
                                                <div className="flex-1">
                                                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3 mb-2">
                                                        <h4 className="font-semibold text-base sm:text-lg">{student.first_name} {student.last_name}</h4>
                                                        {student.grade && (
                                                            <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                                                Grade: {student.grade}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 text-xs sm:text-sm muted">
                                                        <span>{student.username} • {student.email}</span>
                                                        <span>Progress: {student.progress}%</span>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => handleRemove(student.id)}
                                                    className="px-4 py-2 border-2 border-red-500/50 hover:bg-red-500/10 text-red-500 rounded-xl font-bold transition-all duration-300 shadow-sm text-xs sm:text-sm flex items-center gap-2"
                                                >
                                                    <FaUserTimes /> Remove
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 border-2 border-dashed border-[var(--border-color)] rounded-xl bg-[var(--input-bg)] text-[var(--text-muted)] font-medium">
                                        {isSearching ? 'No enrolled students match your search' : 'No enrolled students yet'}
                                        </div>
                        )}
                                    </div>

                    {/* Rejected Students */}
                                {enrollments.rejected.length > 0 && (
                                    <div>
                                        <h3 className="text-base sm:text-lg font-bold mb-4 flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-red-500"></span>
                                            Rejected ({countLabel(filteredRejected.length, enrollments.rejected.length)})
                                        </h3>
                                        <div className="space-y-3">
                                            {filteredRejected.map((student) => (
                                                <div
                                                    key={student.user_id}
                                                    className="card p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0 border-2 hover:shadow-lg transition-all duration-300 group  bg-[var(--surface)] rounded-xl border-[var(--border-color)] hover:border-red-500/70 dark:hover:border-red-500/50 "
                                                >
                                                    <div>
                                                        <h4 className="font-semibold text-base sm:text-lg">{student.first_name} {student.last_name}</h4>
                                                        <p className="text-xs sm:text-sm muted">{student.username} • {student.email}</p>
                                                    </div>
                                                    <button
                                                        onClick={() => handleApprove(student.id, true)}
                                                        className="px-4 py-2 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 text-white rounded-xl font-bold transition-all duration-300 shadow-lg shadow-green-500/20 text-xs sm:text-sm flex items-center gap-2"
                                                    >
                                                        <FaUserCheck /> Approve
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* No Data */}
                                {enrollments.pending_requests.length === 0 &&
                                    enrollments.enrolled.length === 0 &&
                                    enrollments.rejected.length === 0 && (
                                        <div className="text-center py-16 border-2 border-dashed border-[var(--border-color)] rounded-xl bg-[var(--input-bg)] text-[var(--text-muted)] font-medium">
                                            <p>No enrollment requests or enrolled students</p>
                                        </div>
                                    )}
                            </div>
            )}
                        </div>
                    );
};

                    export default CourseEnrollment;