from django.contrib import admin
from .models import *

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'university', 'course', 'uploaded_by', 'status', 'created_at']
    list_filter = ['status', 'document_type', 'university', 'created_at']
    search_fields = ['title', 'description', 'uploaded_by__username']
    list_editable = ['status']
    readonly_fields = ['view_count', 'download_count', 'like_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'description', 'file_path', 'thumbnail')
        }),
        ('Phân loại', {
            'fields': ('university', 'course', 'document_type', 'academic_year', 'semester')
        }),
        ('Trạng thái', {
            'fields': ('status', 'is_public', 'admin_notes')
        }),
        ('Thống kê', {
            'fields': ('view_count', 'download_count', 'like_count'),
            'classes': ('collapse',)
        }),
        ('AI Features', {
            'fields': ('ai_summary', 'ai_keywords'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('university', 'course', 'uploaded_by')

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'short_name']
    list_editable = ['is_active']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'university', 'created_by', 'is_active']
    list_filter = ['university', 'is_active']
    search_fields = ['code', 'name']
    list_editable = ['is_active']