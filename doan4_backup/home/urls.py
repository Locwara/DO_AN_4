from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_login_view, name='home_login'),
    
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('authenticate/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard sau khi đăng nhập
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API endpoints để kiểm tra tính khả dụng
    path('api/check-username/', views.check_username_availability, name='check_username'),
    path('api/check-email/', views.check_email_availability, name='check_email'),
    
    # API endpoints cho universities và courses
    path('api/university/<int:university_id>/courses/', views.university_courses_view, name='university_courses'),
    path('api/course/<int:course_id>/documents/', views.course_documents_view, name='course_documents'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    
    # Password Management URLs
    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    
    # Document URLs
    path('documents/<int:document_id>/view/', views.document_view, name='document_view'),
    path('documents/<int:document_id>/download/', views.document_download, name='document_download'),
    path('documents/search/', views.documents_search, name='documents_search'),
    path('documents/', views.documents_list, name='documents_list'),
    path('documents/<int:document_id>/like/', views.document_like, name='document_like'),
    
    # Chat URLs
    path('chat/', views.chat_rooms_list, name='chat_rooms_list'),
    path('chat/create/', views.chat_room_create, name='chat_room_create'),
    path('chat/room/<int:room_id>/', views.chat_room_detail, name='chat_room_detail'),
    path('chat/room/<int:room_id>/edit/', views.chat_room_edit, name='chat_room_edit'),
    path('chat/room/<int:room_id>/delete/', views.chat_room_delete, name='chat_room_delete'),
    path('chat/room/<int:room_id>/leave/', views.chat_room_leave, name='chat_room_leave'),
    path('chat/room/<int:room_id>/invite/', views.chat_room_invite, name='chat_room_invite'),

    path('api/chat/room/<int:room_id>/send/', views.chat_send_message, name='chat_send_message'),
    path('api/chat/room/<int:room_id>/messages/', views.chat_load_messages, name='chat_load_messages'),
    path('api/chat/room/<int:room_id>/members/', views.chat_room_members, name='chat_room_members'),
    
    # NEW Chat API endpoints
    path('api/chat/room/<int:room_id>/search-documents/', views.chat_search_documents, name='chat_search_documents'),
    path('api/chat/room/<int:room_id>/upload-file/', views.chat_send_message, name='chat_upload_file'),  # Same endpoint, different content-type
    path('api/chat/room/<int:room_id>/files/', views.chat_room_files, name='chat_room_files'),
    path('api/chat/room/<int:room_id>/shared-documents/', views.chat_room_shared_documents, name='chat_room_shared_documents'),
    path('api/chat/room/<int:room_id>/statistics/', views.chat_room_statistics, name='chat_room_statistics'),
    
    # File download
    path('chat/room/<int:room_id>/file/<int:message_id>/download/', views.chat_file_download, name='chat_file_download'),
    # AI Image Solver URLs
    path('ai/', views.ai_image_solver_view, name='ai_image_solver'),
    path('ai/solve/', views.ai_solve_image_api, name='ai_solve_image'),
    path('ai/solve-file/', views.ai_solve_file_api, name='ai_solve_file'),  # NEW URL for file upload
    path('ai/chat/', views.ai_continue_conversation_api, name='ai_continue_conversation'),
    path('ai/solution/<int:solution_id>/', views.ai_solution_detail_view, name='ai_solution_detail'),
    path('ai/history/', views.ai_solutions_history_view, name='ai_solutions_history'),
    path('ai/text-chat/', views.ai_text_chat_api, name='ai_text_chat'),
    # Trong phần urlpatterns
    path('ai/conversation/<int:conversation_id>/', views.get_conversation_api, name='get_conversation'),
    path('ai/search-documents/', views.ai_search_documents_api, name='ai_search_documents'),
    path('ai/search-chat-rooms/', views.ai_search_chat_rooms_api, name='ai_search_chat_rooms'),
    # Report API
    path('api/user-report/', views.user_report_api, name='user_report'),
]