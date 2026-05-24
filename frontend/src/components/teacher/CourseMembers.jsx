import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FaUser, FaTrash, FaCheck, FaUsers } from 'react-icons/fa';
import { getCourseTeachers, removeTeachersFromCourse } from '../../api/api';

const CourseMembers = () => {
    const { courseId } = useParams();
    const [currentTeachers, setCurrentTeachers] = useState([]);
    const [selectedTeachers, setSelectedTeachers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [removing, setRemoving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    // Load current teachers on mount
    useEffect(() => {
        if (courseId) {
            loadCurrentTeachers();
        }
    }, [courseId]);

    const loadCurrentTeachers = async () => {
        setLoading(true);
        try {
            const response = await getCourseTeachers(courseId);
            setCurrentTeachers(response.teachers || []);
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to load teachers' });
            console.error('Error loading teachers:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleSelect = (teacherId) => {
        setSelectedTeachers(prev => 
            prev.includes(teacherId)
                ? prev.filter(id => id !== teacherId)
                : [...prev, teacherId]
        );
    };

    const handleSelectAll = () => {
        if (selectedTeachers.length === currentTeachers.length) {
            setSelectedTeachers([]);
        } else {
            setSelectedTeachers(currentTeachers.map(t => t.id));
        }
    };

    const handleRemoveTeachers = async () => {
        if (selectedTeachers.length === 0) {
            setMessage({ type: 'warning', text: 'Please select at least one teacher to remove' });
            return;
        }

        if (!window.confirm(`Are you sure you want to remove ${selectedTeachers.length} teacher(s)?`)) {
            return;
        }

        setRemoving(true);
        setMessage({ type: '', text: '' });
        try {
            const response = await removeTeachersFromCourse(courseId, selectedTeachers);
            if (response.success) {
                setMessage({ type: 'success', text: response.message || 'Teachers removed successfully' });
                setSelectedTeachers([]);
                // Reload current teachers
                await loadCurrentTeachers();
            }
        } catch (error) {
            setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to remove teachers' });
        } finally {
            setRemoving(false);
        }
    };

    return (
        <div>
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center ">
                    <FaUsers className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                    <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Course Members</h3>
                    <p className="text-xs muted">Manage your teaching staff</p>
                </div>
            </div>

            {/* Message Display */}
            {message.text && (
                <div className={`mb-4 p-3 rounded-lg ${
                    message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-300' :
                    message.type === 'error' ? 'bg-red-500/10 border border-red-500/30 text-red-300' :
                    message.type === 'warning' ? 'bg-yellow-500/10 border border-yellow-500/30 text-yellow-300' :
                    'bg-blue-500/10 border border-blue-500/30 text-blue-300'
                }`}>
                    {message.text}
                </div>
            )}

            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
            ) : currentTeachers.length > 0 ? (
                <form onSubmit={(e) => { e.preventDefault(); handleRemoveTeachers(); }}>
                    <div className="card overflow-x-auto mb-4">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[var(--border-color)]">
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold">
                                        <input
                                            type="checkbox"
                                            checked={selectedTeachers.length === currentTeachers.length && currentTeachers.length > 0}
                                            onChange={handleSelectAll}
                                            className="w-4 h-4 rounded border-[var(--border-color)] bg-[var(--input-bg)]"
                                        />
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold">Name</th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold">Email</th>
                                </tr>
                            </thead>
                            <tbody>
                                {currentTeachers.map((teacher) => (
                                    <tr
                                        key={teacher.id}
                                        className="border-b border-[var(--border-color)] hover:bg-white/5 transition"
                                    >
                                        <td className="px-4 py-3">
                                            <input
                                                type="checkbox"
                                                checked={selectedTeachers.includes(teacher.id)}
                                                onChange={() => handleToggleSelect(teacher.id)}
                                                className="w-4 h-4 rounded border-[var(--border-color)] bg-[var(--input-bg)]"
                                            />
                                        </td>
                                        <td className="px-4 py-3 text-sm font-medium">
                                            {teacher.first_name} {teacher.last_name}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-muted">{teacher.email}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <button
                        type="submit"
                        disabled={removing || selectedTeachers.length === 0}
                        className="px-6 py-2.5 bg-gradient-to-r from-red-600 to-red-500 text-white rounded-xl hover:from-red-700 hover:to-red-600 shadow-lg shadow-red-500/20 transition-all duration-300 font-bold text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <FaTrash className="w-4 h-4" />
                        {removing ? 'Removing...' : 'Remove Teachers'}
                    </button>
                </form>
            ) : (
                <div className="card p-8 text-center">
                    <p className="text-muted">No Teacher(s) added</p>
                </div>
            )}
        </div>
    );
};

export default CourseMembers;




