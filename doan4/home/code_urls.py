from django.urls import path
from . import code_views

urlpatterns = [
    # Dashboard
    path('dashboard/', code_views.code_dashboard, name='code_dashboard'),
    
    # Course Management
    path('', code_views.code_courses_list, name='code_courses_list'),
    path('courses/<slug:course_slug>/', code_views.code_course_detail, name='code_course_detail'),
    path('courses/<slug:course_slug>/enroll/', code_views.code_course_enroll, name='code_course_enroll'),
    
    # Lesson & Code Editor
    path('courses/<slug:course_slug>/lessons/<slug:lesson_slug>/', code_views.code_lesson_detail, name='code_lesson_detail'),
    
    # API Endpoints
    path('api/execute/', code_views.code_execute_api, name='code_execute_api'),
    path('api/submit/', code_views.code_submit_api, name='code_submit_api'),
]
