import React, { useState, useEffect, useRef } from 'react';
import { FaPlus, FaBook, FaCalendarAlt, FaEdit, FaTrash, FaCheckCircle, FaEllipsisV, FaVideo, FaTimes, FaUpload, FaFileAlt, FaExternalLinkAlt, FaArrowUp, FaArrowDown, FaCheck, FaQuestionCircle, FaRandom, FaList, FaSync, FaSearch, FaPuzzlePiece, FaChevronDown, FaChevronUp, FaLayerGroup } from 'react-icons/fa';
import useManageCourseStore from '../../store/manageCourseStore';
import { useSandboxStore } from '../../store/sandboxStore';
import { useNavigate, useParams } from 'react-router-dom';
import { FaBookOpen } from 'react-icons/fa';

const CourseModules = () => {
    const {
        modules,
        showModuleForm,
        editingModule,
        moduleFormData,
        handleModuleFormChange,
        handleCreateModule,
        handleUpdateModule,
        setShowModuleForm,
        setEditingModule,
        showLessonForm,
        editingLesson,
        lessonFormData,
        handleLessonFormChange,
        handleCreateLesson,
        handleUpdateLesson,
        setShowLessonForm,
        setSelectedModule,
        setEditingLesson,
        showQuizForm,
        editingQuiz,
        quizFormData,
        handleQuizFormChange,
        handleCreateQuiz,
        handleUpdateQuiz,
        setShowQuizForm,
        setSelectedModule: setSelectedModuleQuiz,
        setEditingQuiz,
        openCreateLesson,
        openCreateQuiz,
        openEditModule,
        handleDeleteModule,
        openEditLesson,
        handleDeleteLesson,
        openEditQuiz,
        handleDeleteQuiz,
        showExerciseForm,
        editingExercise,
        setEditingExercise,
        exerciseFormData,
        handleExerciseFormChange,
        handleCreateExercise,
        handleUpdateExercise,
        setShowExerciseForm,
        openCreateExercise,
        openEditExercise,
        handleDeleteExercise,
        setModuleFormData,
        setLessonFormData,
        showDesignModuleModal,
        designModule,
        loadingDesignModule,
        designModuleError,
        designingModuleId,
        openDesignModule,
        closeDesignModule,
        handleAddUnitsToModule,
        handleRemoveUnitsFromModule,
        handleChangeModuleUnitOrder,
        handleChangeModuleUnitPrerequisite,
        questionPaperDesign,
        filteredQuestions,
        loadingQuestionPaper,
        questionPaperError,
        showDesignQuestionPaperModal,
        designingQuizId,
        designingQuizName,
        openDesignQuestionPaper,
        closeDesignQuestionPaper,
        handleAddFixedQuestions,
        handleRemoveFixedQuestions,
        handleAddRandomQuestionsSet,
        handleRemoveRandomQuestionsSet,
        handleSaveQuestionPaperOptions,
        handleFilterQuestionPaperQuestions

    } = useManageCourseStore();

    const { courseId } = useParams();
    // Inside CourseModules component definition:
    const navigate = useNavigate();
    const { isGenerating, generateTestSandbox } = useSandboxStore();


    // Dropdown state management
    const [openDropdownId, setOpenDropdownId] = useState(null);
    const dropdownRef = useRef(null);

    // Collapsible module state
    const [expandedModuleId, setExpandedModuleId] = useState(null);

    const toggleModule = (moduleId) => {
        if (expandedModuleId === moduleId) {
            setExpandedModuleId(null);
        } else {
            setExpandedModuleId(moduleId);
        }
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setOpenDropdownId(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleDropdown = (moduleId) => {
        setOpenDropdownId(openDropdownId === moduleId ? null : moduleId);
    };

    // Toggle handlers for the module form
    const handleToggleActive = () => {
        setModuleFormData({
            ...moduleFormData,
            active: !moduleFormData.active
        });
    };

    // Toggle handler for lesson form
    const handleLessonToggleActive = () => {
        setLessonFormData({
            ...lessonFormData,
            active: !lessonFormData.active
        });
    };

    // Handle lesson form submission
    const handleLessonSubmit = (e) => {
        e.preventDefault();
        if (editingLesson) {
            handleUpdateLesson();
        } else {
            handleCreateLesson();
        }
    };

    const handleExerciseSubmit = (e) => {
        e.preventDefault();
        if (editingExercise) {
            handleUpdateExercise();
        } else {
            handleCreateExercise();
        }
    };



    // Helper to get embed URL
    const getVideoEmbedUrl = (url) => {
        if (!url) return null;

        // YouTube
        const youtubeRegex = /^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const ytMatch = url.match(youtubeRegex);
        if (ytMatch && ytMatch[1]) {
            return { type: 'iframe', url: `https://www.youtube.com/embed/${ytMatch[1]}` };
        }

        // Vimeo
        const vimeoRegex = /^(?:https?:\/\/)?(?:www\.)?(?:vimeo\.com\/)(\d+)/;
        const vimeoMatch = url.match(vimeoRegex);
        if (vimeoMatch && vimeoMatch[1]) {
            return { type: 'iframe', url: `https://player.vimeo.com/video/${vimeoMatch[1]}` };
        }

        // Direct Video File (simple check for extension or if it looks like a url)
        if (url.match(/\.(mp4|webm|ogg)$/i) || url.startsWith('http')) {
            return { type: 'video', url: url };
        }

        return null;
    };

    const videoPreview = getVideoEmbedUrl(lessonFormData.video_path);

    const handleClearVideo = () => {
        setLessonFormData({
            ...lessonFormData,
            video_path: ''
        });
    };



    const handleRemoveExistingFile = (fileId) => {
        if (!window.confirm("Mark this file for deletion logic? (Will be deleted on Save)")) return;

        const updatedFiles = lessonFormData.files.filter(f => f.id !== fileId);
        const filesToDelete = [...(lessonFormData.filesToDelete || []), fileId];

        setLessonFormData({
            ...lessonFormData,
            files: updatedFiles,
            filesToDelete: filesToDelete
        });
    };

    const handleClearUploadedVideo = () => {
        // Clears selected file input and marks existing video for removal
        setLessonFormData({
            ...lessonFormData,
            video_file: null,
            newVideoFile: null,
            existing_video_file_url: null,
            clearVideoFile: true
        });

        // Helper to reset file input value visually
        const fileInput = document.getElementById('video-file-upload');
        if (fileInput) fileInput.value = "";
    };


    // --- DESIGN MODULE LOCAL STATE ---
    const [selectedInSelected, setSelectedInSelected] = useState(null); // ID of selected unit (Left side)
    const [selectedInPool, setSelectedInPool] = useState(null); // ValueKey of selected pool item (Right side)

    // Local state for immediate UI updates before API refresh
    const [localSelected, setLocalSelected] = useState([]);
    const [localPool, setLocalPool] = useState([]);

    // Sync local state with API data when modal opens or data changes
    useEffect(() => {
        if (designModule) {
            // Sort units by order
            const sortedUnits = [...(designModule.learning_units || [])].sort((a, b) => a.order - b.order);
            setLocalSelected(sortedUnits);
            setLocalPool(designModule.quiz_les_list || []);
            setSelectedInSelected(null);
            setSelectedInPool(null);
        }
    }, [designModule]);

    // HANDLERS FOR DESIGN MODAL

    // Add item from Pool -> Module
    const handleAddUnit = async () => {
        if (selectedInPool && designingModuleId) {
            // selectedInPool is the value_key (e.g., "5:lesson")
            await handleAddUnitsToModule(designingModuleId, [selectedInPool], courseId);
            setSelectedInPool(null);
        }
    };

    // Remove item from Module -> Pool
    const handleRemoveUnit = async () => {
        if (selectedInSelected && designingModuleId) {
            // selectedInSelected is the unit.id
            await handleRemoveUnitsFromModule(designingModuleId, [selectedInSelected], courseId);
            setSelectedInSelected(null);
        }
    };

    // Reorder: Move Up
    const moveUp = async () => {
        if (selectedInSelected !== null) {
            const idx = localSelected.findIndex(u => u.id === selectedInSelected);
            if (idx > 0) {
                const newOrderList = [...localSelected];
                // Swap
                [newOrderList[idx - 1], newOrderList[idx]] = [newOrderList[idx], newOrderList[idx - 1]];
                setLocalSelected(newOrderList);

                // Construct API payload "unit_id:order"
                const orderedListPayload = newOrderList.map((u, i) => `${u.id}:${i + 1}`);
                await handleChangeModuleUnitOrder(designingModuleId, orderedListPayload, courseId);
            }
        }
    };

    // Reorder: Move Down
    const moveDown = async () => {
        if (selectedInSelected !== null) {
            const idx = localSelected.findIndex(u => u.id === selectedInSelected);
            if (idx < localSelected.length - 1) {
                const newOrderList = [...localSelected];
                // Swap
                [newOrderList[idx], newOrderList[idx + 1]] = [newOrderList[idx + 1], newOrderList[idx]];
                setLocalSelected(newOrderList);

                // Construct API payload "unit_id:order"
                const orderedListPayload = newOrderList.map((u, i) => `${u.id}:${i + 1}`);
                await handleChangeModuleUnitOrder(designingModuleId, orderedListPayload, courseId);
            }
        }
    };

    // Toggle Prerequisite
    const handleTogglePrereq = async (unitId) => {
        if (designingModuleId) {
            await handleChangeModuleUnitPrerequisite(designingModuleId, [unitId], courseId);
        }
    };

    {/* DESIGN QUESTION PAPER MODAL */ }

    const [qPaperTab, setQPaperTab] = useState('FIXED');
    const [shuffleQuestions, setShuffleQuestions] = useState(false);
    const [shuffleTestcases, setShuffleTestcases] = useState(false);

    // Filtering State
    const [filterMarks, setFilterMarks] = useState('');
    const [filterTags, setFilterTags] = useState('');
    const [filterType, setFilterType] = useState('');

    // Checkbox Selections
    const [selectedPoolQs, setSelectedPoolQs] = useState([]);
    const [selectedFixedQs, setSelectedFixedQs] = useState([]);
    const [selectedRandomSets, setSelectedRandomSets] = useState([]);

    // Random Set Creation State
    const [randomSetMarks, setRandomSetMarks] = useState('');
    const [randomSetCount, setRandomSetCount] = useState('');

    const paperId = questionPaperDesign?.question_paper?.id;

    const handleSearchQPaper = () => {
        handleFilterQuestionPaperQuestions(courseId, designingQuizId, paperId, {
            marks: filterMarks,
            tags: filterTags,
            type: filterType
        });
        setSelectedPoolQs([]);
    };

    const handleAddFixed = async () => {
        if (!selectedPoolQs.length) return;
        await handleAddFixedQuestions(courseId, designingQuizId, paperId, selectedPoolQs);
        setSelectedPoolQs([]);
    };

    const handleRemoveFixed = async () => {
        if (!selectedFixedQs.length) return;
        await handleRemoveFixedQuestions(courseId, designingQuizId, paperId, selectedFixedQs);
        setSelectedFixedQs([]);
    };

    const handleAddRandomSet = async () => {
        if (!selectedPoolQs.length || !randomSetCount) {
            alert('Please select matching pool items and the number of questions to pick.');
            return;
        }

        // Auto-assign marks based on the first selected question in the pool (backend requires a value)
        const firstSelectedQ = availableQuestions.find(q => q.id === selectedPoolQs[0]);
        const autoMarks = firstSelectedQ?.points || 1;

        await handleAddRandomQuestionsSet(courseId, designingQuizId, paperId, selectedPoolQs, autoMarks, randomSetCount);

        setSelectedPoolQs([]);
        setRandomSetMarks('');
        setRandomSetCount('');
    };

    const handleRemoveRandomSets = async () => {
        if (!selectedRandomSets.length) return;
        await handleRemoveRandomQuestionsSet(courseId, designingQuizId, paperId, selectedRandomSets);
        setSelectedRandomSets([]);
    };

    const handleSaveQPaperSettings = async (e) => {
        e.preventDefault();
        try {
            await handleSaveQuestionPaperOptions(courseId, designingQuizId, paperId, {
                shuffle_questions: shuffleQuestions,
                shuffle_testcases: shuffleTestcases,
            });
            // Automatically close the modal after successfully saving
            closeDesignQuestionPaper();
        } catch (error) {
            console.error("Failed to save paper settings:", error);
            alert("Failed to save settings. Please try again.");
        }
    };

    const toggleQPaperSelection = (id, list, setList) => {
        if (list.includes(id)) setList(list.filter(item => item !== id));
        else setList([...list, id]);
    };

    const availableQuestions = filteredQuestions?.filtered_questions || [];

    useEffect(() => {
        if (questionPaperDesign?.question_paper) {
            setShuffleQuestions(questionPaperDesign.question_paper.shuffle_questions || false);
            setShuffleTestcases(questionPaperDesign.question_paper.shuffle_testcases || false);
        }
    }, [questionPaperDesign]);


    const [expandedRandomSets, setExpandedRandomSets] = useState([]);



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
                        <p className="text-xs muted">Manage course content & structure</p>
                    </div>
                </div>
                {modules.length > 0 && (
                    <span className="text-xs font-bold text-[var(--text-secondary)] bg-[var(--input-bg)] border-2 border-[var(--border-color)] px-3 py-1.5 rounded-xl shadow-md">
                        Total: <span className="text-cyan-600 dark:text-cyan-400">{modules.length}</span>
                    </span>
                )}
            </div>


            {/* MODULE FORM MODAL */}
            {showModuleForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto">
                    <div className="card-strong w-full max-w-full sm:max-w-2xl p-4 sm:p-6 relative my-4 rounded-2xl border-2 border-[var(--border-strong)] max-h-[90vh] overflow-y-auto">
                        {/* Close (Cross) Button */}
                        <button
                            className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all z-10"
                            onClick={() => {
                                setShowModuleForm(false);
                                setEditingModule(null);
                            }}
                            aria-label="Close"
                        >
                            <FaTimes />
                        </button>
                        {/* Header */}
                        <div className="flex flex-row items-center gap-4 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)] pr-12">
                            <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                                <FaLayerGroup className="w-7 h-7 sm:w-8 sm:h-8 text-blue-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1">
                                    {editingModule ? 'Edit Module' : 'Create New Module'}
                                </h2>
                                <p className="text-xs sm:text-sm muted line-clamp-2">
                                    {editingModule
                                        ? 'Update the details of this module.'
                                        : 'Add a new module to your course.'}
                                </p>
                            </div>
                        </div>
                        {/* Form */}
                        <form
                            onSubmit={e => {
                                e.preventDefault();
                                if (editingModule) {
                                    handleUpdateModule(courseId);
                                } else {
                                    handleCreateModule(courseId);
                                }
                            }}
                            className="space-y-4 sm:space-y-5"
                        >
                            <div className="flex flex-col gap-4">
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">Module Name</label>
                                    <input
                                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                                        name="name"
                                        placeholder="Enter module name *"
                                        value={moduleFormData.name}
                                        onChange={handleModuleFormChange}
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">Description</label>
                                    <textarea
                                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors resize-none"
                                        name="description"
                                        placeholder="Enter description (markdown supported)"
                                        value={moduleFormData.description}
                                        onChange={handleModuleFormChange}
                                        rows={4}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-xs sm:text-sm font-semibold mb-2">Order</label>
                                <input
                                    className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                                    type="number"
                                    name="order"
                                    placeholder="Order priority"
                                    value={moduleFormData.order}
                                    onChange={handleModuleFormChange}
                                />
                            </div>

                            {/* Toggle Switches */}
                            <div className="space-y-3 pt-2">
                                <div className="flex items-center justify-between p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex-1">
                                        <span className="text-sm sm:text-base font-semibold text-[var(--text-primary)]">Active Status</span>
                                        <p className="text-xs muted mt-0.5">Make this module visible to students</p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={handleToggleActive}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${moduleFormData.active ? 'bg-blue-600' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span
                                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${moduleFormData.active ? 'translate-x-6' : 'translate-x-1'
                                                }`}
                                        />
                                    </button>
                                </div>
                            </div>

                            <div className="flex justify-between sm:gap-3 sm:justify-end pt-4 border-t-2 border-[var(--border-subtle)] mt-6">
                                <button
                                    type="button"
                                    className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 font-semibold transition-all duration-300 text-sm"
                                    onClick={() => {
                                        setShowModuleForm(false);
                                        setEditingModule(null);
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className=" px-5 sm:px-8 py-2 sm:py-2.5 rounded-xl bg-blue-500 text-white font-semibold hover:shadow-xl hover:shadow-cyan-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm"
                                >
                                    {editingModule ? 'Update' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* LESSON FORM MODAL - Enhanced UI with File Upload */}
            {showLessonForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto custom-scrollbar">
                    <div className="card-strong w-full max-w-full sm:max-w-2xl p-4 sm:p-6 relative my-4 rounded-2xl border-2 border-[var(--border-strong)] max-h-[90vh] overflow-y-auto">
                        {/* Close Button */}
                        <button
                            className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all z-10"
                            onClick={() => {
                                setShowLessonForm(false);
                                setSelectedModule(null);
                                setEditingLesson(null);
                            }}
                            aria-label="Close"
                        >
                            <FaTimes />
                        </button>

                        {/* Header */}
                        <div className="flex flex-row items-center gap-4 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)] pr-12">
                            <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                                <FaVideo className="w-7 h-7 sm:w-8 sm:h-8 text-cyan-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1">
                                    {editingLesson ? 'Edit Lesson' : 'Create New Lesson'}
                                </h2>
                                <p className="text-xs sm:text-sm muted line-clamp-2">
                                    {editingLesson
                                        ? 'Update the details of this lesson.'
                                        : 'Add a new lesson to your module.'}
                                </p>
                            </div>
                        </div>

                        {/* Form */}
                        <form onSubmit={handleLessonSubmit} className="space-y-4 sm:space-y-5 mt-2">
                            {/* Lesson Name */}
                            <div className="flex flex-col gap-4">
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">Lesson Name *</label>
                                    <input
                                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-cyan-500/50 text-sm transition-colors"
                                        name="name"
                                        placeholder="Enter lesson Name"
                                        value={lessonFormData.name}
                                        onChange={handleLessonFormChange}
                                        required
                                    />
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">Description</label>
                                    <textarea
                                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-cyan-500/50 text-sm transition-colors resize-none"
                                        name="description"
                                        placeholder="Enter description (HTML/Markdown supported)"
                                        value={lessonFormData.description}
                                        onChange={handleLessonFormChange}
                                        rows={4}
                                    />
                                </div>
                            </div>

                            {/* --- VIDEO FILE UPLOAD SECTION --- */}
                            <div className="p-4 sm:p-5 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                <label className="block text-sm font-bold text-cyan-400 mb-4">
                                    Video Source (Select one)
                                </label>

                                {/* Option A: Video File Upload */}
                                <div className="mb-4">
                                    <label className="text-xs font-semibold block mb-1">
                                        Upload Video File (MP4, OGV, WEBM)
                                    </label>

                                    {(lessonFormData.existing_video_file_url && !lessonFormData.clearVideoFile) ? (
                                        <div className="flex items-center gap-3 bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                                            <div className="bg-green-500/20 p-2 rounded-full">
                                                <FaVideo className="text-green-400 w-4 h-4" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-green-400 truncate">
                                                    Current Video Uploaded
                                                </p>
                                                <a href={lessonFormData.existing_video_file_url} target="_blank" rel="noreferrer" className="text-xs text-green-300/70 hover:underline truncate block">
                                                    View current video
                                                </a>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={handleClearUploadedVideo}
                                                className="text-gray-400 hover:text-red-400 p-2 hover:bg-red-500/10 rounded-lg transition"
                                                title="Remove Video"
                                            >
                                                <FaTimes />
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="file"
                                                id="video-file-upload"
                                                name="video_file"
                                                accept=".mp4,.ogv,.webm"
                                                onChange={handleLessonFormChange}
                                                className="block w-full text-sm text-gray-400
                                                    file:mr-4 file:py-2 file:px-4
                                                    file:rounded-lg file:border-0
                                                    file:text-sm file:font-semibold
                                                    file:bg-cyan-600 file:text-white
                                                    hover:file:bg-cyan-700
                                                    cursor-pointer bg-black/20 rounded-lg border border-[var(--border-color)]"
                                            />
                                            {lessonFormData.newVideoFile && (
                                                <button
                                                    type="button"
                                                    onClick={handleClearUploadedVideo}
                                                    className="p-2 text-gray-400 hover:text-red-400 rounded-lg border border-red-500/30 transition"
                                                    title="Clear selection"
                                                >
                                                    <FaTimes />
                                                </button>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <div className="flex items-center gap-4 my-2">
                                    <div className="h-px bg-[var(--border-subtle)] flex-1"></div>
                                    <span className="text-xs text-gray-500 uppercase font-bold">AND</span>
                                    <div className="h-px bg-[var(--border-subtle)] flex-1"></div>
                                </div>

                                {/* Option B: Video Link */}
                                <div>
                                    <label className="text-xs font-semibold block mb-1">
                                        Video Link (YouTube, Vimeo)
                                    </label>
                                    <div className="relative">
                                        <input
                                            type="text"
                                            name="video_path"
                                            value={lessonFormData.video_path || ''}
                                            onChange={handleLessonFormChange}
                                            className="w-full px-4 py-2 pr-10 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:border-cyan-500/50 text-sm"
                                            placeholder="https://youtube.com/..."
                                        />
                                        {lessonFormData.video_path && (
                                            <button
                                                type="button"
                                                onClick={handleClearVideo}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-400 p-1"
                                            >
                                                <FaTimes />
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {/* Video Preview (Link) */}
                                {lessonFormData.video_path && videoPreview && (
                                    <div className="mt-3 relative rounded-lg overflow-hidden bg-black aspect-video border border-white/10">
                                        {videoPreview.type === 'iframe' ? (
                                            <iframe
                                                src={videoPreview.url}
                                                title="Preview"
                                                className="w-full h-full"
                                                allowFullScreen
                                            />
                                        ) : (
                                            <video src={videoPreview.url} controls className="w-full h-full" />
                                        )}
                                    </div>
                                )}
                            </div>


                            {/* --- FILE ATTACHMENTS SECTION --- */}
                            <div className="p-4 sm:p-5 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                <label className="block text-sm font-bold text-[var(--text-primary)] mb-4">
                                    Attached Files
                                </label>

                                <div className="space-y-4">
                                    {/* Existing Files List */}
                                    {editingLesson && lessonFormData.files && lessonFormData.files.length > 0 && (
                                        <div className="space-y-2">
                                            {lessonFormData.files.map((file) => (
                                                <div key={file.id} className="flex items-center justify-between p-2 rounded bg-black/20 border border-white/5 group">
                                                    <a
                                                        href={file.url}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 truncate"
                                                    >
                                                        <FaFileAlt />
                                                        <span className="truncate max-w-[200px] sm:max-w-xs">{file.name}</span>
                                                        <FaExternalLinkAlt className="w-3 h-3 opacity-50" />
                                                    </a>
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRemoveExistingFile(file.id)}
                                                        className="text-gray-500 hover:text-red-400 p-1.5 transition"
                                                        title="Remove File on Save"
                                                    >
                                                        <FaTrash className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* File Input */}
                                    <div className="relative">
                                        <input
                                            type="file"
                                            id="lesson-files-upload"
                                            name="Lesson_files"
                                            multiple
                                            onChange={handleLessonFormChange}
                                            className="hidden"
                                        />
                                        <label
                                            htmlFor="lesson-files-upload"
                                            className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-gray-600 rounded-lg cursor-pointer hover:border-cyan-500 hover:bg-cyan-500/5 transition-all"
                                        >
                                            <div className="flex flex-col items-center justify-center pt-2 pb-3">
                                                <FaUpload className="w-6 h-6 text-gray-400 mb-2" />
                                                <p className="text-xs text-gray-400">
                                                    <span className="font-semibold text-cyan-400">Click to upload</span> or drag and drop
                                                </p>
                                                <p className="text-[10px] text-gray-500 mt-1">PDF, DOC, ZIP (Multiple allowed)</p>
                                            </div>
                                        </label>
                                    </div>

                                    {/* New Files Preview */}
                                    {lessonFormData.newFiles && lessonFormData.newFiles.length > 0 && (
                                        <div className="mt-2 space-y-1">
                                            <p className="text-xs font-bold text-green-400">Selected for upload:</p>
                                            {Array.from(lessonFormData.newFiles).map((file, idx) => (
                                                <div key={idx} className="flex items-center gap-2 text-xs text-gray-300 pl-2">
                                                    <FaCheckCircle className="text-green-500 w-3 h-3" />
                                                    <span className="truncate">{file.name}</span>
                                                    <span className="text-gray-500">({(file.size / 1024).toFixed(0)}KB)</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Active Toggle */}
                            <div className="p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex-1">
                                        <div className="text-sm sm:text-base font-semibold mb-1">Active Status</div>
                                        <div className="text-xs muted mt-0.5">
                                            Make visible to students
                                        </div>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={handleLessonToggleActive}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${lessonFormData.active ? 'bg-cyan-600' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span
                                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${lessonFormData.active ? 'translate-x-6' : 'translate-x-1'
                                                }`}
                                        />
                                    </button>
                                </div>
                            </div>


                            {/* Action Buttons */}
                            <div className="flex justify-between sm:gap-3 sm:justify-end pt-4 border-t-2 border-[var(--border-subtle)] mt-6">
                                <button
                                    type="button"
                                    className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 font-semibold transition-all duration-300 text-sm"
                                    onClick={() => {
                                        setShowLessonForm(false);
                                        setSelectedModule(null);
                                        setEditingLesson(null);
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-5 sm:px-8 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-500 text-white font-semibold hover:shadow-xl hover:shadow-cyan-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm"
                                >
                                    {editingLesson ? 'Save Changes' : 'Create Lesson'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
            {/* QUIZ FORM MODAL */}
            {showQuizForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto custom-scrollbar">
                    <div className="card-strong w-full max-w-full sm:max-w-2xl p-4 sm:p-6 relative my-4 rounded-2xl border-2 border-[var(--border-strong)] max-h-[90vh] overflow-y-auto">

                        {/* Close Button */}
                        <button
                            className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all z-10"
                            onClick={() => {
                                setShowQuizForm(false);
                                setSelectedModuleQuiz(null);
                                setEditingQuiz(null);
                            }}
                            aria-label="Close"
                        >
                            <FaTimes />
                        </button>

                        {/* Header */}
                        <div className="flex flex-row items-center gap-4 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)] pr-12">
                            <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-green-500/10 flex items-center justify-center border border-green-500/20">
                                <svg className="w-7 h-7 sm:w-8 sm:h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <div className="flex-1 min-w-0">
                                <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1">
                                    {editingQuiz ? 'Edit Quiz' : 'Create New Quiz'}
                                </h2>
                                <p className="text-xs sm:text-sm muted line-clamp-2">
                                    {editingQuiz
                                        ? 'Update quiz settings'
                                        : 'Set up a new quiz for this module.'}
                                </p>
                            </div>
                        </div>

                        <form onSubmit={(e) => {
                            e.preventDefault();
                            if (editingQuiz) {
                                handleUpdateQuiz();
                            } else {
                                handleCreateQuiz();
                            }
                        }} className="space-y-6 mt-2">

                            {/* Quiz Name & Description */}
                            <div className="flex flex-col gap-4">
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">Quiz Name/Title *</label>
                                    <input
                                        type="text"
                                        name="description"
                                        value={quizFormData.description}
                                        onChange={handleQuizFormChange}
                                        required
                                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm transition-colors"
                                        placeholder="Enter quiz Name/Title *"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">Instructions</label>
                                    <textarea
                                        name="instructions"
                                        value={quizFormData.instructions}
                                        onChange={handleQuizFormChange}
                                        rows="3"
                                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm transition-colors resize-none"
                                        placeholder="Enter instructions (e.g. 'No calculators allowed')"
                                    />
                                </div>
                            </div>

                            {/* Settings Grid */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl p-4 sm:p-5">

                                {/* Dates Row */}
                                <div className="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4 pb-2 border-b-2 border-[var(--border-subtle)] mb-2">
                                    <div>
                                        <label className="block text-xs sm:text-sm font-semibold mb-2">
                                            Start Date & Time
                                        </label>
                                        <input
                                            type="datetime-local"
                                            name="start_date_time"
                                            value={quizFormData.start_date_time}
                                            onChange={handleQuizFormChange}
                                            required
                                            className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs sm:text-sm font-semibold mb-2">
                                            End Date & Time
                                        </label>
                                        <input
                                            type="datetime-local"
                                            name="end_date_time"
                                            value={quizFormData.end_date_time}
                                            onChange={handleQuizFormChange}
                                            required
                                            className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Duration (min)
                                    </label>
                                    <input
                                        type="number"
                                        name="duration"
                                        value={quizFormData.duration}
                                        onChange={handleQuizFormChange}
                                        required
                                        min="1"
                                        className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Attempts Allowed
                                    </label>
                                    <div className="relative">
                                        <input
                                            type="number"
                                            name="attempts_allowed"
                                            value={quizFormData.attempts_allowed}
                                            onChange={handleQuizFormChange}
                                            min="-1"
                                            className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                        />
                                        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[15px] font-bold text-[var(--text-muted)] pointer-events-none">
                                            -1 = ∞
                                        </span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Pass %
                                    </label>
                                    <input
                                        type="number"
                                        name="pass_criteria"
                                        value={quizFormData.pass_criteria}
                                        onChange={handleQuizFormChange}
                                        min="0"
                                        max="100"
                                        className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Wait time (hrs)
                                    </label>
                                    <input
                                        type="number"
                                        name="time_between_attempts"
                                        value={quizFormData.time_between_attempts}
                                        onChange={handleQuizFormChange}
                                        min="0"
                                        step="0.5"
                                        className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                    />
                                </div>

                                <div >
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Weightage %
                                    </label>
                                    <input
                                        type="number"
                                        name="weightage"
                                        value={quizFormData.weightage}
                                        onChange={handleQuizFormChange}
                                        min="0"
                                        max="100"
                                        className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Order
                                    </label>
                                    <input
                                        type="number"
                                        name="order"
                                        value={quizFormData.order}
                                        onChange={handleQuizFormChange}
                                        className="w-full px-3 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-green-500/50 text-sm"
                                    />
                                </div>

                            </div>

                            {/* Toggles */}
                            <div className="space-y-3 pt-2">
                                {/* Allow Skip */}
                                <div className="flex items-center justify-between p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex-1">
                                        <span className="text-sm sm:text-base font-semibold text-[var(--text-primary)]">Allow Skipping</span>
                                        <p className="text-xs muted mt-0.5">Students can skip questions and return later</p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleQuizFormChange({ target: { name: 'allow_skip', type: 'checkbox', checked: !quizFormData.allow_skip } })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${quizFormData.allow_skip ? 'bg-yellow-600' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${quizFormData.allow_skip ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>

                                {/* View Answer Paper */}
                                <div className="flex items-center justify-between p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex-1">
                                        <span className="text-sm sm:text-base font-semibold text-[var(--text-primary)]">View Answer Paper</span>
                                        <p className="text-xs muted mt-0.5">Allow students to see correct answers after submission</p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleQuizFormChange({ target: { name: 'view_answerpaper', type: 'checkbox', checked: !quizFormData.view_answerpaper } })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${quizFormData.view_answerpaper ? 'bg-indigo-600' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${quizFormData.view_answerpaper ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>

                                {/* Active Status */}
                                <div className="flex items-center justify-between p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex-1">
                                        <span className="text-sm sm:text-base font-semibold text-[var(--text-primary)]">Active Status</span>
                                        <p className="text-xs muted mt-0.5">Make visible to students immediately</p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleQuizFormChange({ target: { name: 'active', type: 'checkbox', checked: !quizFormData.active } })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${quizFormData.active ? 'bg-green-600' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${quizFormData.active ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            </div>

                            {/* Footer Buttons */}
                            <div className="flex flex-col sm:flex-row gap-3 sm:gap-3 justify-between pt-4 border-t-2 border-[var(--border-subtle)] mt-6">
                                {/* Left side - Try buttons (only show when editing) */}
                                {editingQuiz && (
                                    <div className="flex flex-wrap gap-2">
                                        <button
                                            type="button"
                                            // Fix: Pass editingQuiz?.quiz_id instead of currentQuizId
                                            onClick={() => generateTestSandbox('usermode', editingQuiz?.quiz_id, courseId, navigate)}
                                            disabled={isGenerating}
                                            className="flex-1 sm:flex-none px-4 py-2 rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-500 text-xs sm:text-sm font-semibold hover:bg-cyan-500/20 transition flex items-center justify-center gap-2 disabled:opacity-50"
                                        >
                                            {isGenerating ? (
                                                <span className="w-4 h-4 border-2 border-cyan-500 border-t-cyan-500/20 rounded-full animate-spin"></span>
                                            ) : (
                                                <svg className="w-4 h-4 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                                </svg>
                                            )}
                                            <span>User Mode</span>
                                        </button>

                                        <button
                                            type="button"
                                            // Fix: Pass editingQuiz?.quiz_id here as well
                                            onClick={() => generateTestSandbox('godmode', editingQuiz?.quiz_id, courseId, navigate)}
                                            disabled={isGenerating}
                                            className="flex-1 sm:flex-none px-4 py-2 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-500 text-xs sm:text-sm font-semibold hover:bg-amber-500/20 transition flex items-center justify-center gap-2 disabled:opacity-50"
                                        >
                                            {isGenerating ? (
                                                <span className="w-4 h-4 border-2 border-amber-500 border-t-amber-500/20 rounded-full animate-spin"></span>
                                            ) : (
                                                <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                                </svg>
                                            )}
                                            <span>God Mode</span>
                                        </button>
                                    </div>
                                )}

                                {/* Action Buttons Row */}
                                <div className="flex justify-between sm:gap-3 sm:justify-end flex-wrap flex-1">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowQuizForm(false);
                                            setSelectedModuleQuiz(null);
                                            setEditingQuiz(null);
                                        }}
                                        className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 font-semibold transition-all duration-300 text-sm"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-5 sm:px-8 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-green-600 to-green-500 text-white font-semibold hover:shadow-xl hover:shadow-green-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm"
                                    >
                                        {editingQuiz ? 'Update Quiz' : 'Create Quiz'}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* EXERCISE FORM MODAL - Added Integration */}
            {showExerciseForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto">
                    <div className="card-strong w-full max-w-full sm:max-w-xl p-4 sm:p-6 relative my-4 rounded-2xl border-2 border-[var(--border-strong)] max-h-[90vh] overflow-y-auto">
                        <button
                            className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all z-10"
                            onClick={() => {
                                setShowExerciseForm(false);
                                setEditingExercise(null);
                            }}
                        >
                            <FaTimes />
                        </button>

                        <div className="flex flex-row items-center gap-4 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)] pr-12">
                            <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-purple-500/10 flex items-center justify-center border-2 border-purple-500/30 text-purple-400">
                                <FaPuzzlePiece className="w-7 h-7 sm:w-8 sm:h-8" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <h2 className="text-xl sm:text-2xl font-bold mb-1">
                                    {editingExercise ? 'Edit Exercise' : 'Add Exercise'}
                                </h2>
                                <p className="text-xs sm:text-sm muted line-clamp-2">Set up a simple coding exercise/quiz.</p>
                            </div>
                        </div>

                        <form onSubmit={handleExerciseSubmit} className="space-y-4 sm:space-y-5 mt-2">
                            <div className="flex flex-col gap-4">
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">Description</label>
                                    <input
                                        className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-purple-500/50 text-sm transition-colors"
                                        name="Enter description"
                                        placeholder="e.g. NFT Marketplace"
                                        value={exerciseFormData.description}
                                        onChange={handleExerciseFormChange}
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-3 pt-2">
                                <div className="flex items-center justify-between p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex-1">
                                        <span className="text-sm sm:text-base font-semibold text-[var(--text-primary)]">Allow student to view their answer paper</span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleExerciseFormChange({ target: { name: 'view_answerpaper', type: 'checkbox', checked: !exerciseFormData.view_answerpaper } })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${exerciseFormData.view_answerpaper ? 'bg-purple-600' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${exerciseFormData.view_answerpaper ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>

                                <div className="flex items-center justify-between p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex-1">
                                        <span className="text-sm sm:text-base font-semibold text-[var(--text-primary)]">Active Status</span>
                                        <p className="text-xs muted mt-0.5">Make visible to students immediately</p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleExerciseFormChange({ target: { name: 'active', type: 'checkbox', checked: !exerciseFormData.active } })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${exerciseFormData.active ? 'bg-green-600' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${exerciseFormData.active ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            </div>

                            <div className="flex flex-col sm:flex-row gap-3 sm:gap-3 justify-between pt-4 border-t-2 border-[var(--border-subtle)] mt-6">
                                {editingExercise && (
                                    <div className="flex flex-wrap gap-2">
                                        <button
                                            type="button"
                                            // Fix: Pass editingQuiz?.quiz_id instead of currentQuizId
                                            onClick={() => generateTestSandbox('usermode', editingExercise?.quiz_id, courseId, navigate)}
                                            disabled={isGenerating}
                                            className="flex-1 sm:flex-none px-4 py-2 rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-500 text-xs sm:text-sm font-semibold hover:bg-cyan-500/20 transition flex items-center justify-center gap-2 disabled:opacity-50"
                                        >
                                            {isGenerating ? (
                                                <span className="w-4 h-4 border-2 border-cyan-500 border-t-cyan-500/20 rounded-full animate-spin"></span>
                                            ) : (
                                                <svg className="w-4 h-4 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                                </svg>
                                            )}
                                            <span>User Mode</span>
                                        </button>

                                        <button
                                            type="button"
                                            // Fix: Pass editingQuiz?.quiz_id here as well
                                            onClick={() => generateTestSandbox('godmode', editingExercise?.quiz_id, courseId, navigate)}
                                            disabled={isGenerating}
                                            className="flex-1 sm:flex-none px-4 py-2 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-500 text-xs sm:text-sm font-semibold hover:bg-amber-500/20 transition flex items-center justify-center gap-2 disabled:opacity-50"
                                        >
                                            {isGenerating ? (
                                                <span className="w-4 h-4 border-2 border-amber-500 border-t-amber-500/20 rounded-full animate-spin"></span>
                                            ) : (
                                                <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                                </svg>
                                            )}
                                            <span>God Mode</span>
                                        </button>
                                    </div>
                                )}
                                <div className="flex justify-between sm:gap-3 sm:justify-end flex-wrap flex-1">
                                    <button
                                        type="button"
                                        className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 font-semibold transition-all duration-300 text-sm"
                                        onClick={() => setShowExerciseForm(false)}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        className="px-5 sm:px-8 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-purple-500 text-white font-semibold hover:shadow-xl hover:shadow-purple-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm"
                                    >
                                        {editingExercise ? 'Update' : 'Save'}
                                    </button>
                                </div>
                            </div>


                        </form>
                    </div>
                </div>
            )}

            {/* DESIGN MODULE MODAL */}
            {showDesignModuleModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto">
                    <div className="card-strong w-full max-w-6xl h-[85vh] flex flex-col relative rounded-2xl shadow-2xl overflow-hidden border-2 border-[var(--border-strong)]">
                        {/* Styled consistent absolute cross button */}
                        <button
                            className="absolute right-4 top-4 z-10 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all"
                            onClick={closeDesignModule}
                            aria-label="Close"
                        >
                            <FaTimes />
                        </button>

                        {/* Standardized Header */}
                        <div className="flex flex-row items-center gap-4 p-4 sm:p-6 border-b-2 border-[var(--border-subtle)] bg-[var(--bg-primary)] pr-12">
                            <div className="w-12 h-12 flex-shrink-0 sm:w-14 sm:h-14 rounded-xl bg-amber-500/10 flex items-center justify-center border-2 border-amber-500/30 text-amber-500">
                                <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" /></svg>
                            </div>
                            <div className="flex-1 min-w-0">
                                <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1 text-[var(--text-primary)]">Design Module Content</h2>
                                <p className="text-xs sm:text-sm text-[var(--text-muted)] line-clamp-2">Add, remove, and reorder lessons and quizzes</p>
                            </div>
                        </div>

                        {/* Modal Body */}
                        <div className="flex-1 overflow-hidden p-4 sm:p-6 bg-[var(--bg-primary)]">

                            {loadingDesignModule && !designModule ? (
                                <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-3">
                                    <FaSync className="animate-spin text-3xl text-amber-500" />
                                    <span>Loading module configuration...</span>
                                </div>
                            ) : designModuleError ? (
                                <div className="h-full flex items-center justify-center text-red-400">
                                    <p>{designModuleError}</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">

                                    {/* Left Column: SELECTED UNITS (In Module) */}
                                    <div className="flex flex-col h-full bg-[var(--surface-2)] rounded-xl border-2 border-[var(--border-strong)] overflow-hidden shadow-inner">
                                        <div className="p-3 sm:p-4 border-b-2 border-[var(--border-subtle)] bg-[var(--input-bg)]">
                                            <h3 className="font-bold text-sm sm:text-base md:text-lg text-[var(--text-primary)] flex items-center gap-2">
                                                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-blue-500"></span>
                                                Included Content
                                            </h3>
                                            <p className="text-[10px] sm:text-xs text-[var(--text-muted)] mt-0.5">Items currently in this module</p>
                                        </div>

                                        <div className="flex-1 overflow-y-auto p-2 sm:p-3 space-y-2 custom-scrollbar">
                                            {localSelected.length > 0 ? (
                                                localSelected.map((unit) => {
                                                    const isSelected = selectedInSelected === unit.id;
                                                    return (
                                                        <div key={unit.id} className="group">
                                                            <div
                                                                onClick={() => setSelectedInSelected(isSelected ? null : unit.id)}
                                                                className={`flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg cursor-pointer transition active:scale-95 ${isSelected
                                                                    ? 'bg-blue-600/20 border-2 border-blue-600'
                                                                    : 'bg-[var(--surface)] border border-[var(--border-color)] hover:shadow-md hover:bg-[var(--surface-2)] hover:border-blue-400'
                                                                    }`}
                                                            >
                                                                <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${unit.type === 'lesson' ? ('bg-cyan-500/10 text-cyan-400') : unit.is_exercise ? ('bg-purple-500/10 text-purple-400') : ('bg-green-500/10 text-green-400')
                                                                    }`}>

                                                                    {unit.type === 'lesson' ? (
                                                                        <FaVideo className="w-3.5 h-3.5" />
                                                                    ) : unit.is_exercise ? (
                                                                        <FaPuzzlePiece className="w-3.5 h-3.5" />
                                                                    ) : (
                                                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                        </svg>
                                                                    )}
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <div className="font-medium text-sm text-[var(--text-primary)] truncate">{unit.display_name.replace(/\(quiz\)|\(lesson\)/gi, '')}</div>
                                                                    <div className="flex items-center gap-2 mt-0.5">
                                                                        <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] bg-[var(--input-bg)] border border-[var(--border-strong)] px-1.5 py-0.5 rounded">{unit.type === 'lesson' ? (
                                                                            'LESSON'
                                                                        ) : unit.is_exercise ? (
                                                                            'EXERCISE'
                                                                        ) : (
                                                                            'QUIZ'
                                                                        )}</span>
                                                                        {unit.check_prerequisite && <span className="text-[10px] text-purple-500 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/30">Prerequisite</span>}
                                                                    </div>
                                                                </div>
                                                                <input
                                                                    type="radio"
                                                                    checked={isSelected}
                                                                    readOnly
                                                                    className="w-4 h-4 text-blue-500 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] focus:ring-blue-500 focus:ring-offset-[var(--bg-primary)] accent-blue-500"
                                                                />
                                                            </div>

                                                            {/* Context Actions (only visible when selected) */}
                                                            <div className={`transition-all duration-300 overflow-hidden ${isSelected ? 'max-h-20 opacity-100 py-2' : 'max-h-0 opacity-0'}`}>
                                                                <div className="mx-2 p-3 bg-[var(--bg-primary)] rounded-xl flex items-center justify-between border-2 border-[var(--border-subtle)]">
                                                                    <label className="flex items-center gap-2 cursor-pointer select-none">
                                                                        <input
                                                                            type="checkbox"
                                                                            checked={unit.check_prerequisite}
                                                                            onChange={() => handleTogglePrereq(unit.id)}
                                                                            className="rounded border-2 border-[var(--border-strong)] bg-[var(--input-bg)] focus:ring-purple-500 focus:ring-offset-[var(--bg-primary)] accent-purple-500 w-4 h-4"
                                                                        />
                                                                        <span className="text-xs text-[var(--text-primary)] font-semibold">Check Prerequisite</span>
                                                                    </label>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                })
                                            ) : (
                                                <div className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] opacity-50">
                                                    <FaBookOpen className="w-8 h-8 mb-2" />
                                                    <p className="text-sm">Module is empty</p>
                                                </div>
                                            )}
                                        </div>

                                        {/* Left Actions Footer */}
                                        <div className="p-4 border-t-2 border-[var(--border-subtle)] bg-[var(--surface-2)] flex items-center justify-between gap-2">
                                            <button
                                                onClick={handleRemoveUnit}
                                                disabled={!selectedInSelected}
                                                className="px-2 sm:px-3 md:px-4 py-2 sm:py-2.5 border-2 border-red-500/50 hover:bg-red-500/10 text-red-500 rounded-xl text-xs sm:text-sm font-bold transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex-shrink-0"
                                            >
                                                <FaTrash className="inline mr-1" /> Remove
                                            </button>
                                            <div className="flex gap-1.5 sm:gap-2">
                                                <button
                                                    onClick={moveUp}
                                                    disabled={!selectedInSelected}
                                                    className="px-2 sm:px-3 md:px-4 py-2 sm:py-2.5 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-xl text-xs sm:text-sm font-bold hover:bg-[var(--surface-2)] transition flex items-center justify-center gap-1 sm:gap-1.5 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
                                                >
                                                    <FaArrowUp className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                                                    <span className="hidden md:inline">Up</span>
                                                </button>
                                                <button
                                                    onClick={moveDown}
                                                    disabled={!selectedInSelected}
                                                    className="px-2 sm:px-3 md:px-4 py-2 sm:py-2.5 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-xl text-xs sm:text-sm font-bold hover:bg-[var(--surface-2)] transition flex items-center justify-center gap-1 sm:gap-1.5 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
                                                >
                                                    <FaArrowDown className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                                                    <span className="hidden md:inline">Down</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Right Column: AVAILABLE POOL */}
                                    <div className="flex flex-col h-full bg-[var(--surface-2)] rounded-xl border-2 border-[var(--border-strong)] overflow-hidden shadow-inner">
                                        <div className="p-3 sm:p-4 border-b-2 border-[var(--border-subtle)] bg-[var(--input-bg)]">
                                            <h3 className="font-bold text-sm sm:text-base md:text-lg text-[var(--text-primary)] flex items-center gap-2">
                                                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-green-500"></span>
                                                Available Items
                                            </h3>
                                            <p className="text-[10px] sm:text-xs text-[var(--text-muted)] mt-0.5">Unassigned lessons and quizzes</p>
                                        </div>

                                        <div className="flex-1 overflow-y-auto p-2 sm:p-3 space-y-2 custom-scrollbar">
                                            {localPool.length > 0 ? (
                                                localPool.map((item) => {
                                                    const isSelected = selectedInPool === item.value_key;
                                                    return (
                                                        <div
                                                            key={item.value_key}
                                                            onClick={() => setSelectedInPool(isSelected ? null : item.value_key)}
                                                            className={`flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg cursor-pointer transition active:scale-95 ${isSelected
                                                                ? 'bg-green-600/20 border-2 border-green-600'
                                                                : 'bg-[var(--surface)] border border-[var(--border-color)] hover:shadow-md hover:bg-white/[0.03] hover:border-green-400'
                                                                }`}
                                                        >
                                                            <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 ${item.type === 'lesson' ? ('bg-cyan-500/10 text-cyan-400') : item.is_exercise ? ('bg-purple-500/10 text-purple-400') : ('bg-green-500/10 text-green-400')
                                                                }`}>

                                                                {item.type === 'lesson' ? (
                                                                    <FaVideo className="w-3.5 h-3.5" />
                                                                ) : item.is_exercise ? (
                                                                    <FaPuzzlePiece className="w-3.5 h-3.5" />
                                                                ) : (
                                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                    </svg>
                                                                )}
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <div className="font-medium text-xs sm:text-sm text-[var(--text-primary)] truncate">{item.display_name.replace(/\(quiz\)|\(lesson\)/gi, '')}</div>
                                                                <div className="flex items-center gap-2 mt-0.5">
                                                                    <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] bg-[var(--input-bg)] border border-[var(--border-strong)] px-1.5 py-0.5 rounded">{item.type === 'lesson' ? (
                                                                        'LESSON'
                                                                    ) : item.is_exercise ? (
                                                                        'EXERCISE'
                                                                    ) : (
                                                                        'QUIZ'
                                                                    )}</span>
                                                                </div>
                                                            </div>
                                                            <input
                                                                type="radio"
                                                                checked={isSelected}
                                                                readOnly
                                                                className="w-4 h-4 text-green-500 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] focus:ring-green-500 focus:ring-offset-[var(--bg-primary)] accent-green-500 flex-shrink-0"
                                                            />
                                                        </div>
                                                    );
                                                })
                                            ) : (
                                                <div className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] opacity-50 py-8 sm:py-12">
                                                    <FaCheckCircle className="w-6 h-6 sm:w-8 sm:h-8 mb-2" />
                                                    <p className="text-xs sm:text-sm">No available items</p>
                                                    <p className="text-[10px] sm:text-xs muted mt-1">All items are assigned</p>
                                                </div>
                                            )}
                                        </div>

                                        {/* Right Actions Footer */}
                                        <div className="flex items-center justify-between p-4 border-t-2 border-[var(--border-subtle)] bg-[var(--surface-2)]">
                                            <button
                                                onClick={handleAddUnit}
                                                disabled={!selectedInPool}
                                                className="px-2 sm:px-3 md:px-4 py-2 sm:py-2.5 bg-gradient-to-r from-green-600 to-green-500 rounded-xl text-white text-xs sm:text-sm font-bold shadow-lg shadow-green-500/20 hover:from-green-700 hover:to-green-600 transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex-shrink-0"
                                            >
                                                <FaPlus className="inline mr-1" /> Add
                                            </button>
                                        </div>
                                    </div>

                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}



            {/* DESIGN QUESTION PAPER MODAL */}
            {showDesignQuestionPaperModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto">
                    <div className="card-strong w-full max-w-full sm:max-w-6xl h-[95vh] flex flex-col relative rounded-2xl shadow-2xl overflow-hidden border-2 border-[var(--border-strong)]">

                        {/* Styled consistent absolute cross button */}
                        <button
                            className="absolute right-4 top-4 z-10 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all"
                            onClick={closeDesignQuestionPaper}
                        >
                            <FaTimes />
                        </button>

                        {/* Standardized Header */}
                        <div className="flex flex-row items-center gap-4 p-4 sm:p-6  bg-[var(--bg-primary)] pr-12">
                            <div className="w-12 h-12 flex-shrink-0 sm:w-14 sm:h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border-2 border-blue-500/30 text-blue-400">
                                <FaQuestionCircle className="w-7 h-7 sm:w-8 sm:h-8" />
                            </div>
                            <div className="flex-1 min-w-0 pr-12">
                                <h2 className="text-xl sm:text-2xl font-bold mb-1 truncate text-[var(--text-primary)]">
                                    Design: {designingQuizName || "Question Paper"}
                                </h2>
                                <p className="text-xs sm:text-sm text-[var(--text-muted)]">
                                    Total Built Marks: <span className="font-bold text-amber-500">{questionPaperDesign?.question_paper?.total_marks || 0}</span>
                                </p>
                            </div>
                        </div>

                        {/* Tab Bar + Save Settings button on same row */}
                        <div className="flex items-center justify-between px-4 sm:px-6 pt-4 sm:pt-6 bg-[var(--bg-primary)] border-b-2 border-[var(--border-subtle)] pb-2">
                            <div className="flex items-center gap-1">
                                {[
                                    { id: 'FIXED', label: 'Fixed Questions', icon: <FaCheck className="w-3.5 h-3.5" /> },
                                    { id: 'RANDOM', label: 'Random Sets', icon: <FaRandom className="w-3.5 h-3.5" /> },
                                ].map(tab => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setQPaperTab(tab.id)}
                                        className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl transition-all ${qPaperTab === tab.id
                                            ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-xl shadow-blue-600/30 hover:shadow-2xl hover:shadow-blue-600/40 border-transparent scale-101'
                                            : 'card-strong border-[var(--border-strong)] text-[var(--text-secondary)] hover:border-blue-500/40 hover:bg-blue-500/5 hover:text-blue-400 hover:shadow-md'
                                            }`}
                                    >
                                        {tab.icon}
                                        <span className="hidden sm:inline">{tab.label}</span>
                                    </button>
                                ))}
                            </div>
                            {/* Save settings button — always visible, right aligned in tab row */}
                            <form onSubmit={handleSaveQPaperSettings} className="flex items-center pb-2">
                                <button
                                    type="submit"
                                    disabled={loadingQuestionPaper}
                                    className="px-6 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold hover:shadow-xl hover:shadow-blue-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm flex items-center justify-center min-w-[100px]"
                                >
                                    Save
                                </button>
                            </form>
                        </div>

                        {/* Shuffle Toggles — always visible below tab bar, above body */}



                        {/* Modal Body */}
                        <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6 bg-[var(--bg-primary)]">
                            {loadingQuestionPaper && !questionPaperDesign ? (
                                <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-3">
                                    <FaSync className="animate-spin text-3xl text-amber-500" />
                                    <span>Loading paper design...</span>
                                </div>
                            ) : questionPaperError ? (
                                <div className="h-full flex items-center justify-center text-red-400">
                                    <p>{questionPaperError}</p>
                                </div>
                            ) : (
                                <>
                                    {/* FIXED / RANDOM TABS: Two-column layout */}
                                    {(qPaperTab === 'FIXED' || qPaperTab === 'RANDOM') && (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">

                                            {/* LEFT: Added questions / Configured sets */}
                                            <div className="flex flex-col h-full bg-[var(--surface-2)] rounded-xl border-2 border-[var(--border-strong)] overflow-hidden shadow-inner">
                                                <div className="p-3 sm:p-4 border-b-2 border-[var(--border-subtle)] bg-[var(--input-bg)]">
                                                    <h3 className="font-bold text-sm sm:text-base md:text-lg text-[var(--text-primary)] flex items-center gap-2">
                                                        <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${qPaperTab === 'FIXED' ? 'bg-blue-500' : 'bg-purple-500'}`}></span>
                                                        {qPaperTab === 'FIXED' ? 'Fixed Questions' : 'Random Sets'}
                                                    </h3>
                                                    <p className="text-[10px] sm:text-xs text-[var(--text-muted)] mt-0.5">
                                                        {qPaperTab === 'FIXED' ? 'Questions always included in this paper' : 'Sets where N questions are picked randomly'}
                                                    </p>
                                                </div>
                                                <div className="flex-1 overflow-y-auto p-2 sm:p-3 space-y-2 custom-scrollbar">

                                                    {/* FIXED list */}
                                                    {qPaperTab === 'FIXED' && (
                                                        questionPaperDesign?.fixed_questions?.length > 0 ? (
                                                            questionPaperDesign.fixed_questions.map(q => (
                                                                <div
                                                                    key={q.id}
                                                                    onClick={() => toggleQPaperSelection(q.id, selectedFixedQs, setSelectedFixedQs)}
                                                                    className={`flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg cursor-pointer transition active:scale-95 ${selectedFixedQs.includes(q.id)
                                                                        ? 'bg-blue-600/20 border-2 border-blue-600'
                                                                        : 'bg-[var(--surface)] border border-[var(--border-color)] hover:shadow-md hover:bg-[var(--surface-2)] hover:border-blue-400'
                                                                        }`}
                                                                >
                                                                    <div className="w-8 h-8 rounded flex items-center justify-center flex-shrink-0 bg-blue-500/10 text-blue-400">
                                                                        <FaCheck className="w-3.5 h-3.5" />
                                                                    </div>
                                                                    <div className="flex-1 min-w-0">
                                                                        <div className="font-medium text-sm text-[var(--text-primary)] truncate">{q.summary || 'Untitled Question'}</div>
                                                                        <div className="flex items-center gap-2 mt-0.5">
                                                                            <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] bg-[var(--input-bg)] border border-[var(--border-strong)] px-1.5 py-0.5 rounded">{q.type}</span>
                                                                            <span className="text-[10px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">{q.points} pts</span>
                                                                        </div>
                                                                    </div>
                                                                    <input type="radio"
                                                                        readOnly
                                                                        checked={selectedFixedQs.includes(q.id)}
                                                                        className="w-4 h-4 text-blue-500 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] focus:ring-blue-500 focus:ring-offset-[var(--bg-primary)] accent-blue-500" />
                                                                </div>
                                                            ))
                                                        ) : (
                                                            <div className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] opacity-50 py-8">
                                                                <FaCheck className="w-8 h-8 mb-2" />
                                                                <p className="text-sm">No fixed questions yet</p>
                                                                <p className="text-xs mt-1">Search and add from the right panel</p>
                                                            </div>
                                                        )
                                                    )}

                                                    {/* RANDOM list */}
                                                    {qPaperTab === 'RANDOM' && (
                                                        questionPaperDesign?.random_sets?.length > 0 ? (
                                                            questionPaperDesign.random_sets.map(set => (
                                                                <div
                                                                    key={set.id}
                                                                    onClick={() => toggleQPaperSelection(set.id, selectedRandomSets, setSelectedRandomSets)}
                                                                    className={`flex flex-col gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg cursor-pointer transition active:scale-95 ${selectedRandomSets.includes(set.id)
                                                                        ? 'bg-blue-600/20 border-2 border-blue-600'
                                                                        : 'bg-[var(--surface)] border border-[var(--border-color)] hover:shadow-md hover:bg-[var(--surface-2)] hover:border-blue-400'
                                                                        }`}
                                                                >
                                                                    {/* Header Row */}
                                                                    <div className="flex items-center gap-3 w-full">
                                                                        <div className="w-8 h-8 rounded flex items-center justify-center flex-shrink-0 bg-purple-500/10 text-purple-400">
                                                                            <FaRandom className="w-3.5 h-3.5" />
                                                                        </div>
                                                                        <div className="flex-1 min-w-0">
                                                                            <div className="font-medium text-sm text-[var(--text-primary)]">
                                                                                Pick <span className="text-amber-400 font-bold">{set.num_questions}</span> from <span className="text-cyan-400 font-bold">{set.questions?.length || 0}</span> questions
                                                                            </div>
                                                                            <div className="flex items-center gap-2 mt-0.5">

                                                                                <span className="text-[10px] text-[var(--text-muted)]">Set #{set.id}</span>
                                                                            </div>
                                                                        </div>

                                                                        {/* Expand/Collapse Dropdown Trigger */}
                                                                        <button
                                                                            onClick={(e) => {
                                                                                e.stopPropagation(); // Prevents checking the box when opening the dropdown
                                                                                setExpandedRandomSets(prev =>
                                                                                    prev.includes(set.id) ? prev.filter(id => id !== set.id) : [...prev, set.id]
                                                                                );
                                                                            }}
                                                                            className="p-1.5 hover:bg-[var(--surface-2)] rounded ml-1 text-[var(--text-muted)] transition"
                                                                            title="View Questions"
                                                                        >
                                                                            <svg className={`w-4 h-4 transition-transform ${expandedRandomSets.includes(set.id) ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                                                        </button>

                                                                        <input type="radio"
                                                                            readOnly
                                                                            checked={selectedRandomSets.includes(set.id)}
                                                                            className="w-4 h-4 text-blue-500 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] focus:ring-blue-500 focus:ring-offset-[var(--bg-primary)] accent-blue-500" />
                                                                    </div>

                                                                    {/* Inner Questions List (Revealed cleanly when expanded) */}
                                                                    {expandedRandomSets.includes(set.id) && set.questions?.length > 0 && (
                                                                        <div
                                                                            className="mt-1 pt-2 border-t border-[var(--border-subtle)] space-y-2 max-h-48 overflow-y-auto custom-scrollbar"
                                                                            onClick={(e) => e.stopPropagation()} // Stop propagation here too so clicking text doesn't check the set
                                                                        >
                                                                            {set.questions.map((q, idx) => (
                                                                                <div key={q.id || idx} className="flex gap-2 items-start text-xs text-[var(--text-muted)] bg-[var(--surface-2)] hover:bg-[var(--surface)] p-2 rounded-xl border-2 border-[var(--border-strong)]">
                                                                                    <span className="text-[var(--text-muted)] font-mono mt-0.5">{idx + 1}.</span>
                                                                                    <div className="flex-1">
                                                                                        <div
                                                                                            className="line-clamp-2 mb-1.5 text-[var(--text-primary)]"
                                                                                            dangerouslySetInnerHTML={{ __html: q.summary || q.description || `Question ID: ${q.id}` }}
                                                                                        />
                                                                                        {/* Sub-tags showing individual marks underneath each list item */}
                                                                                        <div className="flex items-center gap-2">
                                                                                            <span className="text-[9px] uppercase font-bold text-[var(--text-muted)] bg-[var(--input-bg)] border border-[var(--border-strong)] px-1 py-0.5 rounded">{q.type || 'Question'}</span>
                                                                                            <span className="text-[9px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-1 py-0.5 rounded">{q.points} pts</span>
                                                                                        </div>
                                                                                    </div>
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            ))
                                                        ) : (
                                                            <div className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] opacity-50 py-8">
                                                                <FaRandom className="w-8 h-8 mb-2" />
                                                                <p className="text-sm">No random sets yet</p>
                                                                <p className="text-xs mt-1">Search and build sets from the right panel</p>
                                                            </div>
                                                        )
                                                    )}
                                                </div>

                                                {/* Left Footer: Remove button */}

                                                <div className="p-4 border-t-2 border-[var(--border-subtle)] bg-[var(--surface-2)] flex items-center justify-between gap-2">
                                                    <button
                                                        onClick={qPaperTab === 'FIXED' ? handleRemoveFixed : handleRemoveRandomSets}
                                                        disabled={qPaperTab === 'FIXED' ? (!selectedFixedQs.length || loadingQuestionPaper) : (!selectedRandomSets.length || loadingQuestionPaper)}
                                                        className="px-2 sm:px-3 md:px-4 py-2 sm:py-2.5 border-2 border-red-500/50 hover:bg-red-500/10 text-red-500 rounded-xl text-xs sm:text-sm font-bold transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex-shrink-0"
                                                    >
                                                        <FaTrash className="w-3 h-3 inline mr-1" />
                                                        Remove ({qPaperTab === 'FIXED' ? selectedFixedQs.length : selectedRandomSets.length})
                                                    </button>
                                                </div>
                                            </div>

                                            {/* RIGHT: Search + Results */}
                                            <div className="flex flex-col h-full bg-[var(--input-bg)] rounded-xl border-2 border-[var(--border-strong)] overflow-hidden shadow-inner">
                                                <div className="p-3 sm:p-4  bg-[var(--input-bg)]">
                                                    <h3 className="font-bold text-sm sm:text-base md:text-lg text-[var(--text-primary)] flex items-center gap-2">
                                                        <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-green-500"></span>
                                                        Question Bank
                                                    </h3>
                                                    <p className="text-[10px] sm:text-xs text-[var(--text-muted)] mt-0.5">Filter and select questions to add</p>
                                                </div>

                                                {/* Filter controls */}
                                                <div className="px-3 sm:px-4 pb-3 sm:pb-4 border-b-2 border-[var(--border-subtle)] bg-[var(--input-bg)] flex items-center gap-2">
                                                    <input
                                                        type="number"
                                                        placeholder="Marks"
                                                        value={filterMarks}
                                                        onChange={e => setFilterMarks(e.target.value)}
                                                        className="w-20 bg-[var(--surface-2)] border-2 border-[var(--border-strong)] rounded-xl px-2 py-1.5 text-xs text-[var(--text-primary)] focus:outline-none focus:border-blue-500/50 transition-colors"
                                                    />
                                                    <select
                                                        value={filterType}
                                                        onChange={e => setFilterType(e.target.value)}
                                                        className="flex-1 bg-[var(--surface-2)] border-2 border-[var(--border-strong)] rounded-xl px-2 py-1.5 text-xs text-[var(--text-primary)] focus:outline-none focus:border-blue-500/50 transition-colors"
                                                    >
                                                        <option value="">----------</option>
                                                        <option value="mcq">Single Correct Choice</option>
                                                        <option value="mcc">Multiple Correct Choices</option>
                                                        <option value="code">Code</option>
                                                        <option value="assignment_upload">Assignment Upload</option>
                                                        <option value="integer">Answer in Integer</option>
                                                        <option value="string">Answer in String</option>
                                                        <option value="float">Answer in Float</option>
                                                        <option value="arrange">Arrange in Order</option>
                                                    </select>

                                                    <button
                                                        onClick={handleSearchQPaper}
                                                        disabled={loadingQuestionPaper}
                                                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl text-xs font-bold transition active:scale-95 disabled:opacity-50 flex items-center gap-1.5 flex-shrink-0 text-[var(--text-primary)]"
                                                    >
                                                        {loadingQuestionPaper ? <FaSync className="animate-spin w-3 h-3 text-[var(--text-muted)]" /> : <FaSearch className="w-3 h-3 " />}
                                                        Find
                                                    </button>
                                                </div>

                                                {/* Results */}
                                                <div className="flex-1 overflow-y-auto p-2 sm:p-3 space-y-2 custom-scrollbar items-center justify-between p-4 bg-[var(--surface-2)]">
                                                    {availableQuestions.length > 0 ? (
                                                        availableQuestions.map(q => (
                                                            <div
                                                                key={q.id}
                                                                onClick={() => toggleQPaperSelection(q.id, selectedPoolQs, setSelectedPoolQs)}
                                                                className={`flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 rounded-lg cursor-pointer transition active:scale-95 ${selectedPoolQs.includes(q.id)
                                                                    ? 'bg-green-600/20 border-2 border-green-600'
                                                                    : 'bg-[var(--surface)] border border-[var(--border-color)] hover:shadow-md hover:bg-white/[0.03] hover:border-green-400'
                                                                    }`}
                                                            >
                                                                <div className="w-8 h-8 rounded flex items-center justify-center flex-shrink-0 bg-green-500/10 text-green-400">
                                                                    <FaQuestionCircle className="w-3.5 h-3.5" />
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <div className="font-medium text-xs sm:text-sm text-[var(--text-primary)] truncate">{q.summary || 'Untitled Question'}</div>
                                                                    <div className="flex items-center gap-2 mt-0.5">
                                                                        <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] bg-[var(--input-bg)] border border-[var(--border-strong)] px-1.5 py-0.5 rounded">{q.type}</span>
                                                                        <span className="text-[10px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">{q.points} pts</span>
                                                                    </div>
                                                                </div>
                                                                <input type="radio" readOnly checked={selectedPoolQs.includes(q.id)} className="w-4 h-4 text-green-500 rounded border-2 border-[var(--border-strong)] bg-[var(--input-bg)] focus:ring-green-500 focus:ring-offset-[var(--bg-primary)] accent-green-500 flex-shrink-0" />
                                                            </div>
                                                        ))
                                                    ) : (
                                                        <div className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] opacity-50 py-8 sm:py-12">
                                                            <FaSearch className="w-6 h-6 sm:w-8 sm:h-8 mb-2" />
                                                            <p className="text-xs sm:text-sm">No results yet</p>
                                                            <p className="text-[10px] sm:text-xs mt-1">Use filters above and click Find</p>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Right Footer: Add button(s) */}




                                                <div className="flex items-center justify-between p-4 border-t-2 border-[var(--border-subtle)] bg-[var(--surface-2)]">
                                                    {qPaperTab === 'FIXED' && (

                                                        <button
                                                            onClick={handleAddFixed}
                                                            disabled={!selectedPoolQs.length || loadingQuestionPaper}
                                                            className="px-2 sm:px-3 md:px-4 py-2 sm:py-2.5 bg-gradient-to-r from-green-600 to-green-500 rounded-xl text-white text-xs sm:text-sm font-bold shadow-lg shadow-green-500/20 hover:from-green-700 hover:to-green-600 transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex-shrink-0"
                                                        >
                                                            <FaPlus className="w-3 h-3 inline mr-1" />
                                                            Add {selectedPoolQs.length > 0 ? selectedPoolQs.length : ''} to Fixed
                                                        </button>
                                                    )}

                                                    {qPaperTab === 'RANDOM' && (
                                                        <div className="w-full flex items-center justify-between ">
                                                            <button
                                                                onClick={handleAddRandomSet}
                                                                disabled={!selectedPoolQs.length || loadingQuestionPaper || !randomSetCount}
                                                                className="px-2 sm:px-3 md:px-4 py-2 sm:py-2.5 bg-gradient-to-r from-green-600 to-green-500 rounded-xl text-white text-xs sm:text-sm font-bold shadow-lg shadow-green-500/20 hover:from-green-700 hover:to-green-600 transition active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 flex-shrink-0"
                                                            >
                                                                <FaRandom className="w-3 h-3 inline mr-1" />
                                                                Pick {randomSetCount || 'N'} from {selectedPoolQs.length > 0 ? selectedPoolQs.length : '0'}
                                                            </button>
                                                            <input
                                                                type="number"
                                                                placeholder="Pick N"
                                                                title="Number of random questions to pick from selected"
                                                                value={randomSetCount}
                                                                onChange={e => setRandomSetCount(e.target.value)}
                                                                className="w-24 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl px-3 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:border-blue-500/50 transition-colors flex-shrink-0 text-center"
                                                                min="1"
                                                                max={selectedPoolQs.length || 1}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        {/* Shuffle Toggles — always visible below tab bar, above body */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 px-4 sm:px-6 py-4 bg-[var(--input-bg)] border-t-2 border-[var(--border-subtle)] mt-auto">
                            <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-primary)] border-2 border-[var(--border-strong)]">
                                <div className="flex-1 pr-3">
                                    <span className="text-sm font-semibold text-[var(--text-primary)]">Shuffle Questions</span>
                                    <p className="text-xs muted mt-0.5">Randomize question order for each attempt</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setShuffleQuestions(prev => !prev)}
                                    className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${shuffleQuestions ? 'bg-purple-600' : 'bg-[var(--border-strong)]'
                                        }`}
                                >
                                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${shuffleQuestions ? 'translate-x-6' : 'translate-x-1'}`} />
                                </button>
                            </div>
                            <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-primary)] border-2 border-[var(--border-strong)]">
                                <div className="flex-1 pr-3">
                                    <span className="text-sm font-semibold text-[var(--text-primary)]">Shuffle Test Cases</span>
                                    <p className="text-xs muted mt-0.5">Randomize test case order for coding questions</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setShuffleTestcases(prev => !prev)}
                                    className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${shuffleTestcases ? 'bg-yellow-600' : 'bg-[var(--border-strong)]'
                                        }`}
                                >
                                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${shuffleTestcases ? 'translate-x-6' : 'translate-x-1'}`} />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* MODULES LIST */}
            {modules.length > 0 ? (
                <div className="space-y-5">
                    {modules.map((module) => {
                        const isExpanded = expandedModuleId === module.id;

                        return (
                            <div
                                key={module.id}
                                style={{ zIndex: openDropdownId === module.id ? 9999 : 10 }}
                                className={`
                                relative border-2 hover:shadow-lg transition-all duration-300 group bg-[var(--card-bg)] rounded-xl
                                ${isExpanded ? 'border-blue-500/70 dark:border-blue-500/50 bg-[var(--surface-2)]' : 'border-[var(--border-color)] hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 bg-[var(--surface)]'}
                            `}
                            >
                                {/* Module Row Header */}
                                <div className="p-4 sm:p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">

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
                                                <span
                                                    className={`text-[10px] px-2 py-0.5 rounded-md border-2 uppercase font-bold tracking-wider whitespace-nowrap flex-shrink-0 transition-all duration-200 shadow-md ${module.active
                                                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-emerald-500/20'
                                                        : 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30 shadow-orange-500/20'
                                                        }`}
                                                >
                                                    {module.active ? 'Active' : 'Inactive'}
                                                </span>
                                            </div>
                                            {module.description && (
                                                <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-1 max-w-md hidden sm:block">
                                                    {module.description}
                                                </p>
                                            )}
                                            <div className="flex items-center gap-3 text-xs muted mt-2">
                                                <div className="flex items-center gap-1.5">

                                                    <span>{module.units_count} unit{module.units_count !== 1 ? 's' : ''}</span>
                                                </div>

                                                <span>Order: {module.order}</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Divider for Mobile */}
                                    <div className="h-px w-full bg-white/5 lg:hidden"></div>

                                    {/* Right: Action Buttons */}
                                    <div className="flex items-center justify-between lg:justify-end gap-2 w-full lg:w-auto flex-wrap">
                                        <button
                                            onClick={() => openCreateLesson(module)}
                                            className="px-2 py-1 sm:px-3 sm:py-1.5 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-2 border-cyan-500/30 rounded-lg text-xs font-bold hover:bg-cyan-500/20 hover:border-cyan-500/50 transition-all duration-200 flex items-center gap-1 sm:gap-1.5 shadow-md hover:shadow-cyan-500/20 flex-shrink-0"
                                        >
                                            <FaPlus className="w-3 h-3 hidden sm:inline" />
                                            <span className="hidden sm:inline">Add Lesson</span>
                                            <span className="inline sm:hidden">Lesson</span>
                                        </button>
                                        <button
                                            onClick={() => openCreateQuiz(module)}
                                            className="px-2 py-1 sm:px-3 sm:py-1.5 bg-green-500/10 text-green-600 dark:text-green-400 border-2 border-green-500/30 rounded-lg text-xs font-bold hover:bg-green-500/20 hover:border-green-500/50 transition-all duration-200 flex items-center gap-1 sm:gap-1.5 shadow-md hover:shadow-green-500/20 flex-shrink-0"
                                        >
                                            <FaPlus className="w-3 h-3 hidden sm:inline" />
                                            <span className="hidden sm:inline ">Add Quiz</span>
                                            <span className="inline sm:hidden">Quiz</span>
                                        </button>
                                        <button
                                            onClick={() => openCreateExercise(module)}
                                            className="px-2 py-1 sm:px-3 sm:py-1.5 bg-purple-500/10 text-purple-600 dark:text-purple-400 border-2 border-purple-500/30 rounded-lg text-xs font-bold hover:bg-purple-500/20 hover:border-purple-500/50 transition-all duration-200 flex items-center gap-1 sm:gap-1.5 shadow-md hover:shadow-purple-500/20 flex-shrink-0"
                                        >
                                            <FaPlus className="w-3 h-3 hidden sm:inline" />
                                            <span className="hidden sm:inline">Add Exercise</span>
                                            <span className="inline sm:hidden">Exercise</span>
                                        </button>
                                        <button
                                            onClick={() => {
                                                openDesignModule(module.id);
                                            }}
                                            className="px-2 py-1 sm:px-3 sm:py-1.5 bg-amber-500/10 text-amber-600 dark:text-amber-400 border-2 border-amber-500/30 rounded-lg text-xs font-bold hover:bg-amber-500/20 hover:border-amber-500/50 transition-all duration-200 flex items-center gap-1 sm:gap-1.5 shadow-md hover:shadow-amber-500/20 flex-shrink-0"
                                        >
                                            <svg className="w-3 h-3 hidden sm:inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                                            </svg>
                                            <span className="hidden sm:inline">Design</span>
                                            <span className="inline sm:hidden">Design</span>
                                        </button>

                                        {/* Three-dot dropdown menu */}
                                        <div className="relative flex-shrink-0 z-[100]" ref={openDropdownId === module.id ? dropdownRef : null}>
                                            <button
                                                onClick={() => toggleDropdown(module.id)}
                                                className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-300 border-2 ${openDropdownId === module.id
                                                    ? 'bg-[var(--input-bg)] border-[var(--border-strong)] text-[var(--text-primary)]'
                                                    : 'bg-[var(--input-bg)] border-[var(--border-color)] text-[var(--text-muted)] hover:border-[var(--border-strong)] hover:text-[var(--text-primary)]'
                                                    }`}
                                            >
                                                <FaEllipsisV className="w-3.5 h-3.5" />
                                            </button>

                                            {/* Dropdown Menu */}
                                            {openDropdownId === module.id && (
                                                <div
                                                    className="absolute right-0 mt-2 z-[9999] w-36 bg-[var(--surface-2)] border-2 border-[var(--border-color)] rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.4)] py-2 flex flex-col text-sm animate-fadeIn"
                                                    style={{ pointerEvents: 'auto' }}
                                                >
                                                    <button
                                                        className="flex items-center gap-2 px-4 py-2.5 hover:bg-blue-500/10 transition text-left text-[var(--text-primary)] cursor-pointer w-full"
                                                        onClick={() => {
                                                            openEditModule(module);
                                                            setOpenDropdownId(null);
                                                        }}
                                                    >
                                                        <FaEdit className="w-4 h-4 text-blue-400" />
                                                        <span>Edit</span>
                                                    </button>
                                                    <button
                                                        className="flex items-center gap-2 px-4 py-2.5 hover:bg-red-500/10 transition text-left text-[var(--text-primary)] cursor-pointer w-full"
                                                        onClick={() => {
                                                            if (window.confirm(`Delete module "${module.name}"?`)) {
                                                                handleDeleteModule(courseId, module.id);
                                                            }
                                                            setOpenDropdownId(null);
                                                        }}
                                                    >
                                                        <FaTrash className="w-4 h-4 text-red-400" />
                                                        <span>Delete</span>
                                                    </button>
                                                </div>
                                            )}
                                        </div>

                                        {/* Toggle CTA */}
                                        <button
                                            onClick={() => toggleModule(module.id)}
                                            className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-300 border-2 flex-shrink-0 ${isExpanded
                                                ? 'bg-blue-500/15 border-blue-500/30 text-blue-400'
                                                : 'bg-[var(--input-bg)] border-[var(--border-color)] text-gray-600 dark:text-gray-400'
                                                }`}
                                        >
                                            {isExpanded ? <FaChevronUp size={14} /> : <FaChevronDown size={14} />}
                                        </button>
                                    </div>
                                </div>

                                {/* Dropdown Content - Units */}
                                {isExpanded && (
                                    <div className="border-t-2 border-[var(--border-subtle)] bg-[var(--input-bg)] animate-fadeIn relative shadow-inner">
                                        {(!module.units || module.units.length === 0) ? (
                                            <div className="p-8 text-center text-[var(--text-muted)] text-sm italic bg-[var(--surface)] border border-dashed border-[var(--border-color)] rounded-lg m-4">
                                                No learning units yet. Add a lesson, quiz, or exercise to get started.
                                            </div>
                                        ) : (
                                            <div className="p-4 space-y-3">
                                                {module.units.map((unit) => (
                                                    <div
                                                        key={unit.id}
                                                        className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 sm:p-4 rounded-lg bg-[var(--surface)] border-2 border-[var(--border-color)] hover:border-[var(--border-strong)] hover:shadow-md transition-all duration-200 group gap-3"
                                                    >
                                                        <div className="flex items-center gap-3 sm:gap-4 flex-1 min-w-0">
                                                            {/* Type Icon */}
                                                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center border-2 flex-shrink-0 ${unit.type === 'lesson'
                                                                ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/30'
                                                                : unit.is_exercise
                                                                    ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30'
                                                                    : 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30'
                                                                }`}>
                                                                {unit.type === 'lesson' ? (
                                                                    <FaVideo className="w-4 h-4" />
                                                                ) : unit.is_exercise ? (
                                                                    <FaPuzzlePiece className="w-4 h-4" />
                                                                ) : (
                                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                    </svg>
                                                                )}
                                                            </div>

                                                            {/* Unit Info */}
                                                            <div className="flex-1 min-w-0">
                                                                <div className="font-semibold text-sm text-[var(--text-primary)] truncate group-hover:text-blue-500 transition-colors">
                                                                    {unit.name || `${unit.type} #${unit.id}`}
                                                                </div>
                                                                <div className="text-xs muted flex items-center gap-2 mt-0.5">
                                                                    <span className={`uppercase font-bold text-[10px] px-1.5 py-0.5 rounded border ${unit.type === 'lesson'
                                                                        ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/30'
                                                                        : unit.is_exercise
                                                                            ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30'
                                                                            : 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30'
                                                                        }`}>
                                                                        {unit.type === 'lesson' ? 'LESSON' : unit.is_exercise ? 'EXERCISE' : 'QUIZ'}
                                                                    </span>
                                                                    <span className="text-[11px] font-mono">ORDER #{unit.order}</span>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Action Buttons */}
                                                        <div className="flex flex-wrap gap-2 mt-2 sm:mt-0 justify-end sm:justify-end w-full sm:w-auto">
                                                            {unit.type === 'lesson' ? (
                                                                <>
                                                                    <button
                                                                        onClick={() => openEditLesson(module, unit)}
                                                                        className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400 rounded-lg text-xs font-medium hover:bg-blue-500/20 hover:border-blue-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Edit
                                                                    </button>
                                                                    <button
                                                                        onClick={() => {
                                                                            if (window.confirm(`Delete lesson "${unit.name}"?`)) {
                                                                                handleDeleteLesson(module.id, unit.lesson_id);
                                                                            }
                                                                        }}
                                                                        className="px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/20 hover:border-red-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Delete
                                                                    </button>
                                                                </>
                                                            ) : unit.is_exercise ? (
                                                                <>
                                                                    <button
                                                                        onClick={() => openDesignQuestionPaper(unit.quiz_id, unit.questionpaper_id || null, unit.name)}
                                                                        className="px-3 py-1.5 bg-purple-500/10 border border-purple-500/30 text-purple-600 dark:text-purple-400 rounded-lg text-xs font-medium hover:bg-purple-500/20 hover:border-purple-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Questions
                                                                    </button>
                                                                    <button
                                                                        onClick={() => openEditExercise(module, unit)}
                                                                        className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400 rounded-lg text-xs font-medium hover:bg-blue-500/20 hover:border-blue-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Edit
                                                                    </button>
                                                                    <button
                                                                        onClick={() => {
                                                                            if (window.confirm(`Delete exercise "${unit.name}"?`)) {
                                                                                handleDeleteExercise(module.id, unit.quiz_id);
                                                                            }
                                                                        }}
                                                                        className="px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/20 hover:border-red-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Delete
                                                                    </button>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <button
                                                                        onClick={() => openDesignQuestionPaper(unit.quiz_id, unit.questionpaper_id || null, unit.name)}
                                                                        className="px-3 py-1.5 bg-green-500/10 border border-green-500/30 text-green-600 dark:text-green-400 rounded-lg text-xs font-medium hover:bg-green-500/20 hover:border-green-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Questions
                                                                    </button>
                                                                    <button
                                                                        onClick={() => openEditQuiz(module, unit)}
                                                                        className="px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-400 rounded-lg text-xs font-medium hover:bg-blue-500/20 hover:border-blue-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Edit
                                                                    </button>
                                                                    <button
                                                                        onClick={() => {
                                                                            if (window.confirm(`Delete quiz "${unit.name}"?`)) {
                                                                                handleDeleteQuiz(module.id, unit.quiz_id);
                                                                            }
                                                                        }}
                                                                        className="px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 rounded-lg text-xs font-medium hover:bg-red-500/20 hover:border-red-500/50 transition-all shadow-sm"
                                                                    >
                                                                        Delete
                                                                    </button>
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="text-center py-12 bg-[var(--input-bg)] border-2 border-dashed border-[var(--border-color)] rounded-xl">
                    <div className="mb-4 p-4 bg-cyan-500/10 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
                        <FaLayerGroup className="text-cyan-400 w-8 h-8" />
                    </div>
                    <p className="text-[var(--text-primary)] font-semibold">No modules yet for this course.</p>
                    <p className="text-xs muted mt-2">Create your first module to get started!</p>
                </div>
            )}
        </div>
    );
};

export default CourseModules;