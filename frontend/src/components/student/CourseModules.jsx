/* filepath: /home/bhotto/projects04/online_test/frontend/src/components/student/CourseModules.jsx */
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import useManageCourseStore from '../../store/student/manageCourseStore';
import {
    FaClipboardList,
    FaCheckCircle,
    FaLock,
    FaPlay,
    FaVideo,
    FaPuzzlePiece,
    FaChevronDown,
    FaChevronUp,
    FaLayerGroup,
    FaClock,
    FaSpinner
} from 'react-icons/fa';


const CourseModules = () => {
    const { modules, modulesLoading, modulesError } = useManageCourseStore();
    const { courseId } = useParams();
    const navigate = useNavigate();

    // State to track expanded module
    const [expandedModuleId, setExpandedModuleId] = useState(null);

    const handleUnitClick = (module, unit) => {
        if (unit.type === 'quiz') {
            navigate(`/courses/${courseId}/quizzes/${unit.quiz?.id}`);
        } else if (unit.type === 'lesson') {
            navigate(`/lessons/${unit.lesson?.id}`);
        }
    };

    const handleViewAnswerPaper = (unit) => {
        if (unit.type === 'quiz' && unit.quiz?.questionpaper_id) {
            navigate(`/student/courses/${courseId}/view-answerpaper/${unit.quiz.questionpaper_id}`);
        }
    };

    const toggleModule = (moduleId) => {
        if (expandedModuleId === moduleId) {
            setExpandedModuleId(null);
        } else {
            setExpandedModuleId(moduleId);
        }
    };

    if (modulesLoading) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-2"></div>
                <p className="text-[var(--text-muted)] text-sm">Loading modules...</p>
            </div>
        );
    }

    if (modulesError) {
        return (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-center">
                <p>{modulesError}</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header Section */}
            <div className="flex items-center justify-between mb-4 px-1">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center">
                        <FaLayerGroup className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                        <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Course Modules</h3>
                        <p className="text-xs muted">Track your learning progress</p>
                    </div>
                </div>
                {modules.length > 0 && (
                    <span className="text-xs font-bold text-[var(--text-secondary)] bg-[var(--input-bg)] border-2 border-[var(--border-color)] px-3 py-1.5 rounded-xl shadow-md">
                        Total: <span className="text-cyan-600 dark:text-cyan-400">{modules.length}</span>
                    </span>
                )}
            </div>

            {!modules.length && (
                <div className="text-center py-12 bg-[var(--input-bg)] border-2 border-dashed border-[var(--border-color)] rounded-xl">
                    <div className="mb-4 p-4 bg-cyan-500/10 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
                        <FaLayerGroup className="text-cyan-400 w-8 h-8" />
                    </div>
                    <p className="text-[var(--text-primary)] font-semibold">No modules available for this course yet.</p>
                    <p className="text-xs muted mt-2">Check back later for content</p>
                </div>
            )}

            <div className="space-y-5">
                {modules.map((module, index) => {
                    const isExpanded = expandedModuleId === module.id;
                    const isCompleted = module.progress >= 100;

                    return (
                        <div
                            key={module.id}
                            className={`
                                relative border-2 hover:shadow-lg transition-all duration-300 group bg-[var(--card-bg)] rounded-xl
                                ${isExpanded ? 'border-blue-500/70 dark:border-blue-500/50 bg-[var(--surface-2)]' : 'border-[var(--border-color)] hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 bg-[var(--surface)]'}
                            `}
                        >
                            {/* Module Row Header */}
                            <div className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">

                                {/* Info Section */}
                                <div className="flex-1 min-w-0 flex items-start sm:items-center gap-4">
                                    {/* Icon Box */}
                                    <div className={`p-3 rounded-xl shrink-0 transition-all duration-300 border-2 shadow-lg ${isExpanded
                                        ? 'bg-blue-500/15 border-blue-500/30 text-blue-400'
                                        : 'bg-[var(--input-bg)] border-[var(--border-color)] text-gray-600 dark:text-gray-400'
                                        }`}>
                                        <FaLayerGroup className="w-5 h-5" />
                                    </div>

                                    {/* Text Info */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                                            <h3 className={`font-bold text-base sm:text-lg truncate group-hover:text-blue-500 transition-colors ${isExpanded ? 'text-blue-600 dark:text-blue-400' : 'text-[var(--text-primary)]'
                                                }`}>
                                                {module.name}
                                            </h3>
                                            {isCompleted && (
                                                <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border-2 border-emerald-500/30 shadow-md shadow-emerald-500/20">
                                                    <FaCheckCircle size={10} /> COMPLETED
                                                </span>
                                            )}
                                        </div>
                                        {module.description && (
                                            <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-1 max-w-md hidden sm:block">
                                                {module.description}
                                            </p>
                                        )}
                                    </div>
                                </div>

                                {/* Divider for Mobile */}
                                <div className="h-px w-full bg-white/5 md:hidden"></div>

                                {/* Right: Stats & Action */}
                                <div className="flex items-center justify-between md:justify-end gap-4 w-full md:w-auto">

                                    {/* Progress */}
                                    <div className="flex flex-col items-end min-w-[120px]">
                                        <div className="flex items-center justify-between w-full mb-1.5">
                                            <span className="text-[10px] uppercase text-[var(--text-muted)] font-bold tracking-wider">Progress</span>
                                            <div className="flex items-center gap-1.5">
                                                {isExpanded && !isCompleted && <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 dark:bg-cyan-400 animate-pulse shadow-lg shadow-cyan-500/50"></div>}
                                                <span className={`text-xs font-bold ${isCompleted
                                                    ? 'text-emerald-600 dark:text-emerald-400'
                                                    : 'text-cyan-600 dark:text-cyan-400'
                                                    }`}>
                                                    {Math.round(module.progress || 0)}%
                                                </span>
                                            </div>
                                        </div>
                                        {/* Progress Bar Container */}
                                        <div className="h-2.5 w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-full overflow-hidden relative shadow-inner">
                                            <div
                                                className={`h-full rounded-full transition-all duration-1000 ease-out relative shadow-lg ${isCompleted
                                                    ? 'bg-gradient-to-r from-green-500 to-emerald-400 shadow-emerald-500/50'
                                                    : 'bg-gradient-to-r from-blue-600 to-cyan-400 shadow-blue-500/50'
                                                    }`}
                                                style={{ width: `${module.progress || 0}%` }}
                                            >
                                                {/* Shine effect */}
                                                <div className="absolute top-0 left-0 bottom-0 right-0 bg-gradient-to-b from-white/30 to-transparent"></div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Units Badge Desktop */}
                                    <div className="hidden lg:flex flex-col items-center justify-center px-4 py-1.5 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-color)] min-w-[70px] shadow-md">
                                        <div className="text-sm font-bold text-[var(--text-primary)]">{module.units ? module.units.length : 0}</div>
                                        <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest font-bold">Units</div>
                                    </div>

                                    {/* Toggle CTA */}
                                    <button
                                        onClick={() => toggleModule(module.id)}
                                        className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300 border-2 ${isExpanded
                                            ? 'bg-blue-500/15 border-blue-500/30 text-blue-400'
                                            : 'bg-[var(--input-bg)] border-[var(--border-color)] text-gray-600 dark:text-gray-400'
                                            }`}
                                    >
                                        {isExpanded ? <FaChevronUp size={14} /> : <FaChevronDown size={14} />}
                                    </button>
                                </div>
                            </div>

                            {/* Dropdown Content */}
                            {isExpanded && (
                                <div className="border-t-2 border-[var(--border-subtle)] bg-[var(--input-bg)] animate-fadeIn relative shadow-inner">


                                    {(!module.units || module.units.length === 0) ? (
                                        <div className="p-8 text-center text-[var(--text-muted)] text-sm italic bg-[var(--surface)] border border-dashed border-[var(--border-color)] rounded-lg m-4">
                                            No learning units available in this module.
                                        </div>
                                    ) : (
                                        <>
                                            {/* --- DESKTOP TABLE VIEW (MD+) --- */}
                                            <div className="hidden md:block overflow-x-auto">
                                                <table className="w-full text-left text-sm">
                                                    <thead className="text-xs uppercase text-[var(--text-muted)] bg-[var(--surface)] font-semibold border-b border-[var(--border-color)]">
                                                        <tr>
                                                            <th className="pl-8 pr-4 py-4 w-[140px]">Status</th>
                                                            <th className="px-4 py-4">Unit Details</th>
                                                            <th className="px-4 py-4">Type</th>
                                                            <th className="px-4 py-4 text-right pr-8">Actions</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-[var(--border-subtle)]">
                                                        {module.units.map((unit) => {
                                                            const unitName = unit.type === 'lesson' ? unit.lesson?.name : (unit.quiz?.description || unit.quiz?.name || `Quiz ${unit.order}`);
                                                            const isLocked = unit.check_prerequisite && unit.status === 'locked';
                                                            const isUnitCompleted = unit.status === 'completed' || unit.status === 'passed';
                                                            const isUnitQuitted = unit.status === 'quit';
                                                            const isInProgress = unit.status === 'inprogress';

                                                            return (
                                                                <tr key={unit.id} className="hover:bg-white/[0.02] transition-colors group">
                                                                    <td className="pl-8 pr-4 py-4 whitespace-nowrap align-middle">
                                                                        {isLocked ? (
                                                                            <div className="flex items-center gap-2 text-gray-400 bg-gray-800/40 px-2.5 py-1 rounded-md border border-gray-700/50 w-fit">
                                                                                <FaLock size={10} /> <span className="text-[10px] font-bold uppercase">Locked</span>
                                                                            </div>
                                                                        ) : isUnitCompleted ? (
                                                                            <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20 w-fit shadow-[0_0_10px_rgba(16,185,129,0.1)]">
                                                                                <FaCheckCircle size={10} /> <span className="text-[10px] font-bold uppercase">Completed </span>
                                                                            </div>
                                                                        ) : isInProgress ? (
                                                                            <div className="flex items-center gap-2 text-amber-500 bg-amber-500/10 px-2.5 py-1 rounded-md border border-amber-500/20 w-fit shadow-[0_0_10px_rgba(251,191,36,0.1)]">
                                                                                <FaSpinner className="animate-spin" size={10} /> <span className="text-[10px] font-bold uppercase">In Progress</span>
                                                                            </div>
                                                                        ) : isUnitQuitted ? (
                                                                            <div className="flex items-center gap-2 text-red-400 bg-red-500/10 px-2.5 py-1 rounded-md border border-red-500/20 w-fit shadow-[0_0_10px_rgba(239,68,68,0.1)]">
                                                                                <FaCheckCircle size={10} /> <span className="text-[10px] font-bold uppercase">Quitted</span>
                                                                            </div>
                                                                        ) : (
                                                                            <div className="flex items-center gap-2 text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-md border border-blue-500/20 w-fit shadow-[0_0_10px_rgba(59,130,246,0.1)]">
                                                                                <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
                                                                                <span className="text-[10px] font-bold uppercase">Not Started</span>
                                                                            </div>
                                                                        )}
                                                                    </td>

                                                                    <td className="px-4 py-4 align-middle">
                                                                        <div className="flex flex-col">
                                                                            <span className="text-[var(--text-primary)] font-medium group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors">{unitName}</span>
                                                                            <span className="text-[11px] text-[var(--text-muted)] font-mono mt-0.5">ORDER #{unit.order}</span>
                                                                        </div>
                                                                    </td>

                                                                    <td className="px-4 py-4 align-middle">
                                                                        {unit.type === 'lesson' ? (
                                                                            <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-300 text-xs bg-cyan-500/10 dark:bg-cyan-950/30 px-3 py-1.5 rounded-xl w-fit border border-cyan-500/30">
                                                                                <FaVideo className="text-cyan-500 dark:text-cyan-400" size={12} />
                                                                                <span className="capitalize font-medium">Lesson</span>
                                                                            </div>
                                                                        ) : unit.quiz.is_exercise ? (
                                                                            <div className="flex items-center gap-2 text-purple-600 dark:text-purple-300 text-xs bg-purple-500/10 dark:bg-purple-950/30 px-3 py-1.5 rounded-xl w-fit border border-purple-500/30">
                                                                                <FaPuzzlePiece className="text-purple-500 dark:text-purple-400" size={12} />
                                                                                <span className="capitalize font-medium">Exercise</span>
                                                                            </div>

                                                                        ) : (
                                                                            <div className="flex items-center gap-2 text-green-600 dark:text-green-300 text-xs bg-green-500/10 dark:bg-green-950/30 px-3 py-1.5 rounded-xl w-fit border border-green-500/30">
                                                                                <svg className="w-4 h-4 text-green-500 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                                </svg>

                                                                                <span className="capitalize font-medium">Quiz</span>
                                                                            </div>
                                                                        )}
                                                                    </td>

                                                                    <td className="px-4 py-4 text-right pr-8 align-middle">
                                                                        <DesktopActionButtons
                                                                            unit={unit}
                                                                            module={module}
                                                                            isLocked={isLocked}
                                                                            isUnitCompleted={isUnitCompleted}
                                                                            isUnitQuitted={isUnitQuitted}
                                                                            isInProgress={isInProgress}
                                                                            handleUnitClick={handleUnitClick}
                                                                            handleViewAnswerPaper={handleViewAnswerPaper}
                                                                        />
                                                                    </td>
                                                                </tr>
                                                            );
                                                        })}
                                                    </tbody>
                                                </table>
                                            </div>

                                            {/* --- MOBILE CARD VIEW (< MD) --- */}
                                            <div className="md:hidden space-y-4 p-4">
                                                {module.units.map((unit) => {
                                                    const unitName = unit.type === 'lesson' ? unit.lesson?.name : (unit.quiz?.description || unit.quiz?.name || `Quiz ${unit.order}`);
                                                    const isLocked = unit.check_prerequisite && unit.status === 'locked';
                                                    const isUnitQuitted = unit.status === 'quit';
                                                    const isUnitCompleted = unit.status === 'completed' || unit.status === 'passed';
                                                    const isInProgress = unit.status === 'inprogress';

                                                    return (
                                                        <div key={unit.id} className="bg-[var(--input-bg)] rounded-lg p-4 border-2 border-[var(--border-color)] relative overflow-hidden shadow-md">

                                                            <div className="flex justify-between items-start gap-3 mb-3">
                                                                <div className="flex-1">
                                                                    <div className="flex items-center gap-2 mb-1">
                                                                        {unit.type === 'lesson' ? (
                                                                            <span className="text-[10px] uppercase font-bold px-1.5 rounded bg-cyan-500/10 dark:bg-cyan-900/40 text-cyan-600 dark:text-cyan-300 border border-cyan-500/30">
                                                                                Lesson
                                                                            </span>
                                                                        ) : (
                                                                            <span className="text-[10px] uppercase font-bold px-1.5 rounded bg-purple-500/10 dark:bg-purple-900/40 text-purple-600 dark:text-purple-300 border border-purple-500/30">
                                                                                Quiz
                                                                            </span>
                                                                        )}


                                                                    </div>
                                                                    <h4 className="text-sm font-bold text-[var(--text-primary)] line-clamp-2 leading-tight">{unitName}</h4>
                                                                </div>

                                                                {/* Mobile Status Badge */}
                                                                <div>
                                                                    {isLocked ? (
                                                                        <FaLock className="text-gray-400 dark:text-gray-600" size={14} />
                                                                    ) : isUnitCompleted ? (
                                                                        <FaCheckCircle className="text-emerald-500" size={16} />
                                                                    ) : isInProgress ? (
                                                                        <FaSpinner className="text-amber-500 animate-spin" size={16} />
                                                                    ) : isUnitQuitted ? (
                                                                        <FaCheckCircle className="text-red-500" size={16} />
                                                                    ) : (
                                                                        <div className="w-3 h-3 rounded-full border-2 border-blue-500 bg-blue-500"></div>
                                                                    )}
                                                                </div>
                                                            </div>

                                                            <div className="flex items-center justify-between pt-3 border-t border-[var(--border-subtle)]">
                                                                <div className="text-[10px] text-[var(--text-muted)]">
                                                                    Unit Order: {unit.order}
                                                                </div>
                                                                <DesktopActionButtons
                                                                    unit={unit}
                                                                    module={module}
                                                                    isLocked={isLocked}
                                                                    isUnitCompleted={isUnitCompleted}
                                                                    isUnitQuitted={isUnitQuitted}
                                                                    isInProgress={isInProgress}
                                                                    handleUnitClick={handleUnitClick}
                                                                    handleViewAnswerPaper={handleViewAnswerPaper}
                                                                    isMobile={true}
                                                                />
                                                            </div>
                                                        </div>
                                                    )
                                                })}
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// Helper Component for consistent buttons across Mobile/Desktop
const DesktopActionButtons = ({ unit, module, isLocked, isUnitCompleted, isInProgress, isUnitQuitted, handleUnitClick, handleViewAnswerPaper, isMobile }) => {
    return (
        <div className="flex items-center gap-2 justify-end">
            {!isLocked && unit.type === 'quiz' && unit.quiz?.view_answerpaper && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        if (handleViewAnswerPaper) handleViewAnswerPaper(unit);
                    }}
                    className="px-3 py-1.5 text-blue-500 bg-blue-500/10 hover:bg-blue-500/20 rounded-lg transition-colors border border-blue-500/20 flex items-center gap-2 text-xs font-medium"
                >
                    <FaClipboardList className="w-3 h-3" /> {isMobile ? "Ans." : "Answer Paper"}
                </button>
            )}

            {!isLocked && !isUnitCompleted && isInProgress && !isUnitQuitted && (
                <button
                    onClick={() => handleUnitClick(module, unit)}
                    className="px-4 py-1.5 rounded-lg text-white text-xs font-bold transition-all shadow-lg shadow-amber-500/20 bg-amber-600 hover:bg-amber-500 hover:shadow-amber-500/40 flex items-center gap-1.5"
                >
                    Resume <FaPlay size={10} />
                </button>
            )}

            {!isLocked && !isUnitCompleted && !isInProgress && !isUnitQuitted && (
                <button
                    onClick={() => handleUnitClick(module, unit)}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-white text-xs font-bold transition-all shadow-lg shadow-blue-500/20 bg-blue-600 hover:bg-blue-500 hover:shadow-blue-500/40"
                >
                    Start <FaPlay size={10} />
                </button>
            )}

            {/* FIX HERE: Only check if it was quitted (which implies it failed/aborted) */}
            {(isUnitQuitted || isUnitCompleted) && (
                <button
                    onClick={() => handleUnitClick(module, unit)}
                    className="flex items-center gap-1.5 text-gray-600 hover:text-red-500 text-xs px-4 py-1.5 rounded-lg border border-transparent hover:border-white/10 hover:bg-white/5 transition"
                >
                    Retry <FaPlay size={10} />
                </button>
            )}

            {isLocked && (
                <span className="text-gray-600 px-2 py-1 text-xs italic flex items-center gap-1">
                    Wait <FaClock size={10} />
                </span>
            )}
            {isLocked && (
                <span className="text-gray-600 px-2 py-1 text-xs italic flex items-center gap-1">
                    Wait <FaClock size={10} />
                </span>
            )}
        </div>
    );
};

export default CourseModules;
