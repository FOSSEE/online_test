import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import Home from './pages/Home';
import Signup from './pages/Signup';
import Signin from './pages/Signin';
import SocialAuthCallback from './pages/SocialAuthCallback';
import ForgotPassword from './pages/ForgotPassword';
import DashboardHome from './pages/DashboardHome';
import CourseStudent from './pages/student/Courses';
import Quiz from './pages/Quiz';
import Submission from './pages/Submission';

import AddNewCourseStudent from './pages/student/AddCourse';
import ManageCourseStudent from './pages/student/ManageCourse';
import Lesson from './pages/student/Lesson';
import ViewAnswerPaper from './pages/student/ViewAnswerPaper';
import Insights from './pages/student/Insights';
import Profile from './pages/Profile';

import DashboardTeachers from './pages/teacher/DashboardTeachers';
import AddCourse from './pages/teacher/AddCourse';
import Courses from './pages/teacher/Courses';
import ManageCourse from './pages/teacher/ManageCourse';
import TeacherQuizzes from './pages/teacher/TeacherQuizzes';
import Questions from './pages/teacher/Questions';
import PrivateRoute from './components/auth/PrivateRoute';
import PublicRoute from './components/auth/PublicRoute';
import GradingSystems from './pages/teacher/GradingSystems';
import UploadQuestion from './pages/teacher/UploadQuestion';
import TestQuestion from './pages/teacher/TestQuestion';
import Settings from './pages/Settings';
import Notifications from './pages/Notifications';
import ThemeController from './components/layout/ThemeController';


function App() {
  return (
    <Router>
      <ThemeController />
      <Routes>
        {/* Public-only routes: redirect authenticated users to their dashboard */}
        <Route element={<PublicRoute />}>
          <Route path="/" element={<Home />} />
        </Route>
        <Route path="/signup" element={<Signup />} />
        <Route path="/signin" element={<Signin />} />
        <Route path="/auth/callback" element={<SocialAuthCallback />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />

        {/* Protected Routes */}
        <Route element={<PrivateRoute />}>
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/notifications" element={<Notifications />} />

          <Route path="/dashboard" element={<DashboardHome />} />
          <Route path="/courses" element={<CourseStudent />} />
          <Route path="/add-course" element={<AddNewCourseStudent />} />
          <Route path="/courses/:courseId/manage" element={<ManageCourseStudent />} />
          <Route path="/student/courses/:courseId/view-answerpaper/:questionPaperId" element={<ViewAnswerPaper />} />


          <Route path="/lessons/:lessonId" element={<Lesson />} />
          <Route path="/courses/:courseId/quizzes/:quizId" element={<Quiz />} />
          <Route path="/quizzes/:quizId" element={<Quiz />} />
          <Route path="/answerpapers/:answerpaperId/submission" element={<Submission />} />
          <Route path="/insights" element={<Insights />} />

          {/* Legacy routes for backward compatibility */}

          <Route path="/quiz" element={<Quiz />} />
          <Route path="/lesson" element={<Lesson />} />
          <Route path="/submission" element={<Submission />} />
        </Route>

        {/* Teacher Routes */}
        <Route element={<PrivateRoute />}>
          <Route path="/teacher/dashboard" element={<DashboardTeachers />} />

          <Route path="/teacher/grading-systems" element={<GradingSystems />} />
          <Route path="/teacher/courses" element={<Courses />} />
          <Route path="/teacher/courses/:courseId/manage" element={<ManageCourse />} />
          <Route path="/teacher/courses/:courseId/edit" element={<AddCourse />} />
          <Route path="/teacher/questions" element={<Questions />} />
          <Route path="/teacher/upload-question" element={<UploadQuestion />} />
          <Route path="/teacher/test-question/:questionpaperId/:moduleId/:courseId" element={<TestQuestion />} />

          <Route path="/teacher/quizzes" element={<TeacherQuizzes />} />

        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
