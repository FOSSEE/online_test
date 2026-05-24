import { create } from 'zustand';
import {
    getTeacherCourse, getCourseModules, createModule, updateModule, deleteModule,
    updateQuiz, deleteQuiz, createQuiz, getTeacherQuiz, 
    getCourseEnrollments, approveEnrollment, rejectEnrollment, removeEnrollment,
    reorderCourseModules, reorderModuleUnits, getCourseAnalytics, 
    getTeacherLesson, createTeacherLesson, updateTeacherLesson, deleteTeacherLesson, 
    getCourseDesign, addModulesToCourse, changeCourseModuleOrder, removeModulesFromCourse,
    changeCourseModulePrerequisiteCompletion, changeCourseModulePrerequisitePassing,
    getModuleDesign, addUnitsToModule, changeModuleUnitOrder, removeUnitsFromModule,
    changeModuleUnitPrerequisite, createTeacherExercise, getTeacherExercise, updateTeacherExercise, deleteTeacherExercise,
    getQuestionPaperDesign, addFixedQuestions, removeFixedQuestions, addRandomQuestionsSet, removeRandomQuestionsSet,
    saveQuestionPaperOptions, filterQuestionPaperQuestions
} from '../api/api';

const initialModuleForm = {
    name: '',
    description: '',
    order: 1,
    check_prerequisite: false,
    active: true,
};

const initialLessonForm = {
    name: '',
    description: '',
    video_path: '',
    active: true,
    order: 1,
};

const initialQuizForm = {
    description: '',
    instructions: '',
    duration: 20,
    attempts_allowed: 1,
    time_between_attempts: 0.0,
    pass_criteria: 40.0,
    weightage: 100.0,
    allow_skip: true,
    view_answerpaper: true, // Added
    is_exercise: false,
    active: true,
    start_date_time: '', // Added
    end_date_time: '',   // Added
    order: 1,
};

const initialExerciseForm = {
    description: '',
    view_answerpaper: false,
    active: true,
};

const useManageCourseStore = create((set, get) => ({
    // State
    activeTab: 'Modules',
    activeForumTab: 'Course Forum',
    course: null,
    modules: [],
    loading: true,
    error: null,
    
    analytics: null,
    loadingAnalytics: false,
    showQuizQuestionManager: false,
    selectedQuizId: null,
    moduleOrder: [],
    unitOrders: {},
    savingOrder: false,
    showModuleForm: false,
    editingModule: null,
    showLessonForm: false,
    showQuizForm: false,
    showExerciseForm: false, // Added
    selectedModule: null,
    editingLesson: null,
    editingQuiz: null,
    editingExercise: null,   // Added
    moduleFormData: { ...initialModuleForm },
    lessonFormData: { ...initialLessonForm },
    quizFormData: { ...initialQuizForm },
    exerciseFormData: { ...initialExerciseForm }, // Added

    // Actions
    setActiveTab: (tab) => set({ activeTab: tab }),
    setActiveForumTab: (tab) => set({ activeForumTab: tab }),
    setShowQuizQuestionManager: (val) => set({ showQuizQuestionManager: val }),
    setSelectedQuizId: (id) => set({ selectedQuizId: id }),

    // Load course data
    loadCourseData: async (courseId) => {
        set({ loading: true, error: null });
        try {
            const courseData = await getTeacherCourse(courseId);
            if (!courseData) throw new Error('Course data not found');
            if (courseData.error) throw new Error(courseData.error);
            set({ course: courseData });
            if (courseData.modules && Array.isArray(courseData.modules)) {
                set({ modules: courseData.modules });
            } else {
                const modulesData = await getCourseModules(courseId);
                set({ modules: Array.isArray(modulesData) ? modulesData : [] });
            }
        } catch (err) {
            set({ error: err.message, course: null });
        } finally {
            set({ loading: false });
        }
    },

    // Analytics tab ============================================================
    loadAnalytics: async (courseId) => {
        set({ loadingAnalytics: true });
        try {
            const data = await getCourseAnalytics(courseId);
            set({ analytics: data });
        } catch (err) {
            set({ analytics: null });
        } finally {
            set({ loadingAnalytics: false });
        }
    },

    // Enrollments tab ============================================================
    enrollments: { enrolled: [], pending_requests: [], rejected: [] },
    loadingEnrollments: false,
    enrollmentsError: null,

    loadEnrollments: async (courseId) => {
        set({ loadingEnrollments: true, enrollmentsError: null });
        try {
            const data = await getCourseEnrollments(courseId);
            set({
                enrollments: {
                    enrolled: data.enrolled || [],
                    pending_requests: data.pending_requests || [],
                    rejected: data.rejected || []
                }
            });
        } catch (err) {
            set({ enrollmentsError: err?.response?.data?.error || 'Failed to load enrollments' });
        } finally {
            set({ loadingEnrollments: false });
        }
    },

    approveEnrollments: async (courseId, userIds, wasRejected = false) => {
        set({ loadingEnrollments: true, enrollmentsError: null });
        try {
            await approveEnrollment(courseId, userIds, wasRejected);
            await get().loadEnrollments(courseId);
        } catch (err) {
            set({ enrollmentsError: err?.response?.data?.error || 'Failed to approve enrollment' });
        } finally {
            set({ loadingEnrollments: false });
        }
    },

    rejectEnrollments: async (courseId, userIds, wasEnrolled = false) => {
        set({ loadingEnrollments: true, enrollmentsError: null });
        try {
            await rejectEnrollment(courseId, userIds, wasEnrolled);
            await get().loadEnrollments(courseId);
        } catch (err) {
            set({ enrollmentsError: err?.response?.data?.error || 'Failed to reject enrollment' });
        } finally {
            set({ loadingEnrollments: false });
        }
    },

    removeEnrollments: async (courseId, userIds) => {
        set({ loadingEnrollments: true, enrollmentsError: null });
        try {
            await removeEnrollment(courseId, userIds);
            await get().loadEnrollments(courseId);
        } catch (err) {
            set({ enrollmentsError: err?.response?.data?.error || 'Failed to remove enrollment' });
        } finally {
            set({ loadingEnrollments: false });
        }
    },

    // DESIGN COURSE TAB ============================================================
    designCourse: null,
    loadingDesignCourse: false,
    designCourseError: null,

    loadDesignCourse: async (courseId) => {
        set({ loadingDesignCourse: true, designCourseError: null });
        try {
            const data = await getCourseDesign(courseId);
            set({ designCourse: data });
        } catch (err) {
            set({ designCourseError: err.message, designCourse: null });
        } finally {
            set({ loadingDesignCourse: false });
        }
    },

    handleAddModulesToCourse: async (courseId, moduleList) => {
        set({ loadingDesignCourse: true });
        try {
            await addModulesToCourse(courseId, moduleList);
            await get().loadDesignCourse(courseId);
            await get().loadCourseData(courseId);
        } catch (err) {
            set({ designCourseError: err.message });
        } finally {
            set({ loadingDesignCourse: false });
        }
    },

    handleChangeCourseModuleOrder: async (courseId, orderedList) => {
        set({ loadingDesignCourse: true });
        try {
            await changeCourseModuleOrder(courseId, orderedList);
            await get().loadDesignCourse(courseId);
            await get().loadCourseData(courseId);
        } catch (err) {
            set({ designCourseError: err.message });
        } finally {
            set({ loadingDesignCourse: false });
        }
    },

    handleRemoveModulesFromCourse: async (courseId, deleteList) => {
        set({ loadingDesignCourse: true });
        try {
            await removeModulesFromCourse(courseId, deleteList);
            await get().loadDesignCourse(courseId);
            await get().loadCourseData(courseId);
        } catch (err) {
            set({ designCourseError: err.message });
        } finally {
            set({ loadingDesignCourse: false });
        }
    },

    handleChangeCourseModulePrerequisiteCompletion: async (courseId, checkPrereqList) => {
        set({ loadingDesignCourse: true });
        try {
            await changeCourseModulePrerequisiteCompletion(courseId, checkPrereqList);
            await get().loadDesignCourse(courseId);
        } catch (err) {
            set({ designCourseError: err.message });
        } finally {
            set({ loadingDesignCourse: false });
        }
    },

    handleChangeCourseModulePrerequisitePassing: async (courseId, checkPrereqPassesList) => {
        set({ loadingDesignCourse: true });
        try {
            await changeCourseModulePrerequisitePassing(courseId, checkPrereqPassesList);
            await get().loadDesignCourse(courseId);
        } catch (err) {
            set({ designCourseError: err.message });
        } finally {
            set({ loadingDesignCourse: false });
        }
    },

    // Module tab ============================================================
    initializeOrdering: () => {
        const modules = get().modules;
        const orderedModules = [...modules].sort((a, b) => (a.order || 0) - (b.order || 0));
        set({ moduleOrder: orderedModules.map(m => m.id) });
        const orders = {};
        modules.forEach(module => {
            if (module.units) {
                const orderedUnits = [...module.units].sort((a, b) => (a.order || 0) - (b.order || 0));
                orders[module.id] = orderedUnits.map(u => ({
                    unit_id: u.lesson_id || u.quiz_id,
                    order: u.order || 0
                }));
            }
        });
        set({ unitOrders: orders });
    },

    moveModule: (moduleId, direction) => {
        const moduleOrder = [...get().moduleOrder];
        const currentIndex = moduleOrder.indexOf(moduleId);
        if (currentIndex === -1) return;
        const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
        if (newIndex < 0 || newIndex >= moduleOrder.length) return;
        [moduleOrder[currentIndex], moduleOrder[newIndex]] = [moduleOrder[newIndex], moduleOrder[currentIndex]];
        set({ moduleOrder });
    },

    saveModuleOrder: async (courseId) => {
        set({ savingOrder: true });
        try {
            const moduleOrder = get().moduleOrder;
            const moduleOrders = moduleOrder.map((moduleId, index) => ({
                module_id: moduleId,
                order: index + 1
            }));
            await reorderCourseModules(courseId, moduleOrders);
            await get().loadCourseData(courseId);
        } finally {
            set({ savingOrder: false });
        }
    },

    moveUnit: (moduleId, unitId, direction) => {
        const unitOrders = { ...get().unitOrders };
        const units = unitOrders[moduleId] || [];
        const currentIndex = units.findIndex(u => u.unit_id === unitId);
        if (currentIndex === -1) return;
        const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
        if (newIndex < 0 || newIndex >= units.length) return;
        [units[currentIndex], units[newIndex]] = [units[newIndex], units[currentIndex]];
        unitOrders[moduleId] = units;
        set({ unitOrders });
    },

    saveUnitOrder: async (moduleId) => {
        set({ savingOrder: true });
        try {
            const units = get().unitOrders[moduleId] || [];
            const unitOrdersData = units.map((unit, index) => ({
                unit_id: unit.unit_id,
                order: index + 1
            }));
            await reorderModuleUnits(moduleId, unitOrdersData);
            await get().loadCourseData(get().course.id);
        } finally {
            set({ savingOrder: false });
        }
    },

    // Module CRUD ============================================================
    setShowModuleForm: (val) => set({ showModuleForm: val }),
    setEditingModule: (mod) => set({ editingModule: mod }),
    setModuleFormData: (data) => set({ moduleFormData: data }),
    
    handleModuleFormChange: (e) => {
        const { name, value, type, checked } = e.target;
        set(state => ({
            moduleFormData: {
                ...state.moduleFormData,
                [name]: type === 'checkbox' ? checked : value
            }
        }));
    },

    handleCreateModule: async (courseId) => {
        await createModule(courseId, get().moduleFormData);
        set({ showModuleForm: false, moduleFormData: { ...initialModuleForm } });
        await get().loadCourseData(courseId);
    },

    handleUpdateModule: async (courseId) => {
        await updateModule(courseId, get().editingModule.id, get().moduleFormData);
        set({ showModuleForm: false, editingModule: null, moduleFormData: { ...initialModuleForm } });
        await get().loadCourseData(courseId);
    },

    handleDeleteModule: async (courseId, moduleId) => {
        await deleteModule(courseId, moduleId);
        await get().loadCourseData(courseId);
    },

    openEditModule: (module) => {
        set({
            editingModule: module,
            moduleFormData: {
                name: module.name,
                description: module.description,
                order: module.order,
                check_prerequisite: module.check_prerequisite,
                active: module.active,
            },
            showModuleForm: true
        });
    },

    openCreateModule: (modules) => {
        set({
            editingModule: null,
            moduleFormData: { ...initialModuleForm, order: modules.length + 1 },
            showModuleForm: true
        });
    },

    // ============================================================
    //  LESSON CRUD 
    // ============================================================
    
    setShowLessonForm: (val) => set({ showLessonForm: val }),
    setSelectedModule: (mod) => set({ selectedModule: mod }),
    setEditingLesson: (lesson) => set({ editingLesson: lesson }),
    setLessonFormData: (data) => set({ lessonFormData: data }),
    
    handleLessonFormChange: (e) => {
        const { name, value, type, checked, files } = e.target;
        set(state => ({
            lessonFormData: {
                ...state.lessonFormData,
                
                ...(type !== 'file' && { [name]: type === 'checkbox' ? checked : value }),
                
                ...(name === 'video_file' && files && files.length > 0
                    ? { newVideoFile: files[0], video_file: files }
                    : {}),
                
                ...(name === 'Lesson_files' && files
                    ? { Lesson_files: files, newFiles: files }
                    : {}),
            }
        }));
    },

    
    openCreateLesson: (module) => {
        const lastUnit = module.units && module.units.length > 0
            ? Math.max(...module.units.map(u => u.order))
            : 0;
        set({
            selectedModule: module,
            editingLesson: null,
            lessonFormData: { ...initialLessonForm, order: lastUnit + 1 },
            showLessonForm: true
        });
    },

   
    
    openEditLesson: async (module, unit) => {
        const courseId = get().course?.id;
        if (!courseId) {
            console.error('Course ID not found');
            return;
        }

        set({ selectedModule: module, editingLesson: unit, loading: true });
        
        try {
            
            const lessonData = await getTeacherLesson(courseId, module.id, unit.lesson_id);
            set({
                lessonFormData: {
                    name: lessonData.name || '',
                    description: lessonData.description || '',
                    video_path: lessonData.video_path || '',
                    existing_video_file_url: lessonData.video_file || null, 
                    active: lessonData.active !== undefined ? lessonData.active : true,
                    order: lessonData.order || unit.order,
                    files: lessonData.files || [], // Existing attached files
                },
                showLessonForm: true,
                loading: false
            });
        } catch (error) {
            console.error('Failed to load lesson:', error);
            
            set({
                lessonFormData: {
                    name: unit.name || '',
                    description: '',
                    video_path: '',
                    active: true,
                    order: unit.order,
                },
                showLessonForm: true,
                loading: false
            });
        }
    },

    handleCreateLesson: async () => {
        const { selectedModule, lessonFormData, course } = get();
        if (!selectedModule || !course) return;

        try {
            set({ loading: true });
            
            const payload = new FormData();
            payload.append('name', lessonFormData.name);
            payload.append('description', lessonFormData.description || '');
            payload.append('video_path', lessonFormData.video_path || '');
            payload.append('active', lessonFormData.active);
            
            
            const fileToUpload = lessonFormData.newVideoFile || (lessonFormData.video_file && lessonFormData.video_file[0]);
            
            if (fileToUpload instanceof File) {
                payload.append('video_file', fileToUpload);
            }

            if (lessonFormData.Lesson_files && lessonFormData.Lesson_files.length > 0) {
                Array.from(lessonFormData.Lesson_files).forEach(file => {
                    payload.append('Lesson_files', file);
                });
            }
            
            await createTeacherLesson(course.id, selectedModule.id, payload);
            set({ showLessonForm: false, selectedModule: null, lessonFormData: { ...initialLessonForm }, loading: false });
            await get().loadCourseData(course.id);
        } catch (error) {
            console.error('Failed to create lesson:', error);
            set({ loading: false, error: error.message });
        }
    },


    
    handleUpdateLesson: async () => {
        const { selectedModule, editingLesson, lessonFormData, course } = get();
        if (!selectedModule || !editingLesson || !course) return;

        try {
            set({ loading: true });
            
            const payload = new FormData();
            payload.append('name', lessonFormData.name);
            payload.append('description', lessonFormData.description || '');
            payload.append('video_path', lessonFormData.video_path || '');
            payload.append('active', lessonFormData.active);

            
            const fileToUpload = lessonFormData.newVideoFile || (lessonFormData.video_file && lessonFormData.video_file[0]);
            
            if (fileToUpload instanceof File) {
                payload.append('video_file', fileToUpload);
            }

            if (lessonFormData.clearVideoFile) {
                payload.append('video_file-clear', 'true');
            }

            
            if (lessonFormData.Lesson_files && lessonFormData.Lesson_files.length > 0) {
                Array.from(lessonFormData.Lesson_files).forEach(file => {
                     payload.append('Lesson_files', file);
                });
            }

           
            if (lessonFormData.filesToDelete && lessonFormData.filesToDelete.length > 0) {
                lessonFormData.filesToDelete.forEach(id => {
                    payload.append('delete_files', id);
                });
            }

            await updateTeacherLesson(
                course.id, 
                selectedModule.id, 
                editingLesson.lesson_id, 
                payload
            );
            set({ 
                showLessonForm: false, 
                selectedModule: null,
                editingLesson: null,
                lessonFormData: { ...initialLessonForm },
                loading: false
            });
            await get().loadCourseData(course.id);
        } catch (error) {
            console.error('Failed to update lesson:', error);
            set({ loading: false, error: error.message });
        }
    },

    handleDeleteLesson: async (moduleId, lessonId) => {
        const { course } = get();
        if (!moduleId || !course) {
            console.error('Module ID or Course not found');
            return;
        }

        try {
            set({ loading: true });
            await deleteTeacherLesson(course.id, moduleId, lessonId);
            set({ loading: false });
            await get().loadCourseData(course.id);
        } catch (error) {
            console.error('Failed to delete lesson:', error);
            set({ loading: false, error: error.message });
        }
    },

    // Quiz CRUD ============================================================
    setShowQuizForm: (val) => set({ showQuizForm: val }),
    setEditingQuiz: (quiz) => set({ editingQuiz: quiz }),
    setQuizFormData: (data) => set({ quizFormData: data }),
    
    handleQuizFormChange: (e) => {
        const { name, value, type, checked } = e.target;
        set(state => ({
            quizFormData: {
                ...state.quizFormData,
                [name]: type === 'checkbox' ? checked : (type === 'number' ? parseFloat(value) : value)
            }
        }));
    },

    openCreateQuiz: (module) => {
        const lastUnit = module.units && module.units.length > 0
            ? Math.max(...module.units.map(u => u.order))
            : 0;
        
        // Default dates: Start now, End in 1 year
        const now = new Date();
        const nextYear = new Date();
        nextYear.setFullYear(now.getFullYear() + 1);

        set({
            selectedModule: module,
            editingQuiz: null,
            quizFormData: { 
                ...initialQuizForm, 
                order: lastUnit + 1,
                start_date_time: now.toISOString().slice(0, 16), // Format for datetime-local input
                end_date_time: nextYear.toISOString().slice(0, 16)
            },
            showQuizForm: true
        });
    },

    openEditQuiz: async (module, unit) => {
        const courseId = get().course?.id;
        if (!courseId) return;

        set({ selectedModule: module, editingQuiz: unit });
        try {
            const quizData = await getTeacherQuiz(courseId, module.id, unit.quiz_id);
            
            // Helper to format API date string to input datetime-local format
            const formatDateForInput = (dateStr) => {
                if (!dateStr) return '';
                const date = new Date(dateStr);
                // Adjust to local timezone string for input
                const offset = date.getTimezoneOffset() * 60000;
                const localISOTime = (new Date(date - offset)).toISOString().slice(0, 16);
                return localISOTime;
            };

            set({
                quizFormData: {
                    id: quizData.id,
                    description: quizData.description || '',
                    instructions: quizData.instructions || '',
                    duration: quizData.duration || 30,
                    attempts_allowed: quizData.attempts_allowed || 1,
                    time_between_attempts: quizData.time_between_attempts || 0.0,
                    pass_criteria: quizData.pass_criteria || 40.0,
                    weightage: quizData.weightage || 100.0,
                    allow_skip: quizData.allow_skip !== undefined ? quizData.allow_skip : true,
                    view_answerpaper: quizData.view_answerpaper !== undefined ? quizData.view_answerpaper : true, // Added
                    is_exercise: quizData.is_exercise !== undefined ? quizData.is_exercise : false,
                    active: quizData.active !== undefined ? quizData.active : true,
                    start_date_time: formatDateForInput(quizData.start_date_time), // Added
                    end_date_time: formatDateForInput(quizData.end_date_time),     // Added
                    order: quizData.order || unit.order,
                },
                showQuizForm: true
            });
        } catch (error) {
            console.error("Error fetching quiz:", error);
            // Fallback
            set({
                quizFormData: {
                    ...initialQuizForm,
                    description: unit.name || '',
                    order: unit.order,
                },
                showQuizForm: true
            });
        }
    },

    handleCreateQuiz: async () => {
        const { selectedModule, quizFormData, course } = get();
        if (!selectedModule || !course) return;

        try {
            set({ loading: true });
            
            // Ensure dates are sent in ISO format for the API
            const payload = { ...quizFormData };
            if (payload.start_date_time) payload.start_date_time = new Date(payload.start_date_time).toISOString();
            if (payload.end_date_time) payload.end_date_time = new Date(payload.end_date_time).toISOString();

            await createQuiz(course.id, selectedModule.id, payload);
            set({ showQuizForm: false, selectedModule: null, quizFormData: { ...initialQuizForm }, loading: false });
            await get().loadCourseData(course.id);
        } catch (err) {
            console.error(err);
            set({ loading: false, error: err.message });
        }
    },

    handleUpdateQuiz: async () => {
        const { selectedModule, editingQuiz, quizFormData, course } = get();
        if (!selectedModule || !editingQuiz || !course) return;

        try {
            set({ loading: true });
            
             // Ensure dates are sent in ISO format for the API
            const payload = { ...quizFormData };
            if (payload.start_date_time) payload.start_date_time = new Date(payload.start_date_time).toISOString();
            if (payload.end_date_time) payload.end_date_time = new Date(payload.end_date_time).toISOString();

            await updateQuiz(course.id, selectedModule.id, editingQuiz.quiz_id, payload);
            set({ showQuizForm: false, selectedModule: null, editingQuiz: null, quizFormData: { ...initialQuizForm }, loading: false });
            await get().loadCourseData(course.id);
        } catch (err) {
            console.error(err);
            set({ loading: false, error: err.message });
        }
    },
    


    // DESIGN MODULE TAB ============================================================
    designModule: null,
    loadingDesignModule: false,
    designModuleError: null,
    showDesignModuleModal: false, // Added
    designingModuleId: null,      // Added

    openDesignModule: (moduleId) => {
        set({ showDesignModuleModal: true, designingModuleId: moduleId });
        const courseId = get().course?.id;
        get().loadModuleDesign(moduleId, courseId);
    },

    closeDesignModule: () => {
        set({ showDesignModuleModal: false, designingModuleId: null, designModule: null });
    },

    // Load module design data (Available items vs Added items)
    loadModuleDesign: async (moduleId, courseId = null) => {
        set({ loadingDesignModule: true, designModuleError: null });
        try {
            const data = await getModuleDesign(moduleId, courseId);
            set({ designModule: data });
        } catch (err) {
            set({ designModuleError: err.message, designModule: null });
        } finally {
            set({ loadingDesignModule: false });
        }
    },

    // Add items (quizzes/lessons) to the module
    handleAddUnitsToModule: async (moduleId, chosenList, courseId = null) => {
        set({ loadingDesignModule: true });
        try {
            await addUnitsToModule(moduleId, chosenList, courseId);
            // Refresh design data to show new list
            await get().loadModuleDesign(moduleId, courseId);
            // Also refresh main course data to reflect hierarchy changes if needed
            if (courseId) await get().loadCourseData(courseId);
        } catch (err) {
            set({ designModuleError: err.message });
        } finally {
            set({ loadingDesignModule: false });
        }
    },

    // Reorder items within the module
    handleChangeModuleUnitOrder: async (moduleId, orderedList, courseId = null) => {
        set({ loadingDesignModule: true });
        try {
            await changeModuleUnitOrder(moduleId, orderedList, courseId);
            await get().loadModuleDesign(moduleId, courseId);
            if (courseId) await get().loadCourseData(courseId);
        } catch (err) {
            set({ designModuleError: err.message });
        } finally {
            set({ loadingDesignModule: false });
        }
    },

    // Remove items from the module
    handleRemoveUnitsFromModule: async (moduleId, deleteList, courseId = null) => {
        set({ loadingDesignModule: true });
        try {
            await removeUnitsFromModule(moduleId, deleteList, courseId);
            await get().loadModuleDesign(moduleId, courseId);
            if (courseId) await get().loadCourseData(courseId);
        } catch (err) {
            set({ designModuleError: err.message });
        } finally {
            set({ loadingDesignModule: false });
        }
    },

    // Toggle prerequisite check for specific units
    handleChangeModuleUnitPrerequisite: async (moduleId, checkPrereqList, courseId = null) => {
        set({ loadingDesignModule: true });
        try {
            await changeModuleUnitPrerequisite(moduleId, checkPrereqList, courseId);
            await get().loadModuleDesign(moduleId, courseId);
        } catch (err) {
            set({ designModuleError: err.message });
        } finally {
            set({ loadingDesignModule: false });
        }
    },

    
// EXERCISE TAB ===========================================================    


    setShowExerciseForm: (val) => set({ showExerciseForm: val }),
    setEditingExercise: (exercise) => set({ editingExercise: exercise }),
    setExerciseFormData: (data) => set({ exerciseFormData: data }),

    handleExerciseFormChange: (e) => {
        const { name, value, type, checked } = e.target;
        set((state) => ({
            exerciseFormData: {
                ...state.exerciseFormData,
                [name]: type === 'checkbox' ? checked : value,
            },
        }));
    },

    openCreateExercise: (module) => {
        set({
            selectedModule: module,
            editingExercise: null,
            exerciseFormData: { ...initialExerciseForm },
            showExerciseForm: true,
        });
    },

    openEditExercise: async (module, unit) => {
        const courseId = get().course?.id;
        if (!courseId) return;

        // Reset other form visibilities to be safe
        set({ 
            selectedModule: module, 
            editingExercise: unit, 
            showQuizForm: false, // Ensure Quiz form is hidden
            showLessonForm: false, 
            loading: true 
        });

        try {
            const exerciseData = await getTeacherExercise(courseId, module.id, unit.quiz_id);
            set({
                exerciseFormData: {
                    id: exerciseData.id,
                    description: exerciseData.description || '',
                    view_answerpaper: exerciseData.view_answerpaper || false,
                    active: exerciseData.active !== undefined ? exerciseData.active : true,
                },
                showExerciseForm: true, // Show ONLY exercise form
                loading: false,
            });
        } catch (error) {
            console.error("Error fetching exercise:", error);
            // Fallback if fetch fails
            set({
                exerciseFormData: {
                    ...initialExerciseForm,
                    description: unit.name || '',
                },
                showExerciseForm: true,
                loading: false,
            });
        }
    },

    handleCreateExercise: async () => {
        const { selectedModule, exerciseFormData, course } = get();
        if (!selectedModule || !course) return;

        try {
            set({ loading: true });
            
            // Send only the 3 editable properties
            const payload = {
                description: exerciseFormData.description,
                view_answerpaper: exerciseFormData.view_answerpaper,
                active: exerciseFormData.active,
            };

            await createTeacherExercise(course.id, selectedModule.id, payload);
            set({
                showExerciseForm: false,
                selectedModule: null,
                exerciseFormData: { ...initialExerciseForm },
                loading: false,
            });
            await get().loadCourseData(course.id);
        } catch (err) {
            console.error("Failed to create exercise:", err);
            set({ loading: false, error: err.message });
        }
    },

    handleUpdateExercise: async () => {
        const { selectedModule, editingExercise, exerciseFormData, course } = get();
        if (!selectedModule || !editingExercise || !course) return;

        try {
            set({ loading: true });

            // Send only the 3 editable properties
            const payload = {
                description: exerciseFormData.description,
                view_answerpaper: exerciseFormData.view_answerpaper,
                active: exerciseFormData.active,
            };

            await updateTeacherExercise(course.id, selectedModule.id, editingExercise.quiz_id, payload);
            set({
                showExerciseForm: false,
                selectedModule: null,
                editingExercise: null,
                exerciseFormData: { ...initialExerciseForm },
                loading: false,
            });
            await get().loadCourseData(course.id);
        } catch (err) {
            console.error("Failed to update exercise:", err);
            set({ loading: false, error: err.message });
        }
    },

    handleDeleteExercise: async (moduleId, quizId) => {
        const { course } = get();
        if (!course) return;

        try {
            set({ loading: true });
            await deleteTeacherExercise(course.id, moduleId, quizId);
            set({ loading: false });
            await get().loadCourseData(course.id);
        } catch (err) {
            console.error("Failed to delete exercise:", err);
            set({ loading: false, error: err.message });
        }
    },

// ============================================================
// DESIGN QUESTION PAPER TAB 
// ============================================================
    questionPaperDesign: null,
    filteredQuestions: null,     // Holds the results from the filter action
    loadingQuestionPaper: false,
    questionPaperError: null,
    showDesignQuestionPaperModal: false,
    designingQuizId: null,
    designingQuestionPaperId: null,
    designingQuizName: '', // <-- Add this

    openDesignQuestionPaper: (quizId, questionPaperId = null, quizName = '') => {
        set({ 
            showDesignQuestionPaperModal: true, 
            designingQuizId: quizId,
            designingQuestionPaperId: questionPaperId,
            designingQuizName: quizName // <-- Add this
        });
        const courseId = get().course?.id;
        if (courseId) {
            get().loadQuestionPaperDesign(courseId, quizId, questionPaperId);
        }
    },

    closeDesignQuestionPaper: () => {
        set({ 
            showDesignQuestionPaperModal: false, 
            designingQuizId: null, 
            designingQuestionPaperId: null,
            designingQuizName: '', // <-- Add this
            questionPaperDesign: null,
            filteredQuestions: null,
            questionPaperError: null
        });
    },
    
    loadQuestionPaperDesign: async (courseId, quizId, questionPaperId = null) => {
        set({ loadingQuestionPaper: true, questionPaperError: null });
        try {
            const data = await getQuestionPaperDesign(courseId, quizId, questionPaperId);
            set({ questionPaperDesign: data });
        } catch (err) {
            set({ questionPaperError: err.response?.data?.error || err.message || 'Failed to load question paper design' });
        } finally {
            set({ loadingQuestionPaper: false });
        }
    },

    handleAddFixedQuestions: async (courseId, quizId, questionPaperId, questionIds) => {
        set({ loadingQuestionPaper: true });
        try {
            await addFixedQuestions(courseId, quizId, questionPaperId, questionIds);
            await get().loadQuestionPaperDesign(courseId, quizId, questionPaperId);
        } catch (err) {
            set({ questionPaperError: err.response?.data?.error || err.message || 'Failed to add fixed questions' });
        } finally {
            set({ loadingQuestionPaper: false });
        }
    },

    handleRemoveFixedQuestions: async (courseId, quizId, questionPaperId, questionIds) => {
        set({ loadingQuestionPaper: true });
        try {
            await removeFixedQuestions(courseId, quizId, questionPaperId, questionIds);
            await get().loadQuestionPaperDesign(courseId, quizId, questionPaperId);
        } catch (err) {
            set({ questionPaperError: err.response?.data?.error || err.message || 'Failed to remove fixed questions' });
        } finally {
            set({ loadingQuestionPaper: false });
        }
    },

    handleAddRandomQuestionsSet: async (courseId, quizId, questionPaperId, questionIds, marks, numOfQuestions) => {
        set({ loadingQuestionPaper: true });
        try {
            await addRandomQuestionsSet(courseId, quizId, questionPaperId, questionIds, marks, numOfQuestions);
            await get().loadQuestionPaperDesign(courseId, quizId, questionPaperId);
        } catch (err) {
            set({ questionPaperError: err.response?.data?.error || err.message || 'Failed to add random question set' });
        } finally {
            set({ loadingQuestionPaper: false });
        }
    },

    handleRemoveRandomQuestionsSet: async (courseId, quizId, questionPaperId, randomSetIds) => {
        set({ loadingQuestionPaper: true });
        try {
            await removeRandomQuestionsSet(courseId, quizId, questionPaperId, randomSetIds);
            await get().loadQuestionPaperDesign(courseId, quizId, questionPaperId);
        } catch (err) {
            set({ questionPaperError: err.response?.data?.error || err.message || 'Failed to remove random question set' });
        } finally {
            set({ loadingQuestionPaper: false });
        }
    },

    handleSaveQuestionPaperOptions: async (courseId, quizId, questionPaperId, paperData) => {
        set({ loadingQuestionPaper: true });
        try {
            await saveQuestionPaperOptions(courseId, quizId, questionPaperId, paperData);
            await get().loadQuestionPaperDesign(courseId, quizId, questionPaperId);
        } catch (err) {
            set({ questionPaperError: err.response?.data?.error || err.message || 'Failed to save question paper options' });
        } finally {
            set({ loadingQuestionPaper: false });
        }
    },

    handleFilterQuestionPaperQuestions: async (courseId, quizId, questionPaperId, filters = {}) => {
        set({ loadingQuestionPaper: true });
        try {
            // Store the result directly in `filteredQuestions` so your UI can display the search results
            const data = await filterQuestionPaperQuestions(courseId, quizId, questionPaperId, filters);
            set({ filteredQuestions: data });
            return data;
        } catch (err) {
            set({ questionPaperError: err.response?.data?.error || err.message || 'Failed to filter questions' });
        } finally {
            set({ loadingQuestionPaper: false });
        }
    },




}));

export default useManageCourseStore;