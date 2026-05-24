import React, { useEffect, useState } from 'react';
import { FaArrowUp, FaArrowDown, FaPlus, FaTrash, FaPuzzlePiece } from 'react-icons/fa';
import useManageCourseStore from '../../store/manageCourseStore';

const CourseDesign = () => {
    const {
        course,
        designCourse, loadingDesignCourse, designCourseError,
        loadDesignCourse,
        handleAddModulesToCourse,
        handleRemoveModulesFromCourse,
        handleChangeCourseModuleOrder,
        handleChangeCourseModulePrerequisiteCompletion,
        handleChangeCourseModulePrerequisitePassing,
    } = useManageCourseStore();

    // UI state for selection
    const [selectedInSelected, setSelectedInSelected] = useState(null);
    const [selectedInPool, setSelectedInPool] = useState(null);

    // Local state for reordering before save
    const [localSelected, setLocalSelected] = useState([]);
    const [localPool, setLocalPool] = useState([]);

    // Sync local state with API data
    useEffect(() => {
        if (designCourse) {
            setLocalSelected([...designCourse.added_learning_modules].sort((a, b) => a.order - b.order));
            setLocalPool([...designCourse.learning_modules]);
            setSelectedInSelected(null);
            setSelectedInPool(null);
        }
    }, [designCourse]);

    // Load on mount/course change
    useEffect(() => {
        if (course?.id) loadDesignCourse(course.id);
    }, [course?.id, loadDesignCourse]);

    // Add module from pool to selected
    const addModule = async () => {
        if (selectedInPool !== null && course?.id) {
            await handleAddModulesToCourse(course.id, [selectedInPool]);
            setSelectedInPool(null);
        }
    };

    // Remove module from selected to pool
    const removeModule = async () => {
        if (selectedInSelected !== null && course?.id) {
            await handleRemoveModulesFromCourse(course.id, [selectedInSelected]);
            setSelectedInSelected(null);
        }
    };

    // Move up in selected
    const moveUp = async () => {
        if (selectedInSelected !== null) {
            const idx = localSelected.findIndex(m => m.id === selectedInSelected);
            if (idx > 0) {
                const newOrder = [...localSelected];
                [newOrder[idx - 1], newOrder[idx]] = [newOrder[idx], newOrder[idx - 1]];
                setLocalSelected(newOrder);
                // Persist order
                if (course?.id) {
                    const orderedList = newOrder.map((m, i) => `${m.id}:${i + 1}`);
                    await handleChangeCourseModuleOrder(course.id, orderedList);
                }
            }
        }
    };

    // Move down in selected
    const moveDown = async () => {
        if (selectedInSelected !== null) {
            const idx = localSelected.findIndex(m => m.id === selectedInSelected);
            if (idx < localSelected.length - 1) {
                const newOrder = [...localSelected];
                [newOrder[idx], newOrder[idx + 1]] = [newOrder[idx + 1], newOrder[idx]];
                setLocalSelected(newOrder);
                // Persist order
                if (course?.id) {
                    const orderedList = newOrder.map((m, i) => `${m.id}:${i + 1}`);
                    await handleChangeCourseModuleOrder(course.id, orderedList);
                }
            }
        }
    };

    // Selection handlers
    const handleSelectedClick = (moduleId) => {
        setSelectedInSelected(selectedInSelected === moduleId ? null : moduleId);
    };
    const handlePoolClick = (moduleId) => {
        setSelectedInPool(selectedInPool === moduleId ? null : moduleId);
    };

    // Loading/error UI
    if (loadingDesignCourse) {
        return (
            <div className="flex items-center justify-center min-h-[200px]">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
                <span className="text-blue-400">Loading course design...</span>
            </div>
        );
    }
    if (designCourseError) {
        return (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-300 text-center">
                {designCourseError}
            </div>
        );
    }

    return (
        <div className='px-1 mb-1'>
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center ">

                    <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" /></svg>
                </div>
                <div>
                    <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Course Design</h3>
                    <p className="text-xs muted">Organize your course modules</p>
                </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
                {/* Selected Modules */}
                <div className="card p-4 sm:p-6 border-2  transition-all duration-300 group bg-[var(--card-bg)] rounded-xl border-[var(--border-color)] hover:border-blue-500/70 dark:hover:border-blue-500/50 hover:shadow-lg bg-[var(--surface)]">
                    <div className="mb-3 sm:mb-4">
                        <h4 className="font-bold text-base sm:text-lg mb-1">Selected Modules</h4>
                        <p className="text-xs sm:text-sm muted">Modules currently in this course</p>
                    </div>
                    <div
                        className="space-y-2 sm:space-y-3 mb-3 sm:mb-4"
                        style={{ maxHeight: '290px', minHeight: '120px', overflowY: 'auto' }}
                    >
                        {localSelected.map((module) => {
                            const isSelected = selectedInSelected === module.id;
                            return (
                                <div key={module.id}>
                                    <div
                                        onClick={() => handleSelectedClick(module.id)}
                                        className={`flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg cursor-pointer transition active:scale-95 ${isSelected
                                            ? 'bg-red-600/20 border-2 border-red-600'
                                            : 'bg-[var(--surface-2)] border border-[var(--border-color)] hover:shadow-md hover:bg-white/[0.03] hover:border-red-400'
                                            }`}
                                    >
                                        <input
                                            type="radio"
                                            checked={isSelected}
                                            onChange={() => handleSelectedClick(module.id)}
                                            className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-600 flex-shrink-0"
                                        />
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium text-sm sm:text-base line-clamp-1">{module.name}</div>
                                            <div className="text-xs muted line-clamp-2" dangerouslySetInnerHTML={{ __html: module.description }} />
                                        </div>
                                    </div>
                                    {/* Slide-down panel for toggles */}
                                    <div
                                        className={`transition-all duration-300 overflow-hidden ${isSelected ? 'max-h-40 opacity-100 py-3' : 'max-h-0 opacity-0 py-0'}`}
                                        style={{ background: 'rgba(0,0,0,0.03)' }}
                                    >
                                        {isSelected && (
                                            <div className="bg-black/5 rounded-lg p-4 flex flex-col gap-4 shadow-inner border-2 border-[var(--border-color)]">
                                                <div className="font-semibold text-sm text-blue-400 mb-1">Prerequisite Options</div>
                                                <div className="flex items-center gap-3">
                                                    <input
                                                        id={`prereq-completion-${module.id}`}
                                                        type="checkbox"
                                                        checked={!!module.check_prerequisite}
                                                        onChange={async (e) => {
                                                            await handleChangeCourseModulePrerequisiteCompletion(course.id, [module.id]);
                                                        }}
                                                        className="accent-green-500 w-4 h-4"
                                                    />
                                                    <label htmlFor={`prereq-completion-${module.id}`} className="text-xs font-medium cursor-pointer">
                                                        Check Prerequisite <span className="font-semibold">Completion</span>
                                                    </label>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <input
                                                        id={`prereq-passing-${module.id}`}
                                                        type="checkbox"
                                                        checked={!!module.check_prerequisite_passes}
                                                        onChange={async (e) => {
                                                            await handleChangeCourseModulePrerequisitePassing(course.id, [module.id]);
                                                        }}
                                                        className="accent-green-500 w-4 h-4"
                                                    />
                                                    <label htmlFor={`prereq-passing-${module.id}`} className="text-xs font-medium cursor-pointer">
                                                        Check Prerequisite <span className="font-semibold">Passing</span>
                                                    </label>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                        {localSelected.length === 0 && (
                            <div className="text-center text-muted py-8">No modules in this course yet.</div>
                        )}
                    </div>
                    <div className="flex items-center justify-between gap-2 pt-3 sm:pt-4 border-t border-[var(--border-subtle)]">
                        <button
                            onClick={removeModule}
                            disabled={selectedInSelected === null}
                            className="px-4 py-2 border-2 border-red-500/50 hover:bg-red-500/10 text-red-500 rounded-xl font-bold transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent text-xs sm:text-sm"
                        >
                            <FaTrash className="inline" /> Remove
                        </button>
                        <div className="flex gap-2">
                            <button
                                onClick={moveUp}
                                disabled={selectedInSelected === null}
                                className="px-4 py-2 rounded-xl border-2 border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--border-subtle)] font-bold transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm"
                            >
                                <FaArrowUp className="w-3 h-3" />
                                <span className="hidden md:inline">Up</span>
                            </button>
                            <button
                                onClick={moveDown}
                                disabled={selectedInSelected === null}
                                className="px-4 py-2 rounded-xl border-2 border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--border-subtle)] font-bold transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm"
                            >
                                <FaArrowDown className="w-3 h-3" />
                                <span className="hidden md:inline">Down</span>
                            </button>
                        </div>
                    </div>
                </div>


                {/* Pool of Modules */}
                <div className="card p-4 sm:p-6 border-2 hover:shadow-lg transition-all duration-300 group bg-[var(--card-bg)] rounded-xl border-[var(--border-color)] hover:border-blue-500/70 dark:hover:border-blue-500/50 bg-[var(--surface)]">
                    <div className="mb-3 sm:mb-4">
                        <h4 className="font-bold text-base sm:text-lg mb-1">Pool of Modules</h4>
                        <p className="text-xs sm:text-sm muted">Available modules to add</p>
                    </div>
                    <div className="space-y-2 sm:space-y-3 mb-3 sm:mb-4"
                        style={{ maxHeight: '290px', minHeight: '120px', overflowY: 'auto' }}
                    >
                        {localPool.map((module) => (
                            <div
                                key={module.id}
                                onClick={() => handlePoolClick(module.id)}
                                className={`flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg cursor-pointer transition active:scale-95 ${selectedInPool === module.id
                                    ? 'bg-green-600/20 border-2 border-green-600'
                                    : 'bg-[var(--surface-2)] border border-[var(--border-color)] hover:shadow-md hover:bg-white/[0.03] hover:border-green-400'
                                    }`}
                            >
                                <input
                                    type="radio"
                                    checked={selectedInPool === module.id}
                                    onChange={() => handlePoolClick(module.id)}
                                    className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-blue-600 flex-shrink-0"
                                />
                                <div className="flex-1 min-w-0">
                                    <div className="font-medium text-sm sm:text-base line-clamp-1">{module.name}</div>
                                    <div className="text-xs muted line-clamp-2" dangerouslySetInnerHTML={{ __html: module.description }} />
                                </div>
                            </div>
                        ))}
                        {localPool.length === 0 && (
                            <div className="flex flex-col items-center justify-center py-12 sm:py-16 text-center">
                                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-[var(--surface)] flex items-center justify-center mb-3 sm:mb-4">
                                    <FaPlus className="w-5 h-5 sm:w-6 sm:h-6 text-[var(--text-muted)]" />
                                </div>
                                <p className="text-xs sm:text-sm text-muted max-w-[200px]">
                                    All modules are selected
                                </p>
                            </div>
                        )}
                    </div>
                    <div className="flex items-center justify-between gap-2 pt-3 sm:pt-4 border-t border-[var(--border-subtle)]">
                        <button
                            onClick={addModule}
                            disabled={selectedInPool === null}
                            className="px-4 py-2 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 text-white rounded-xl font-bold transition-all duration-300 shadow-lg shadow-green-500/20 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm"
                        >
                            <FaPlus className="inline" /> Add
                        </button>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default CourseDesign;