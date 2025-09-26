from django.urls import path
from . import code_views, course_management_views

urlpatterns = [
    # Dashboard
    path('dashboard/', code_views.code_dashboard, name='code_dashboard'),
    
    # Course Management Dashboard
    path('manage/', course_management_views.course_management_dashboard, name='course_management_dashboard'),
    path('manage/create/', course_management_views.course_create, name='course_management_create'),
    path('manage/<int:course_id>/', course_management_views.course_edit, name='course_management_edit'),
    path('manage/<int:course_id>/lessons/', course_management_views.course_lessons_manage, name='course_lessons_manage'),
    path('manage/<int:course_id>/students/', course_management_views.course_students, name='course_students'),
    path('manage/<int:course_id>/analytics/', course_management_views.course_analytics, name='course_analytics'),
    path('manage/<int:course_id>/publish/', course_management_views.course_publish, name='course_publish'),
    
    # Lesson Management
    path('manage/<int:course_id>/lessons/create/', course_management_views.lesson_create, name='lesson_create'),
    path('manage/<int:course_id>/lessons/<int:lesson_id>/', course_management_views.lesson_edit, name='lesson_edit'),
    path('manage/<int:course_id>/lessons/<int:lesson_id>/publish/', course_management_views.lesson_publish, name='lesson_publish'),
    path('manage/<int:course_id>/lessons/reorder/', course_management_views.lesson_reorder, name='lesson_reorder'),
    
    # Course Learning (Student View)
    path('', code_views.code_courses_list, name='code_courses_list'),
    path('courses/<slug:course_slug>/', code_views.code_course_detail, name='code_course_detail'),
    path('courses/<slug:course_slug>/enroll/', code_views.code_course_enroll, name='code_course_enroll'),
    
    # Lesson & Code Editor
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/', code_views.code_lesson_detail, name='code_lesson_detail'),
    
    # API Endpoints
    path('api/execute/', code_views.code_execute_api, name='code_execute_api'),
    path('api/submit/', code_views.code_submit_api, name='code_submit_api'),
]
