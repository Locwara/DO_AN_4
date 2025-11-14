from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .premium_views import check_download_limit, check_course_enrollment_limit

def premium_required(view_func):
    """Decorator yêu cầu premium"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Vui lòng đăng nhập!')
            return redirect('login')
        
        if not request.user.is_premium:
            messages.warning(request, 'Tính năng này yêu cầu tài khoản Premium!')
            return redirect('premium_upgrade')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def check_download_restriction(view_func):
    """Decorator kiểm tra giới hạn download"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Vui lòng đăng nhập!')
            return redirect('login')
        
        can_download, count = check_download_limit(request.user)
        
        if not can_download:
            messages.warning(
                request, 
                f'Bạn đã tải {count} tài liệu hôm nay. '
                f'Nâng cấp Premium để tải không giới hạn!'
            )
            return redirect('premium_upgrade')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def check_course_restriction(view_func):
    """Decorator kiểm tra giới hạn đăng ký khóa học"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Vui lòng đăng nhập!')
            return redirect('login')
        
        can_enroll, count = check_course_enrollment_limit(request.user)
        
        if not can_enroll:
            messages.warning(
                request,
                f'Bạn đã đăng ký {count} khóa học. '
                f'Nâng cấp Premium để đăng ký không giới hạn!'
            )
            return redirect('premium_upgrade')
        
        return view_func(request, *args, **kwargs)
    return wrapper
