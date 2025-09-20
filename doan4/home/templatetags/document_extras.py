from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.templatetags.static import static
from django.utils import timezone
from django.conf import settings
import os

register = template.Library()

@register.filter
def document_type_icon(document_type):
    """Trả về icon FontAwesome cho loại tài liệu"""
    icons = {
        'textbook': 'fas fa-book',
        'exercise': 'fas fa-pencil-alt', 
        'exam': 'fas fa-file-alt',
        'thesis': 'fas fa-graduation-cap',
        'lecture': 'fas fa-chalkboard-teacher',
        'other': 'fas fa-file'
    }
    return icons.get(document_type, 'fas fa-file')

@register.filter
def document_type_name(document_type):
    """Trả về tên tiếng Việt của loại tài liệu"""
    names = {
        'textbook': 'Sách giáo khoa',
        'exercise': 'Bài tập', 
        'exam': 'Đề thi',
        'thesis': 'Luận văn',
        'lecture': 'Bài giảng',
        'other': 'Khác'
    }
    return names.get(document_type, 'Khác')

@register.filter
def document_type_color(document_type):
    """Trả về màu cho badge loại tài liệu"""
    colors = {
        'textbook': '#6366f1',
        'exercise': '#10b981',
        'exam': '#f59e0b', 
        'thesis': '#8b5cf6',
        'lecture': '#06b6d4',
        'other': '#6b7280'
    }
    return colors.get(document_type, '#6b7280')

@register.simple_tag
def get_document_thumbnail(document):
    """Trả về URL thumbnail của tài liệu hoặc placeholder"""
    if document.thumbnail:
        return document.thumbnail.url
    else:
        # Trả về placeholder dựa trên loại tài liệu
        placeholder_map = {
            'textbook': 'images/placeholders/textbook.svg',
            'exercise': 'images/placeholders/exercise.svg', 
            'exam': 'images/placeholders/exam.svg',
            'thesis': 'images/placeholders/thesis.svg',
            'lecture': 'images/placeholders/lecture.svg',
            'other': 'images/placeholders/document.svg'
        }
        placeholder = placeholder_map.get(document.document_type, 'images/placeholders/document.svg')
        return static(placeholder)

@register.filter
def status_badge_class(status):
    """Trả về class CSS cho badge trạng thái"""
    classes = {
        'approved': 'status-approved',
        'pending': 'status-pending',
        'rejected': 'status-rejected'
    }
    return classes.get(status, 'status-pending')

@register.filter
def status_name(status):
    """Trả về tên tiếng Việt của trạng thái"""
    names = {
        'approved': 'Đã duyệt',
        'pending': 'Chờ duyệt', 
        'rejected': 'Từ chối'
    }
    return names.get(status, 'Chưa xác định')

@register.filter
def status_icon(status):
    """Trả về icon cho trạng thái"""
    icons = {
        'approved': 'fas fa-check',
        'pending': 'fas fa-clock',
        'rejected': 'fas fa-times'
    }
    return icons.get(status, 'fas fa-question')

@register.simple_tag
def document_stats_html(document):
    """Tạo HTML hiển thị thống kê tài liệu"""
    return format_html(
        '<div class="document-stats-inline">'
        '<span class="stat-item"><i class="fas fa-eye"></i> {}</span>'
        '<span class="stat-item"><i class="fas fa-download"></i> {}</span>'
        '<span class="stat-item"><i class="fas fa-heart"></i> {}</span>'
        '</div>',
        document.view_count,
        document.download_count, 
        document.like_count
    )

@register.filter
def time_since_upload(created_at):
    """Tính thời gian đã trải qua kể từ khi upload"""
    now = timezone.now()
    diff = now - created_at
    
    if diff.days > 7:
        return created_at.strftime('%d/%m/%Y')
    elif diff.days > 0:
        return f'{diff.days} ngày trước'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} giờ trước'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} phút trước'
    else:
        return 'Vừa mới'

@register.filter
def file_extension(filename):
    """Trả về phần mở rộng của file"""
    if filename:
        return os.path.splitext(filename)[1].upper().replace('.', '')
    return ''

@register.filter
def format_file_size(size_bytes):
    """Format kích thước file"""
    if not size_bytes:
        return 'N/A'
    
    size_bytes = int(size_bytes)
    
    if size_bytes >= 1024 * 1024 * 1024:  # GB
        return f'{size_bytes / (1024**3):.1f} GB'
    elif size_bytes >= 1024 * 1024:  # MB
        return f'{size_bytes / (1024**2):.1f} MB'
    elif size_bytes >= 1024:  # KB
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes} B'

@register.simple_tag
def user_can_download(user, document):
    """Kiểm tra user có thể tải tài liệu không"""
    # Premium user có thể tải tất cả
    if user.is_premium:
        return True
    
    # Người upload có thể tải tài liệu của mình
    if document.uploaded_by == user:
        return True
    
    # Kiểm tra giới hạn download hàng ngày cho user thường
    from home.models import DocumentDownload  # Import trong function để tránh circular import
    today_downloads = DocumentDownload.objects.filter(
        user=user,
        created_at__date=timezone.now().date()
    ).count()
    
    return today_downloads < 5  # Giới hạn 5 lần/ngày

@register.filter
def truncate_smart(text, max_length=100):
    """Cắt text thông minh tại ranh giới từ"""
    if not text or len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    
    # Tìm vị trí khoảng trắng cuối cùng
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Chỉ cắt tại từ nếu không quá ngắn
        truncated = truncated[:last_space]
    
    return truncated + '...'

@register.simple_tag
def get_university_logo(university):
    """Trả về URL logo trường hoặc placeholder"""
    if university.logo:
        return university.logo.url
    return static('images/placeholders/university.svg')

@register.inclusion_tag('tags/document_card.html')
def document_card(document, show_university=True, show_stats=True):
    """Render card tài liệu"""
    return {
        'document': document,
        'show_university': show_university,
        'show_stats': show_stats,
    }

@register.inclusion_tag('tags/document_list.html')
def document_list(documents, title="Danh sách tài liệu", show_pagination=True):
    """Render danh sách tài liệu"""
    return {
        'documents': documents,
        'title': title,
        'show_pagination': show_pagination,
    }

@register.simple_tag(takes_context=True)
def is_document_liked(context, document):
    """Kiểm tra user hiện tại có thích tài liệu không"""
    user = context['user']
    if not user.is_authenticated:
        return False
    
    from home.models import DocumentLike
    return DocumentLike.objects.filter(
        document=document,
        user=user
    ).exists()

@register.filter
def mul(value, arg):
    """Phép nhân trong template"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Tính phần trăm"""
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0