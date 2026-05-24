from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

app_name = 'api'

urlpatterns = [
    
    ##============================================================================================================================================================================================
    # STUDENT ROUTES
    ##============================================================================================================================================================================================    

    
    # Student Dashboard & Stats
    url(r'student/dashboard/$', views.student_dash, name="student_dashboard_courses"), #ok

    # Course Modules & Lessons
    url(r'student/courses/$', views.user_courselist, name='user_courselist'), #ok
    url(r'student/new-courses/', views.search_new_courses, name='search_new_courses'), #ok
    url(r'student/available-courses/$', views.all_available_courses, name='all_available_courses'),
    url(r'student/courses/(?P<course_id>[0-9]+)/modules/$', views.course_modules, name='course_modules'), #ok
    url(r'student/modules/(?P<module_id>[0-9]+)/$', views.module_detail, name='module_detail'), #ok

    # Course Enrollment
    url(r'student/courses/(?P<course_id>[0-9]+)/enroll-request/$', views.enroll_request_api, name='enroll_request_api'), #ok
    url(r'student/courses/(?P<course_id>[0-9]+)/self-enroll/$', views.self_enroll_api, name='self_enroll_api'), #ok

    # Lesson Content & Completion
    url(r'student/lessons/(?P<lesson_id>[0-9]+)/$', views.lesson_detail, name='lesson_detail'), #ok
    url(r'student/lessons/(?P<lesson_id>[0-9]+)/complete/$', views.complete_lesson, name='complete_lesson'), #ok

    # View AnswerPaper
    url(r'view_answerpaper/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.view_answerpaper_api, name='api_view_answerpaper'), #ok
    
    # Course Catalog & Enrollment
    url(r'student/courses/catalog/$', views.course_catalog, name='course_catalog'),
    url(r'student/courses/enrolled/$', views.enrolled_courses, name='enrolled_courses'),
    url(r'student/courses/(?P<course_id>[0-9]+)/enroll/$', views.enroll_course, name='enroll_course'),
    
    # Badges & Insights
    url(r'student/insights/badges/$', views.user_badges, name='user_badges'),
    url(r'student/insights/achievements/$', views.user_achievements, name='user_achievements'),
    



    
    # Existing endpoints
    url(r'^questions/$', views.QuestionList.as_view(), name='questions'),
    url(r'questions/(?P<pk>[0-9]+)/$', views.QuestionDetail.as_view(),
        name='question'),
    url(r'get_courses/$', views.CourseList.as_view(), name='get_courses'),
    
    url(r'^quizzes/$', views.QuizList.as_view(), name='quizzes'), # IMP : DONT USE  ^ for this, otherwise it will not work with the teacher routes which also have quizzes in the url
    url(r'quizzes/(?P<pk>[0-9]+)/$', views.QuizDetail.as_view(), name='quiz'), # IMP :  USE  ^ for this, otherwise it will not work with the teacher routes which also have quizzes in the url
    url(r'questionpapers/$', views.QuestionPaperList.as_view(),
        name='questionpapers'),
    url(r'questionpapers/(?P<pk>[0-9]+)/$',
        views.QuestionPaperDetail.as_view(), name='questionpaper'),
    url(r'answerpapers/$', views.AnswerPaperList.as_view(),
        name='answerpapers'),
    
    
    url(r'course/(?P<pk>[0-9]+)/$',
        views.GetCourse.as_view(), name='get_course'),
    
    


    ##============================================================================================================================================================================================
    ##============================================================================================================================================================================================
    


    ##============================================================================================================================================================================================
    # COMMON ROUTES
    ##============================================================================================================================================================================================
    

    # Authentication endpoints
    url(r'auth/register/$', views.register_user, name='register'),
    url(r'auth/login/$', views.login_user, name='login'),
    url(r'auth/social-urls/$', views.get_social_auth_url, name='social_auth_url'),
    url(r'auth/social-login/$', views.social_login, name='social_login'),
    url(r'auth/logout/$', views.logout_user, name='logout'),

    # User common features
    url(r'auth/profile/$', views.user_profile, name='user_profile'),
    url(r'auth/password-change/request/$', views.request_password_change, name='request_password_change'),
    url(r'auth/password-change/confirm/$', views.confirm_password_change, name='confirm_password_change'),
    url(r'auth/moderator/status/$', views.get_moderator_status, name='get_moderator_status'),
    url(r'auth/toggle_moderator/$', views.toggle_moderator_role_api, name='toggle_moderator_role'),
    url(r'auth/password-reset/request/$', views.forgot_password, name='forgot_password'),
    url(r'auth/password-reset/confirm/$', views.confirm_forgot_password, name='confirm_forgot_password'),
    
    


    # Notification endpoints (Common for both students and teachers)
    url(r'^notifications/$', views.get_notifications, name='api_get_notifications'),
    url(r'^notifications/unread/count/$', views.get_unread_notifications_count, name='api_unread_notifications_count'),
    url(r'^notifications/(?P<message_uid>[0-9a-f-]+)/mark-read/$', views.mark_notification_read, name='api_mark_notification_read'),
    url(r'^notifications/mark-all-read/$', views.mark_all_notifications_read, name='api_mark_all_notifications_read'),
    url(r'^notifications/mark-bulk-read/$', views.mark_bulk_notifications_read, name='api_mark_bulk_notifications_read'),


    
    # Forum API endpoints
    url(r'^forum/courses/(?P<course_id>\d+)/posts/$', views.ForumPostListCreateView.as_view(), name='api_forum_post_list_create'),  #ok
    url(r'^forum/courses/(?P<course_id>\d+)/posts/(?P<id>\d+)/$', views.ForumPostDetailView.as_view(), name='api_forum_post_detail'), #ok 
    url(r'^forum/courses/(?P<course_id>\d+)/posts/(?P<post_id>\d+)/comments/$', views.ForumCommentListCreateView.as_view(), name='api_forum_comment_list_create'), #ok 
    url(r'^forum/courses/(?P<course_id>\d+)/comments/(?P<comment_id>\d+)/$', views.ForumCommentDetailView.as_view(), name='api_forum_comment_detail'), #ok

    # --- Lesson Forum Routes ---
    url(r'^forum/courses/(?P<course_id>\d+)/lesson-posts/$', views.LessonForumPostListView.as_view(), name='api_lesson_forum_post_list'), #ok
    url(r'^forum/courses/(?P<course_id>\d+)/lessons/(?P<lesson_id>\d+)/post/$', views.LessonForumPostDetailView.as_view(), name='api_lesson_forum_post_detail'), #ok
    url(r'^forum/courses/(?P<course_id>\d+)/lessons/(?P<lesson_id>\d+)/comments/$', views.LessonForumCommentListCreateView.as_view(), name='api_lesson_forum_comment_list_create'), #ok
    url(r'^forum/courses/(?P<course_id>\d+)/comments/(?P<comment_id>\d+)/$', views.LessonForumCommentDetailView.as_view(), name='api_lesson_forum_comment_detail'), #ok

    
   # Quiz Participation
    url(r'start_quiz/(?P<course_id>[0-9]+)/(?P<quiz_id>[0-9]+)/$', views.StartQuiz.as_view(), name='start_quiz'),
    url(r'validate/(?P<answerpaper_id>[0-9]+)/(?P<question_id>[0-9]+)/$', views.AnswerValidator.as_view(), name='validators'),
    url(r'quit/(?P<answerpaper_id>\d+)/$', views.QuitQuiz.as_view(), name="quit_quiz"),
    url(r'validate/(?P<uid>[0-9]+)/$', views.AnswerValidator.as_view(), name='validator'),
    url(r'student/answerpapers/(?P<answerpaper_id>[0-9]+)/submission/$', views.quiz_submission_status, name='quiz_submission_status'),



    
   
    ##============================================================================================================================================================================================
    ##============================================================================================================================================================================================
    
    
    
    
    
    
    ##============================================================================================================================================================================================
    # TEACHER ROUTES
    ##============================================================================================================================================================================================
    url(r'teacher/dashboard/$', views.teacher_dashboard, name='teacher_dashboard'), #ok
    url(r'teacher/courses/$', views.teacher_courses_list, name='teacher_courses_list'), #ok
    url(r'teacher/courses/create/$', views.teacher_create_course, name='teacher_create_course'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/$', views.teacher_get_course, name='teacher_get_course'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/update/$', views.teacher_update_course, name='teacher_update_course'), #ok
    url(r'teacher/courses/create_demo_course/$', views.CreateDemoCourseAPIView.as_view(), name="api_create_demo_course"), #ok
    url(r'^teacher/grading-systems/$', views.GradingSystemListCreateView.as_view(), name='grading-system-list-create'),  #ok
    url(r'^teacher/grading-systems/(?P<pk>[0-9]+)/$', views.GradingSystemDetailView.as_view(), name='grading-system-detail'),  #ok

    url(r'teacher/courses/(?P<course_id>[0-9]+)/enrollments/$', views.teacher_get_course_enrollments, name='teacher_get_course_enrollments'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/enrollments/approve/$', views.teacher_approve_enrollment, name='teacher_approve_enrollment'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/enrollments/reject/$', views.teacher_reject_enrollment, name='teacher_reject_enrollment'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/enrollments/remove/$', views.teacher_remove_enrollment, name='teacher_remove_enrollment'), #ok
    
    url(r'teacher/courses/(?P<course_id>[0-9]+)/send_mail/$', views.teacher_send_mail, name='teacher_send_mail'),


    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/$', views.teacher_get_course_modules, name='teacher_get_course_modules'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/create/$', views.teacher_create_module, name='teacher_create_module'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/(?P<module_id>[0-9]+)/update/$', views.teacher_update_module, name='teacher_update_module'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/(?P<module_id>[0-9]+)/delete/$', views.teacher_delete_module, name='teacher_delete_module'), #ok
    
    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/(?P<module_id>[0-9]+)/lessons/$', views.api_lesson_handler, name='api_lesson_handler'), #ok
    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/(?P<module_id>[0-9]+)/lessons/(?P<lesson_id>[0-9]+)/$', views.api_lesson_handler, name='api_lesson_handler'), #ok

    url(r'teacher/modules/(?P<module_id>[0-9]+)/design/$', views.api_design_module, name='api_design_module'),#ok
    url(r'teacher/modules/(?P<module_id>[0-9]+)/design/(?P<course_id>[0-9]+)/$', views.api_design_module, name='api_design_module'),#ok

    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/(?P<module_id>[0-9]+)/exercises/$', views.api_exercise_handler, name='api_exercise_handler'),
    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/(?P<module_id>[0-9]+)/exercises/(?P<quiz_id>[0-9]+)/$', views.api_exercise_handler, name='api_exercise_handler'),

    url(r'^teacher/courses/(?P<course_id>\d+)/modules/(?P<module_id>\d+)/quizzes/$', views.api_quiz_handler, name='api_quiz_handler_create'), #ok  # IMP USE ^ for this, otherwise it will conflict with the update route which also has quizzes in the url
    url(r'^teacher/courses/(?P<course_id>\d+)/modules/(?P<module_id>\d+)/quizzes/(?P<quiz_id>\d+)/$', views.api_quiz_handler, name='api_quiz_handler_update'), #ok #IMP USE ^ for this, otherwise it will conflict with the create route which also has quizzes in the url

    url(r'teacher/test-quiz/(?P<mode>godmode|usermode)/(?P<quiz_id>\d+)/(?P<course_id>\d+)/$', views.api_test_quiz, name='api_test_quiz'),

    url(r'^teacher/designquestionpaper/(?P<course_id>[0-9]+)/(?P<quiz_id>[0-9]+)/(?P<questionpaper_id>[0-9]+)/$', views.design_questionpaper_api, name='designquestionpaper_api'),
    url(r'^teacher/designquestionpaper/(?P<course_id>[0-9]+)/(?P<quiz_id>[0-9]+)/$', views.design_questionpaper_api, name='designquestionpaper_api'),


    url(r'teacher/courses/(?P<course_id>\d+)/designcourse/$', views.api_design_course, name='api_design_course'), #ok

    # Teacher Courses Analytics
    url(r'teacher/courses/(?P<course_id>[0-9]+)/analytics/$', views.teacher_get_course_analytics, name='teacher_get_course_analytics'), #ok


    # Teacher/TA Management
    url(r'teacher/courses/(?P<course_id>[0-9]+)/teachers/$', views.teacher_get_course_teachers, name='teacher_get_course_teachers'),
    url(r'teacher/courses/(?P<course_id>[0-9]+)/teachers/search/$', views.teacher_search_teachers, name='teacher_search_teachers'),
    url(r'teacher/courses/(?P<course_id>[0-9]+)/teachers/add/$', views.teacher_add_teachers, name='teacher_add_teachers'),
    url(r'teacher/courses/(?P<course_id>[0-9]+)/teachers/remove/$', views.teacher_remove_teachers, name='teacher_remove_teachers'),
    
    # Course MD Upload/Download
    url(r'teacher/courses/(?P<course_id>[0-9]+)/md/download/$', views.teacher_download_course_md, name='teacher_download_course_md'),
    url(r'teacher/courses/(?P<course_id>[0-9]+)/md/upload/$', views.teacher_upload_course_md, name='teacher_upload_course_md'),

    # Question Management APIs
    url(r'teacher/questions/$', views.teacher_questions_list, name='teacher_questions_list'), #ok 
    url(r'teacher/questions/(?P<question_id>[0-9]+)/$', views.teacher_get_question, name='teacher_get_question'),#ok
    url(r'teacher/questions/files/(?P<file_id>[0-9]+)/delete/$', views.delete_question_file, name='delete_question_file'), #ok
    url(r'teacher/questions/(?P<question_id>[0-9]+)/files/upload/$', views.upload_question_file, name='upload_question_file'), #ok 
    url(r'teacher/questions/(?P<question_id>[0-9]+)/update/$', views.teacher_update_question, name='teacher_update_question'), #ok
    url(r'teacher/questions/(?P<question_id>[0-9]+)/delete/$', views.teacher_delete_question, name='teacher_delete_question'), #ok
    url(r'teacher/questions/create/$', views.teacher_create_question, name='teacher_create_question'), #ok
    url(r'teacher/questions/(?P<question_id>[0-9]+)/test/$', views.teacher_test_question, name='teacher_test_question'),#ok
    url(r'teacher/questions/bulk-upload/$', views.bulk_upload_questions, name='bulk_upload_questions'),#ok
    url(r'teacher/questions/template/$', views.download_question_template, name='download_question_template'),#ok


    #  Quizzes Grading Management APIs
    url(r'teacher/grading/courses/$', views.api_get_grading_courses, name='api_get_grading_courses'),
    url(r'teacher/grading/(?P<quiz_id>\d+)/(?P<course_id>\d+)/users/$', views.api_get_quiz_users, name='api_get_quiz_users'),
    url(r'teacher/grading/(?P<quiz_id>\d+)/(?P<user_id>\d+)/(?P<course_id>\d+)/attempts/$', views.api_get_user_attempts, name='api_get_user_attempts'),
    url(r'teacher/grading/(?P<quiz_id>\d+)/(?P<user_id>\d+)/(?P<attempt_number>\d+)/(?P<course_id>\d+)/$', views.api_grade_user_attempt, name='api_grade_user_attempt'),

    #  Quizzes Regrading APIs
    
    url(r'teacher/regrading/paper/question/(?P<course_id>\d+)/(?P<questionpaper_id>\d+)/(?P<question_id>\d+)/$', views.api_regrade, name='api_regrade_by_quiz'),         # 1. Regrade specific question in a paper (Quiz wide or specific Context)
    url(r'teacher/regrading/user/(?P<course_id>\d+)/(?P<questionpaper_id>\d+)/(?P<answerpaper_id>\d+)/$', views.api_regrade, name='api_regrade_by_user'),                # 2. Regrade a specific user's attempt (AnswerPaper)
    url(r'teacher/regrading/user/question/(?P<course_id>\d+)/(?P<questionpaper_id>\d+)/(?P<answerpaper_id>\d+)/(?P<question_id>\d+)/$', views.api_regrade, name='api_regrade_by_question'), # 3. Regrade a specific question for a specific user

    #  Quizzes Monitor APIs
    url(r'teacher/monitor/$', views.monitor_papers, name="monitor_papers_list"),
    url(r'teacher/monitor/(?P<quiz_id>\d+)/(?P<course_id>\d+)/$', views.monitor_papers, name="monitor_papers"),
    url(r'teacher/monitor/(?P<quiz_id>\d+)/(?P<course_id>\d+)/(?P<attempt_number>\d+)/$', views.monitor_papers, name="monitor_papers_attempt"),
    

     # Statistics APIs
    url(r'teacher/statistics/question/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.show_statistics, name="show_statistics"),

    url(r'teacher/statistics/question/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/(?P<attempt_number>\d+)/$', views.show_statistics, name="show_statistics_attempt"),

    # Download CSV API
    url(r'teacher/download_quiz_csv/(?P<course_id>\d+)/(?P<quiz_id>\d+)/$', views.download_quiz_csv, name="download_quiz_csv"),
    url(r'teacher/upload_marks/(?P<course_id>\d+)/(?P<questionpaper_id>\d+)/$', views.upload_marks, name='upload_marks'),

    # User Data
    url(r'teacher/user_data/(?P<user_id>\d+)/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.user_data, name="user_data_detail"),
    url(r'teacher/user_data/(?P<user_id>\d+)/$', views.user_data, name="user_data"),

    # Extend Time
    url(r'teacher/extend_time/(?P<paper_id>\d+)/$', views.extend_time, name='extend_time'),

    # MicroManager / Special Attempts
    url(r'teacher/micromanager/allow_special_attempt/(?P<user_id>\d+)/(?P<course_id>\d+)/(?P<quiz_id>\d+)/$', views.allow_special_attempt, name='allow_special_attempt'),    
    url(r'teacher/micromanager/special_start/(?P<micromanager_id>\d+)/$', views.special_start, name='special_start'),    
    url(r'teacher/micromanager/special_revoke/(?P<micromanager_id>\d+)/$', views.revoke_special_attempt, name='revoke_special_attempt'),

    

    # for quiz question testing functionality
    url(r'^quiz/start/(?P<questionpaper_id>\d+)/(?P<module_id>\d+)/(?P<course_id>\d+)/$', views.api_start_quiz),  # First time start (shows intro) //  #teacher : ok
    url(r'^quiz/start/(?P<attempt_num>\d+)/(?P<module_id>\d+)/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.api_start_quiz), # Resume with attempt number // #teacher : ok
    url(r'^quiz/quit/(?P<attempt_num>\d+)/(?P<module_id>\d+)/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.api_quit_quiz, name='api_quit_quiz'),
    url(r'^quiz/complete/$', views.api_complete_quiz, name='api_complete_quiz_error'), # Route 1: Error/generic completion (no parameters required)
    url(r'^quiz/complete/(?P<attempt_num>\d+)/(?P<module_id>\d+)/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.api_complete_quiz, name='api_complete_quiz'), # Route 2: Normal completion with all parameters
    url(r'^quiz/check/(?P<q_id>\d+)/(?P<attempt_num>\d+)/(?P<module_id>\d+)/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.api_check_answer, name='api_check_answer'),
    url(r'^quiz/skip/(?P<q_id>\d+)/(?P<attempt_num>\d+)/(?P<module_id>\d+)/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.api_skip_question, name='api_skip_question'),
    url(r'^quiz/skip/(?P<q_id>\d+)/(?P<next_q>\d+)/(?P<attempt_num>\d+)/(?P<module_id>\d+)/(?P<questionpaper_id>\d+)/(?P<course_id>\d+)/$', views.api_skip_question, name='api_skip_question_with_next'),




    



    url(r'teacher/quizzes/(?P<quiz_id>[0-9]+)/questions/$', views.teacher_get_quiz_questions, name='teacher_get_quiz_questions'), #have to check if this is correct
    url(r'teacher/quizzes/(?P<quiz_id>[0-9]+)/questions/add/$', views.teacher_add_question_to_quiz, name='teacher_add_question_to_quiz'), #have to check if this is correct
    url(r'teacher/quizzes/(?P<quiz_id>[0-9]+)/questions/(?P<question_id>[0-9]+)/remove/$', views.teacher_remove_question_from_quiz, name='teacher_remove_question_from_quiz'),
    url(r'teacher/quizzes/(?P<quiz_id>[0-9]+)/questions/reorder/$', views.teacher_reorder_quiz_questions, name='teacher_reorder_quiz_questions'),
    url(r'teacher/quizzes/grouped/$', views.teacher_quizzes_grouped, name='teacher_quizzes_grouped'),
    
    url(r'teacher/modules/(?P<module_id>[0-9]+)/units/reorder/$', views.teacher_reorder_module_units, name='teacher_reorder_module_units'),
    url(r'teacher/courses/(?P<course_id>[0-9]+)/modules/reorder/$', views.teacher_reorder_course_modules, name='teacher_reorder_course_modules'),
    
    

]
    
    

urlpatterns = format_suffix_patterns(urlpatterns)
