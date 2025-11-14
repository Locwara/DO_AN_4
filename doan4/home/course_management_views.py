from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from django.contrib import messages
from django.utils.text import slugify
from django.db import transaction
import json
from datetime import timedelta
from django.http import JsonResponse
import json
from .models import (
    CodeLanguage, CodeCourse, CodeLesson, CodeEnrollment,
    CodeSubmission, CodeLessonProgress, CodeCourseTag,
    User, University
)
from .forms import CodeCourseForm, CodeLessonForm
from .decorators import premium_required

@login_required
def course_management_dashboard(request):
    """Dashboard quản lý khóa học của người tạo"""
    user_courses = CodeCourse.objects.filter(
        created_by=request.user
    ).annotate(
        total_enrollments=Count('codeenrollment'),
        avg_rating=Avg('codecourserating__rating')
    ).order_by('-created_at')
    
    # Thống kê tổng quan
    stats = {
        'total_courses': user_courses.count(),
        'published_courses': user_courses.filter(status='published').count(),
        'draft_courses': user_courses.filter(status='draft').count(),
        'total_students': CodeEnrollment.objects.filter(
            course__created_by=request.user
        ).count(),
        'total_lessons': CodeLesson.objects.filter(
            course__created_by=request.user
        ).count()
    }
    
    # Khóa học gần đây
    recent_courses = user_courses[:5]
    
    # Hoạt động gần đây
    recent_enrollments = CodeEnrollment.objects.filter(
        course__created_by=request.user
    ).select_related('user', 'course').order_by('-enrolled_at')[:10]
    
    context = {
        'stats': stats,
        'recent_courses': recent_courses,
        'recent_enrollments': recent_enrollments,
        'user_courses': user_courses
    }
    
    return render(request, 'code/management/dashboard.html', context)

@login_required
@premium_required
def course_create(request):
    """Tạo khóa học mới - YÊU CẦU PREMIUM"""
    if request.method == 'POST':
        form = CodeCourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.slug = slugify(course.title)
            
            # Ensure unique slug
            original_slug = course.slug
            counter = 1
            while CodeCourse.objects.filter(slug=course.slug).exists():
                course.slug = f"{original_slug}-{counter}"
                counter += 1
            
            course.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f'Khóa học "{course.title}" đã được tạo thành công!')
            return redirect('course_management_edit', course_id=course.id)
    else:
        form = CodeCourseForm()
    
    context = {
        'form': form,
        'page_title': 'Tạo khóa học mới'
    }
    
    return render(request, 'code/management/course_form.html', context)

@login_required
@premium_required
def course_edit(request, course_id):
    """Chỉnh sửa khóa học - YÊU CẦU PREMIUM"""
    course = get_object_or_404(
        CodeCourse, 
        id=course_id, 
        created_by=request.user
    )
    
    if request.method == 'POST':
        form = CodeCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Khóa học "{course.title}" đã được cập nhật!')
            return redirect('course_management_edit', course_id=course.id)
    else:
        form = CodeCourseForm(instance=course)
    
    # Lấy danh sách bài học
    lessons = CodeLesson.objects.filter(course=course).order_by('order_index')
    
    # Thống kê khóa học
    course_stats = {
        'enrollments': CodeEnrollment.objects.filter(course=course).count(),
        'total_lessons': lessons.count(),
        'published_lessons': lessons.filter(is_published=True).count(),
        'avg_completion': CodeEnrollment.objects.filter(
            course=course
        ).aggregate(avg=Avg('completion_percentage'))['avg'] or 0
    }
    
    context = {
        'form': form,
        'course': course,
        'lessons': lessons,
        'course_stats': course_stats,
        'page_title': f'Chỉnh sửa: {course.title}'
    }
    
    return render(request, 'code/management/course_form.html', context)

@login_required
@premium_required
def course_lessons_manage(request, course_id):
    """Quản lý bài học trong khóa học - YÊU CẦU PREMIUM"""
    course = get_object_or_404(
        CodeCourse, 
        id=course_id, 
        created_by=request.user
    )
    
    lessons = CodeLesson.objects.filter(
        course=course
    ).order_by('order_index')
    
    # Calculate statistics
    lesson_stats = {
        'total_lessons': lessons.count(),
        'published_lessons': lessons.filter(is_published=True).count(),
        'draft_lessons': lessons.filter(is_published=False).count(),
        'total_points': sum(lesson.points_reward for lesson in lessons)
    }
    
    context = {
        'course': course,
        'lessons': lessons,
        'lesson_stats': lesson_stats
    }
    
    return render(request, 'code/management/lessons_manage.html', context)

@login_required
@premium_required
def lesson_create(request, course_id):
    """Tạo bài học mới - YÊU CẦU PREMIUM"""
    course = get_object_or_404(
        CodeCourse, 
        id=course_id, 
        created_by=request.user
    )
    
    if request.method == 'POST':
        form = CodeLessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.slug = slugify(lesson.title)
            
            # Ensure unique slug within course
            original_slug = lesson.slug
            counter = 1
            while CodeLesson.objects.filter(course=course, slug=lesson.slug).exists():
                lesson.slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Set order index
            max_order = CodeLesson.objects.filter(
                course=course
            ).aggregate(max_order=Max('order_index'))['max_order'] or 0
            lesson.order_index = max_order + 1
            
            lesson.save()
            
            messages.success(request, f'Bài học "{lesson.title}" đã được tạo!')
            return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
    else:
        form = CodeLessonForm()
    
    context = {
        'form': form,
        'course': course,
        'page_title': 'Tạo bài học mới'
    }
    
    return render(request, 'code/management/lesson_form.html', context)

@login_required
@premium_required
def lesson_edit(request, course_id, lesson_id):
    """Chỉnh sửa bài học - YÊU CẦU PREMIUM"""
    course = get_object_or_404(
        CodeCourse, 
        id=course_id, 
        created_by=request.user
    )
    
    lesson = get_object_or_404(
        CodeLesson,
        id=lesson_id,
        course=course
    )
    
    if request.method == 'POST':
        form = CodeLessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bài học "{lesson.title}" đã được cập nhật!')
            return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
    else:
        form = CodeLessonForm(instance=lesson)
    
    # Thống kê bài học
    lesson_stats = {
        'attempts': CodeSubmission.objects.filter(lesson=lesson).count(),
        'completions': CodeLessonProgress.objects.filter(
            lesson=lesson, status='completed'
        ).count(),
        'avg_score': CodeSubmission.objects.filter(
            lesson=lesson
        ).aggregate(avg=Avg('score'))['avg'] or 0
    }
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'lesson_stats': lesson_stats,
        'page_title': f'Chỉnh sửa: {lesson.title}'
    }
    
    return render(request, 'code/management/lesson_form.html', context)

@login_required
def course_students(request, course_id):
    """Quản lý học viên trong khóa học"""
    course = get_object_or_404(
        CodeCourse, 
        id=course_id, 
        created_by=request.user
    )
    
    enrollments = CodeEnrollment.objects.filter(
        course=course
    ).select_related('user').order_by('-enrolled_at')
    
    # Pagination
    paginator = Paginator(enrollments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'course': course,
        'page_obj': page_obj
    }
    
    return render(request, 'code/management/course_students.html', context)

@login_required
def course_analytics(request, course_id):
    """Phân tích và báo cáo khóa học"""
    course = get_object_or_404(
        CodeCourse, 
        id=course_id, 
        created_by=request.user
    )
    
    # Thống kê tổng quan
    enrollments = CodeEnrollment.objects.filter(course=course)
    total_enrollments = enrollments.count()
    completed_enrollments = enrollments.filter(is_completed=True).count()
    completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Thống kê theo thời gian (30 ngày gần đây)
    from django.utils import timezone
    from datetime import timedelta
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    daily_enrollments = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        count = enrollments.filter(enrolled_at__date=date).count()
        daily_enrollments.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Top performing lessons
    lessons_stats = []
    for lesson in course.lessons.all():
        completions = CodeLessonProgress.objects.filter(
            lesson=lesson, status='completed'
        ).count()
        attempts = CodeSubmission.objects.filter(lesson=lesson).count()
        avg_score = CodeSubmission.objects.filter(
            lesson=lesson
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        lessons_stats.append({
            'lesson': lesson,
            'completions': completions,
            'attempts': attempts,
            'avg_score': avg_score
        })
    
    context = {
        'course': course,
        'total_enrollments': total_enrollments,
        'completion_rate': completion_rate,
        'daily_enrollments': daily_enrollments,
        'lessons_stats': lessons_stats
    }
    
    return render(request, 'code/management/course_analytics.html', context)


@login_required
def course_publish(request, course_id):
    """Publish/unpublish khóa học - Updated with JSON response support"""
    print(f"\n=== COURSE PUBLISH DEBUG START ===")
    print(f"Method: {request.method}")
    print(f"Course ID: {course_id}")
    print(f"User: {request.user}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    
    if request.method == 'POST':
        print(f"POST Data: {dict(request.POST)}")
    
    # Chỉ chấp nhận POST method
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Phương thức không hợp lệ!'})
        messages.error(request, 'Phương thức không hợp lệ!')
        return redirect('course_management_edit', course_id=course_id)
    
    try:
        print(f"Looking for course with ID {course_id} created by user {request.user.id}")
        course = get_object_or_404(
            CodeCourse, 
            id=course_id, 
            created_by=request.user
        )
        print(f"Found course: {course.title} (ID: {course.id}, Status: {course.status})")
        
        action = request.POST.get('action')
        print(f"Action: '{action}'")
        
        success_message = ""
        
        if action == 'publish':
            print(f"Processing PUBLISH action...")
            # Allow publishing without lesson requirement
            print(f"Setting course status to 'published'...")
            course.status = 'published'
            course.published_at = timezone.now()
            course.save()
            success_message = f'Khóa học "{course.title}" đã được publish thành công!'
            
        elif action == 'unpublish':
            print(f"Processing UNPUBLISH action...")
            course.status = 'draft'
            course.published_at = None
            course.save()
            success_message = f'Khóa học "{course.title}" đã được chuyển về draft!'
            
        else:
            error_msg = 'Action không hợp lệ!'
            print(f"ERROR: {error_msg}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
        
        print(f"Operation successful: {success_message}")
        
        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': success_message,
                'new_status': course.status,
                'published_at': course.published_at.isoformat() if course.published_at else None
            })
        
        # Traditional redirect for regular form submissions
        messages.success(request, success_message)
        print(f"Redirecting to course_management_edit...")
        print(f"=== COURSE PUBLISH DEBUG END ===\n")
        return redirect('course_management_edit', course_id=course.id)
        
    except Exception as e:
        error_msg = f'Có lỗi xảy ra: {str(e)}'
        print(f"ERROR in course_publish: {e}")
        import traceback
        traceback.print_exc()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        print(f"=== COURSE PUBLISH DEBUG END (ERROR) ===\n")
        return redirect('course_management_edit', course_id=course_id)

# Sửa lại phần validation JSON trong lesson_publish view

@login_required
def lesson_publish(request, course_id, lesson_id):
    """Publish/unpublish bài học - Updated with JSON response support"""
    print(f"\n=== LESSON PUBLISH DEBUG START ===")
    print(f"Method: {request.method}")
    print(f"Course ID: {course_id}")
    print(f"Lesson ID: {lesson_id}")
    print(f"User: {request.user}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Phương thức không hợp lệ!'})
        messages.error(request, 'Phương thức không hợp lệ!')
        return redirect('lesson_edit', course_id=course_id, lesson_id=lesson_id)
    
    try:
        course = get_object_or_404(CodeCourse, id=course_id, created_by=request.user)
        lesson = get_object_or_404(CodeLesson, id=lesson_id, course=course)
        
        action = request.POST.get('action')
        print(f"Action: '{action}'")
        print(f"Current lesson published state: {lesson.is_published}")
        
        success_message = ""
        
        if action == 'publish':
            print(f"Processing PUBLISH action for lesson...")
            
            # Validate lesson before publishing
            if not lesson.title or not lesson.title.strip():
                error_msg = 'Bài học cần có tên để được publish!'
                print(f"ERROR: {error_msg}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
                
            if lesson.lesson_type == 'coding':
                print(f"Validating coding lesson...")
                if not lesson.problem_statement or not lesson.test_cases:
                    error_msg = 'Bài tập coding cần có đề bài và test cases!'
                    print(f"ERROR: {error_msg}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
                    
                # Validate JSON fields
                try:
                    if lesson.test_cases:
                        if isinstance(lesson.test_cases, str):
                            parsed_test_cases = json.loads(lesson.test_cases)
                        else:
                            parsed_test_cases = lesson.test_cases
                            
                        if not isinstance(parsed_test_cases, list):
                            error_msg = 'Test cases phải là một mảng!'
                            print(f"ERROR: {error_msg}")
                            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                return JsonResponse({'success': False, 'error': error_msg})
                            messages.error(request, error_msg)
                            return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
                    
                    if lesson.hints:
                        if isinstance(lesson.hints, str):
                            parsed_hints = json.loads(lesson.hints)
                        else:
                            parsed_hints = lesson.hints
                            
                        if parsed_hints and isinstance(parsed_hints, list):
                            for i, hint in enumerate(parsed_hints):
                                if not isinstance(hint, dict) or 'title' not in hint or 'content' not in hint:
                                    error_msg = 'Mỗi hint phải có "title" và "content"!'
                                    print(f"ERROR: {error_msg}")
                                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                                        return JsonResponse({'success': False, 'error': error_msg})
                                    messages.error(request, error_msg)
                                    return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
                        
                except (json.JSONDecodeError, TypeError) as e:
                    error_msg = f'Test cases hoặc hints không đúng định dạng JSON: {str(e)}'
                    print(f"ERROR: {error_msg}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': error_msg})
                    messages.error(request, error_msg)
                    return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
            
            lesson.is_published = True
            lesson.save()
            success_message = f'Bài học "{lesson.title}" đã được publish!'
            
        elif action == 'unpublish':
            print(f"Processing UNPUBLISH action for lesson...")
            lesson.is_published = False
            lesson.save()
            success_message = f'Bài học "{lesson.title}" đã được chuyển về draft!'
            
        else:
            error_msg = 'Action không hợp lệ!'
            print(f"ERROR: {error_msg}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
        
        print(f"Operation successful: {success_message}")
        
        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': success_message,
                'is_published': lesson.is_published
            })
        
        # Traditional redirect for regular form submissions
        messages.success(request, success_message)
        print(f"Redirecting to lesson_edit...")
        print(f"=== LESSON PUBLISH DEBUG END ===\n")
        return redirect('lesson_edit', course_id=course.id, lesson_id=lesson.id)
        
    except Exception as e:
        error_msg = f'Có lỗi xảy ra: {str(e)}'
        print(f"ERROR in lesson_publish: {e}")
        import traceback
        traceback.print_exc()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        messages.error(request, error_msg)
        print(f"=== LESSON PUBLISH DEBUG END (ERROR) ===\n")
        return redirect('lesson_edit', course_id=course_id, lesson_id=lesson_id)
@login_required
@require_http_methods(["POST"])
def lesson_reorder(request, course_id):
    """Sắp xếp lại thứ tự bài học"""
    course = get_object_or_404(
        CodeCourse, 
        id=course_id, 
        created_by=request.user
    )
    
    try:
        data = json.loads(request.body)
        lesson_orders = data.get('orders', [])
        
        with transaction.atomic():
            for item in lesson_orders:
                lesson_id = item['id']
                new_order = item['order']
                
                CodeLesson.objects.filter(
                    id=lesson_id, 
                    course=course
                ).update(order_index=new_order)
        
        return JsonResponse({
            'success': True,
            'message': 'Thứ tự bài học đã được cập nhật!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
