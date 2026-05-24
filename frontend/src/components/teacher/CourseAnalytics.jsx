import React from 'react';
import { FaUsers, FaCheckCircle, FaChartLine, FaTrophy, FaQuestionCircle, FaLayerGroup, FaListOl } from 'react-icons/fa';

const CourseAnalytics = ({ analytics, loading }) => {
    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (!analytics) {
        return (
            <div className="text-center py-12 text-muted">
                <p>No analytics data available</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center ">
                    <FaChartLine className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                    <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Course Analytics</h3>
                    <p className="text-xs muted">Monitor course performance</p>
                </div>
            </div>
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card p-4 rounded-2xl border-2 border-[var(--border-subtle)] hover:shadow-lg transition-all duration-300 group relative overflow-hidden">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs muted mb-1">Total Students</p>
                            <p className="text-2xl font-bold">{analytics.total_students || 0}</p>
                        </div>
                        <div className="w-10 h-10 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
                            <FaUsers className="w-5 h-5 text-blue-400" />
                        </div>
                    </div>
                </div>

                <div className="card p-4 rounded-2xl border-2 border-[var(--border-subtle)] hover:shadow-lg transition-all duration-300 group relative overflow-hidden">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs muted mb-1">Completion Rate</p>
                            <p className="text-2xl font-bold">{analytics.completion_rate || 0}%</p>
                        </div>
                        <div className="w-10 h-10 rounded-lg bg-green-500/20 border border-green-500/30 flex items-center justify-center">
                            <FaCheckCircle className="w-5 h-5 text-green-400" />
                        </div>
                    </div>
                </div>

                <div className="card p-4 rounded-2xl border-2 border-[var(--border-subtle)] hover:shadow-lg transition-all duration-300 group relative overflow-hidden">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs muted mb-1">Average Score</p>
                            <p className="text-2xl font-bold">{analytics.average_score || 0}%</p>
                        </div>
                        <div className="w-10 h-10 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
                            <FaChartLine className="w-5 h-5 text-purple-400" />
                        </div>
                    </div>
                </div>

                <div className="card p-4 rounded-2xl border-2 border-[var(--border-subtle)] hover:shadow-lg transition-all duration-300 group relative overflow-hidden">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs muted mb-1">Active Students</p>
                            <p className="text-2xl font-bold">{analytics.enrolled_students || 0}</p>
                        </div>
                        <div className="w-10 h-10 rounded-lg bg-orange-500/20 border border-orange-500/30 flex items-center justify-center">
                            <FaUsers className="w-5 h-5 text-orange-400" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Module Statistics */}
            {analytics.module_stats && analytics.module_stats.length > 0 && (
                <div className="card-strong p-6 border-2 border-[var(--border-strong)] shadow-lg rounded-2xl bg-[var(--surface)]">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <FaLayerGroup className="w-5 h-5" />
                        Module Completion Statistics
                    </h3>
                    <div className="space-y-3">
                        {analytics.module_stats.map((module) => (
                            <div key={module.module_id} className="card p-4 bg-[var(--surface-2)] border-2 hover:shadow-lg transition-all duration-300 group rounded-xl border-[var(--border-color)]">
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="font-semibold">{module.module_name}</h4>
                                    <span className="text-sm font-bold text-green-400">
                                        {module.completion_rate}%
                                    </span>
                                </div>
                                <div className="w-full bg-[var(--input-bg)] border border-[var(--border-subtle)] rounded-full h-2 mb-2">
                                    <div
                                        className="bg-gradient-to-r from-green-500 to-green-400 h-2 rounded-full transition-all"
                                        style={{ width: `${module.completion_rate}%` }}
                                    ></div>
                                </div>
                                <div className="flex items-center justify-between text-xs muted">
                                    <span>{module.students_completed} students completed</span>
                                    <span>{module.total_units} units</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Quiz Statistics */}
            {analytics.quiz_stats && analytics.quiz_stats.length > 0 && (
                <div className="card-strong p-6 border-2 border-[var(--border-strong)] shadow-lg rounded-2xl bg-[var(--surface)]">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <FaQuestionCircle className="w-5 h-5" />
                        Quiz Performance
                    </h3>
                    <div className="overflow-x-auto rounded-2xl border-2 border-[var(--border-strong)]">
                        <table className="min-w-full text-sm">
                            <thead>
                                <tr className="bg-blue-500/10 border-b-2 border-[var(--border-strong)]">
                                    <th className="px-4 py-3 text-left font-bold text-blue-400">Quiz Name</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Attempts</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Avg Score</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Pass Rate</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Questions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analytics.quiz_stats.map((quiz) => (
                                    <tr key={quiz.quiz_id} className="border-b border-[var(--border-subtle)] transition-colors">
                                        <td className="px-4 py-3 font-medium">{quiz.quiz_name}</td>
                                        <td className="px-4 py-3 text-center font-semibold">{quiz.total_attempts}</td>
                                        <td className="px-4 py-3 text-center font-semibold text-blue-500">{quiz.average_score}%</td>
                                        <td className="px-4 py-3 text-center">
                                            <span className={`px-2 py-1 rounded text-xs ${quiz.pass_rate >= 70
                                                ? 'text-green-400 font-bold'
                                                : quiz.pass_rate >= 50
                                                    ? 'text-yellow-400 font-bold'
                                                    : 'text-red-400 font-bold'
                                                }`}>
                                                {quiz.pass_rate}%
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-center font-semibold">{quiz.total_questions}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Top Students */}
            {analytics.top_students && analytics.top_students.length > 0 && (
                <div className="card-strong p-6 border-2 border-[var(--border-strong)] shadow-lg rounded-2xl bg-[var(--surface)]">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <FaTrophy className="w-5 h-5 text-yellow-400" />
                        Top Students
                    </h3>
                    <div className="space-y-3">
                        {analytics.top_students.map((student, index) => (
                            <div key={student.user_id} className="card p-4 flex items-center justify-between border-2 border-[var(--border-strong)] bg-[var(--surface-2)] hover:border-yellow-500/50 transition-all shadow-sm">
                                <div className="flex items-center gap-4">
                                    <div className="w-8 h-8 rounded-lg bg-yellow-500/10 border-2 border-yellow-500/20 flex items-center justify-center text-yellow-500 font-extrabold shadow-inner shadow-yellow-500/10">
                                        {index + 1}
                                    </div>
                                    <div>
                                        <h4 className="font-semibold">
                                            {student.first_name} {student.last_name}
                                        </h4>
                                        <p className="text-xs muted">{student.username}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right">
                                        <p className="text-sm font-bold">{student.score}%</p>
                                        <p className="text-xs muted">Score</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-sm font-bold">{student.completion}%</p>
                                        <p className="text-xs muted">Complete</p>
                                    </div>
                                    {student.grade && student.grade !== 'N/A' && (
                                        <div className="px-3 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-sm font-bold">
                                            {student.grade}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Question Statistics */}
            {analytics.question_statistics && analytics.question_statistics.length > 0 && (
                <div className="card-strong p-6 border-2 border-[var(--border-strong)] shadow-lg rounded-2xl bg-[var(--surface)]">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <FaListOl className="w-5 h-5" />
                        Question Statistics</h3>
                    <div className="overflow-x-auto rounded-2xl border-2 border-[var(--border-strong)]">
                        <table className="min-w-full text-sm">
                            <thead>
                                <tr className="bg-blue-500/10 border-b-2 border-[var(--border-strong)]">
                                    <th className="px-4 py-3 text-left font-bold text-blue-400">Question</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Quiz</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Attempts</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Correct</th>
                                    <th className="px-4 py-3 text-center font-bold text-blue-400">Avg Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analytics.question_statistics.slice(0, 10).map((q, index) => (
                                    <tr key={index} className="border-b border-[var(--border-subtle)] transition-colors">
                                        <td className="px-4 py-3 font-medium">{q.summary}</td>
                                        <td className="px-4 py-3 text-center font-medium">{q.quiz_name}</td>
                                        <td className="px-4 py-3 text-center font-semibold">{q.attempts}</td>
                                        <td className="px-4 py-3 text-center font-semibold text-green-500">{q.correct_attempts}</td>
                                        <td className="px-4 py-3 text-center font-bold text-blue-500">{q.average_score}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CourseAnalytics;

