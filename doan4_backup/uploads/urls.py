
from django.urls import path, include
from . import views
urlpatterns = [

   
    path('', views.upload_step1, name='upload_step1'),
    path('step1/', views.upload_step1, name='upload_step1'),
    path('step2/', views.upload_step2, name='upload_step2'),
    path('success/', views.upload_success, name='upload_success'),
    
    # User uploads management
    path('my-uploads/', views.my_uploads, name='my_uploads'),
    
    # API endpoints
    path('api/universities/', views.api_universities, name='api_universities'),
    path('api/courses/', views.api_courses, name='api_courses'),
    path('api/upload/', views.api_upload_document, name='api_upload_document'),
    path('api/delete/<int:document_id>/', views.api_delete_document, name='api_delete_document'),
    # uploads/urls.py
    path('api/temporary-upload/', views.api_temporary_upload, name='api_temporary_upload'),
    path('api/finalize-upload/', views.api_finalize_upload, name='api_finalize_upload'),
    # Thêm vào urls.py
    path('api/temp-files-info/', views.api_temp_files_info, name='api_temp_files_info'),
]
