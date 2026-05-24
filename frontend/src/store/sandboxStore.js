import { create } from 'zustand';
import { testQuiz } from '../api/api';
import { useNavigate, useParams } from 'react-router-dom';



export const useSandboxStore = create((set) => ({
  isGenerating: false,
  error: null,

  // mode = 'usermode' or 'godmode'
  generateTestSandbox: async (mode, quizId, courseId, navigate) => {
    set({ isGenerating: true, error: null });
    
    try {
      const response = await testQuiz(mode, quizId, courseId);
      
      const trialCourseId = response.trial_course_id;
      const trialQuizId = response.trial_quiz_id;

      if (trialCourseId && trialQuizId) {
        // Automatically navigate the teacher directly into the generated standard Quiz route!
        navigate(`/courses/${trialCourseId}/quizzes/${trialQuizId}`);
      } else {
        set({ error: "Invalid API response: Missing sandbox IDs." });
      }
    } catch (err) {
      console.error("Sandbox generation failed:", err);
      const errorMessage = err.response?.data?.error || "Error generating test environment.";
      set({ error: errorMessage });
      alert(errorMessage);
    } finally {
      set({ isGenerating: false });
    }
  },

  clearError: () => set({ error: null })
}));