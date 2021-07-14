import { createRouter, createWebHistory } from 'vue-router';
import CourseDetail from '../components/course/CourseDetail.vue';
import Course from '../components/course/Course.vue'

const routes = [
  {
    path: '/exam/manage/course/detail/:course_id',
    name: 'course_detail',
    component: CourseDetail,
  },
  {
    path: '/exam/manage/mycourses',
    name: 'courses',
    component: Course,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
