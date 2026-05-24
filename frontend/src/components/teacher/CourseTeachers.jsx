import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FaSearch, FaPlus, FaTrash, FaUser, FaCheck } from 'react-icons/fa';
import { searchTeachers, getCourseTeachers, addTeachersToCourse, removeTeachersFromCourse } from '../../api/api';

const CourseTeachers = () => {
    const { courseId } = useParams();
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [currentTeachers, setCurrentTeachers] = useState([]);
    const [selectedTeachers, setSelectedTeachers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingTeachers, setLoadingTeachers] = useState(false);
    const [adding, setAdding] = useState(false);
    const [removing, setRemoving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    // Load current teachers on mount
    useEffect(() => {
        if (courseId) {
            loadCurrentTeachers();
        }
    }, [courseId]);

    const loadCurrentTeachers = async () => {
        setLoadingTeachers(true);
        try {
            const response = await getCourseTeachers(courseId);
            setCurrentTeachers(response.teachers || []);
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to load teachers' });
            console.error('Error loading teachers:', error);
        } finally {
            setLoadingTeachers(false);
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) {
            setMessage({ type: 'warning', text: 'Please enter a search query' });
            return;
        }

        setLoading(true);
        setMessage({ type: '', text: '' });
        try {
            const response = await searchTeachers(courseId, searchQuery);
            if (response.success) {
                setSearchResults(response.teachers || []);
                setSelectedTeachers([]);
                if (response.count === 0) {
                    setMessage({ type: 'info', text: 'No results found' });
                }
            }
        } catch (error) {
            setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to search teachers' });
            setSearchResults([]);
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
        if (selectedTeachers.length === searchResults.length) {
            setSelectedTeachers([]);
        } else {
            setSelectedTeachers(searchResults.map(t => t.id));
        }
    };

    const handleAddTeachers = async () => {
        if (selectedTeachers.length === 0) {
            setMessage({ type: 'warning', text: 'Please select at least one teacher to add' });
            return;
        }

        setAdding(true);
        setMessage({ type: '', text: '' });
        try {
            const response = await addTeachersToCourse(courseId, selectedTeachers);
            if (response.success) {
                setMessage({ type: 'success', text: response.message || 'Teachers added successfully' });
                setSearchResults([]);
                setSearchQuery('');
                setSelectedTeachers([]);
                // Reload current teachers
                await loadCurrentTeachers();
            }
        } catch (error) {
            setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to add teachers' });
        } finally {
            setAdding(false);
        }
    };

    const handleRemoveTeachers = async (teacherIds) => {
        if (teacherIds.length === 0) return;

        if (!window.confirm(`Are you sure you want to remove ${teacherIds.length} teacher(s)?`)) {
            return;
        }

        setRemoving(true);
        setMessage({ type: '', text: '' });
        try {
            const response = await removeTeachersFromCourse(courseId, teacherIds);
            if (response.success) {
                setMessage({ type: 'success', text: response.message || 'Teachers removed successfully' });
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
                    <FaUser className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                    <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Add Teachers / TAs</h3>
                    <p className="text-xs muted">Search and add co-teachers</p>
                </div>
            </div>

            {/* Message Display */}
            {message.text && (
                <div className={`mb-4 p-3 rounded-lg ${message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-300' :
                    message.type === 'error' ? 'bg-red-500/10 border border-red-500/30 text-red-300' :
                        message.type === 'warning' ? 'bg-yellow-500/10 border border-yellow-500/30 text-yellow-300' :
                            'bg-blue-500/10 border border-blue-500/30 text-blue-300'
                    }`}>
                    {message.text}
                </div>
            )}

            {/* Search Section */}
            <div className="mb-8">
                <form onSubmit={handleSearch} className="flex flex-row sm:flex-row gap-3">
                    <div className="flex-1 relative">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search teachers with username, firstname, lastname, email"
                            className="w-full px-4 py-2.5 bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="px-3 sm:px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-700 hover:to-blue-600 transition-all duration-300 font-bold shadow-lg shadow-blue-500/20 text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <FaSearch className="w-4 h-4" />
                        <div className='hidden sm:inline'>
                            {loading ? 'Searching...' : 'Search'}
                        </div>
                    </button>
                </form>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base sm:text-lg font-bold">
                            Search Results ({searchResults.length})
                        </h3>
                        <button
                            onClick={handleSelectAll}
                            className="text-xs sm:text-sm text-blue-400 hover:text-blue-300 transition"
                        >
                            {selectedTeachers.length === searchResults.length ? 'Deselect All' : 'Select All'}
                        </button>
                    </div>
                    <div className="bg-blue-500/20  border-2 border-blue-500/40 dark:border-blue-500/30 rounded-lg p-3 mb-4 text-sm text-blue-700 dark:text-blue-400 font-semibold">
                        Search results do not include teachers already added
                    </div>
                    <div className="overflow-x-auto rounded-2xl border-2 border-[var(--border-strong)]">
                        <table className="min-w-full text-sm">
                            <thead>
                                <tr className="bg-blue-500/10 border-b-2 border-[var(--border-strong)]">
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold">
                                        <input
                                            type="checkbox"
                                            checked={selectedTeachers.length === searchResults.length && searchResults.length > 0}
                                            onChange={handleSelectAll}
                                            className="w-4 h-4 rounded border-[var(--border-color)] bg-[var(--input-bg)]"
                                        />
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold text-blue-400">Username</th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold text-blue-400">Name</th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold text-blue-400">Email</th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold text-blue-400">Institute</th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold text-blue-400">Department</th>
                                    <th className="px-4 py-3 text-left text-xs sm:text-sm font-semibold text-blue-400">Position</th>
                                </tr>
                            </thead>
                            <tbody>
                                {searchResults.map((teacher) => (
                                    <tr
                                        key={teacher.id}
                                        className="border-b border-[var(--border-subtle)] hover:bg-[var(--input-bg)] transition-colors"
                                    >
                                        <td className="px-4 py-3">
                                            <input
                                                type="checkbox"
                                                checked={selectedTeachers.includes(teacher.id)}
                                                onChange={() => handleToggleSelect(teacher.id)}
                                                className="w-4 h-4 rounded border-[var(--border-color)] bg-[var(--input-bg)]"
                                            />
                                        </td>
                                        <td className="px-4 py-3 text-sm">{teacher.username}</td>
                                        <td className="px-4 py-3 text-sm">
                                            {teacher.first_name} {teacher.last_name}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-muted">{teacher.email}</td>
                                        <td className="px-4 py-3 text-sm text-muted">{teacher.institute || '-'}</td>
                                        <td className="px-4 py-3 text-sm text-muted">{teacher.department || '-'}</td>
                                        <td className="px-4 py-3 text-sm text-muted">{teacher.position || '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {selectedTeachers.length > 0 && (
                        <div className="mt-4 flex justify-end">
                            <button
                                onClick={handleAddTeachers}
                                disabled={adding}
                                className="px-6 py-2.5 bg-gradient-to-r from-green-600 to-green-500 text-white rounded-xl hover:from-green-700 hover:to-green-600 transition-all duration-300 font-bold shadow-lg shadow-green-500/20 text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <FaPlus className="w-4 h-4" />
                                {adding ? 'Adding...' : `Add Selected (${selectedTeachers.length})`}
                            </button>
                        </div>
                    )}
                </div>
            )}

        </div>
    );
};

export default CourseTeachers;

