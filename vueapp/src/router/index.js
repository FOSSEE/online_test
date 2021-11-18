import { createRouter, createWebHistory } from 'vue-router';
import CourseContents from '../components/course/CourseContents.vue';
import CourseEnrollments from '../components/course/CourseEnrollments.vue';
import Course from '../components/course/Course.vue'
import CourseTeachers from '../components/course/CourseTeachers.vue'
import CourseSendMail from '../components/course/CourseSendMail.vue'
import CourseStatistics from '../components/course/CourseStatistics.vue'
import ModeratorDashboard from '../components/course/ModeratorDashboard.vue';
import AddCourse from '../components/course/AddCourse'
import CourseForum from '../components/forum/CourseForum'
import PostComments from '../components/forum/PostComments'

const routes = [
  {
    path: '/exam/manage/course/detail/:course_id',
    name: 'course_contents',
    component: CourseContents,
  },
  {
    path: '/exam/manage/course/enrollments/:course_id',
    name: 'course_enrollments',
    component: CourseEnrollments,
  },
  {
    path: '/exam/manage/course/view/teachers/:course_id',
    name: 'course_teachers',
    component: CourseTeachers,
  },
  {
    path: '/exam/manage/course/send_mail/:course_id',
    name: 'course_send_mail',
    component: CourseSendMail,
  },
  {
    path: '/exam/manage/course/statistics/:course_id',
    name: 'course_statistics',
    component: CourseStatistics,
  },
  {
    path: '/exam/manage/mycourses',
    name: 'courses',
    component: Course,
  },
  {
    path: '/exam/manage/moderator_dashboard/',
    name: 'moderator_dashboard',
    component: ModeratorDashboard,
  },
  {
    path: '/exam/manage/addcourse/',
    name: 'add_course',
    component: AddCourse
  },
  {
    path: '/forum/courseforum/:course_id/',
    name: 'course_forum',
    component: CourseForum,
  },
  {
    path: '/forum/courseforum/:course_id/post/:post_id/',
    name: 'post_comments',
    component: PostComments,
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
