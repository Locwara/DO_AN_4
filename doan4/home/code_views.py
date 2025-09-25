from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib import messages
from django.utils.text import slugify
from django.db import transaction
import json
import time
import uuid
import tempfile
import subprocess
from datetime import timedelta

from .models import (
    CodeLanguage, CodeCourse, CodeLesson, CodeEnrollment,
    CodeSubmission, CodeLessonProgress, CodeExecutionSession,
    CodeHint, CodeDiscussion, CodeReviewRequest, UserCodingProfile,
    User, University
)

# Code Courses Views
@login_required
def code_courses_list(request):
    """List all coding courses"""
    courses = CodeCourse.objects.filter(
        status='published'
    ).select_related(
        'language', 'created_by', 'university'
    ).annotate(
        avg_rating=Avg('codecourserating__rating')
    ).order_by('-is_featured', '-enrollment_count')
    
    # Filters
    language_id = request.GET.get('language')
    difficulty = request.GET.get('difficulty')
    university_id = request.GET.get('university')
    search = request.GET.get('search')
    
    if language_id:
        courses = courses.filter(language_id=language_id)
    if difficulty:
        courses = courses.filter(difficulty=difficulty)
    if university_id:
        courses = courses.filter(university_id=university_id)
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    languages = CodeLanguage.objects.filter(is_active=True)
    universities = University.objects.filter(is_active=True)
    
    # User's enrollments
    user_enrollments = set()
    if request.user.is_authenticated:
        user_enrollments = set(
            CodeEnrollment.objects.filter(
                user=request.user
            ).values_list('course_id', flat=True)
        )
    
    context = {
        'page_obj': page_obj,
        'languages': languages,
        'universities': universities,
        'user_enrollments': user_enrollments,
        'current_filters': {
            'language': language_id,
            'difficulty': difficulty,
            'university': university_id,
            'search': search,
        }
    }
    
    return render(request, 'code/courses_list.html', context)


@login_required
def code_course_detail(request, course_slug):
    """Course detail with lessons list"""
    course = get_object_or_404(
        CodeCourse,
        slug=course_slug,
        status='published'
    )
    
    # Check if user is enrolled
    enrollment = CodeEnrollment.objects.filter(
        user=request.user,
        course=course
    ).first()
    
    # Get lessons with progress
    lessons = CodeLesson.objects.filter(
        course=course,
        is_published=True
    ).order_by('order_index')
    
    # Add progress info if enrolled
    lessons_with_progress = []
    for lesson in lessons:
        lesson_data = {
            'lesson': lesson,
            'is_unlocked': True,  # For now, all lessons are unlocked
            'progress': None
        }
        
        if enrollment:
            progress = CodeLessonProgress.objects.filter(
                enrollment=enrollment,
                lesson=lesson
            ).first()
            lesson_data['progress'] = progress
        
        lessons_with_progress.append(lesson_data)
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'lessons_with_progress': lessons_with_progress,
        'total_lessons': lessons.count(),
        'completed_lessons': 0 if not enrollment else lessons.filter(
            codelessonprogress__enrollment=enrollment,
            codelessonprogress__status='completed'
        ).count()
    }
    
    return render(request, 'code/course_detail.html', context)


@login_required
@require_http_methods(["POST"])
def code_course_enroll(request, course_slug):
    """Enroll in a course"""
    course = get_object_or_404(CodeCourse, slug=course_slug, status='published')
    
    # Check if already enrolled
    if CodeEnrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, f'Bạn đã đăng ký khóa học "{course.title}" rồi!')
        return redirect('code_course_detail', course_slug=course.slug)
    
    # Check premium requirement
    if course.requires_premium and not request.user.is_premium:
        messages.error(request, 'Khóa học này yêu cầu tài khoản Premium!')
        return redirect('code_course_detail', course_slug=course.slug)
    
    # Create enrollment
    enrollment = CodeEnrollment.objects.create(
        user=request.user,
        course=course
    )
    
    # Update course enrollment count
    course.enrollment_count += 1
    course.save()
    
    # Create or update user coding profile
    profile, created = UserCodingProfile.objects.get_or_create(
        user=request.user,
        defaults={'preferred_language': course.language}
    )
    if not created:
        profile.total_courses_enrolled += 1
        profile.save()
    
    messages.success(request, f'Đăng ký khóa học "{course.title}" thành công!')
    return redirect('code_course_detail', course_slug=course.slug)


@login_required
def code_lesson_detail(request, course_slug, lesson_slug):
    """Main code editor view for a lesson"""
    course = get_object_or_404(CodeCourse, slug=course_slug, status='published')
    lesson = get_object_or_404(
        CodeLesson,
        course=course,
        slug=lesson_slug,
        is_published=True
    )
    
    # Check enrollment
    enrollment = get_object_or_404(
        CodeEnrollment,
        user=request.user,
        course=course
    )
    
    # Get or create lesson progress
    progress, created = CodeLessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={'status': 'in_progress', 'started_at': timezone.now()}
    )
    
    if created or progress.status == 'not_started':
        progress.status = 'in_progress'
        progress.started_at = timezone.now()
        progress.save()
    
    # Get user's latest submission
    latest_submission = CodeSubmission.objects.filter(
        user=request.user,
        lesson=lesson
    ).order_by('-created_at').first()
    
    # Get hints (progressive based on attempts)
    available_hints = []
    if progress.attempts_count >= 3:
        hints = CodeHint.objects.filter(
            lesson=lesson,
            show_after_attempts__lte=progress.attempts_count
        ).order_by('order_index')
        available_hints = list(hints)
    
    # Get lesson discussions
    discussions = CodeDiscussion.objects.filter(
        lesson=lesson,
        parent=None  # Top-level discussions only
    ).select_related('user').order_by('-upvotes', '-created_at')[:5]
    
    context = {
        'course': course,
        'lesson': lesson,
        'enrollment': enrollment,
        'progress': progress,
        'latest_submission': latest_submission,
        'available_hints': available_hints,
        'discussions': discussions,
        'starter_code': lesson.starter_code or f'# {course.language.display_name} starter code\n# Write your solution here\n',
    }
    
    return render(request, 'code/lesson_editor.html', context)


# Code Execution API
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def code_execute_api(request):
    """Execute code and return results"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        language_id = data.get('language_id')
        lesson_id = data.get('lesson_id')
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'No code provided'
            })
        
        # Get language
        language = get_object_or_404(CodeLanguage, id=language_id, is_active=True)
        
        # Get lesson (optional)
        lesson = None
        if lesson_id:
            lesson = get_object_or_404(CodeLesson, id=lesson_id)
        
        # Execute code safely
        execution_result = execute_code_safely(
            code=code,
            language=language,
            lesson=lesson
        )
        
        return JsonResponse({
            'success': True,
            'result': execution_result
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Execution error: {str(e)}'
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def code_submit_api(request):
    """Submit code for grading and AI review"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        lesson_id = data.get('lesson_id')
        language_id = data.get('language_id')
        
        if not code or not lesson_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            })
        
        # Get lesson and language
        lesson = get_object_or_404(CodeLesson, id=lesson_id)
        language = get_object_or_404(CodeLanguage, id=language_id)
        
        # Get enrollment
        enrollment = get_object_or_404(
            CodeEnrollment,
            user=request.user,
            course=lesson.course
        )
        
        # Count submission attempts
        submission_count = CodeSubmission.objects.filter(
            user=request.user,
            lesson=lesson
        ).count() + 1
        
        # Execute code with test cases
        execution_result = execute_code_with_tests(
            code=code,
            language=language,
            lesson=lesson
        )
        
        # Create submission
        submission = CodeSubmission.objects.create(
            user=request.user,
            lesson=lesson,
            enrollment=enrollment,
            submitted_code=code,
            language=language,
            status=execution_result['status'],
            execution_output=execution_result.get('output', ''),
            error_message=execution_result.get('error', ''),
            execution_time=execution_result.get('execution_time', 0),
            memory_used=execution_result.get('memory_used', 0),
            test_results=execution_result.get('test_results', []),
            tests_passed=execution_result.get('tests_passed', 0),
            tests_total=execution_result.get('tests_total', 0),
            score=execution_result.get('score', 0),
            submission_count=submission_count,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Update lesson progress
        progress = CodeLessonProgress.objects.get(
            enrollment=enrollment,
            lesson=lesson
        )
        progress.attempts_count += 1
        progress.last_attempt_at = timezone.now()
        
        # Check if passed
        if execution_result.get('score', 0) >= 80:  # 80% to pass
            progress.status = 'completed'
            progress.completed_at = timezone.now()
            progress.points_earned = lesson.points_reward
            progress.best_score = max(progress.best_score, execution_result.get('score', 0))
        
        progress.save()
        
        # Get AI feedback (async in background)
        if lesson.ai_prompt_template:
            ai_feedback = get_ai_code_feedback(
                code=code,
                lesson=lesson,
                test_results=execution_result.get('test_results', []),
                score=execution_result.get('score', 0)
            )
            submission.ai_feedback = ai_feedback
            submission.save()
        
        return JsonResponse({
            'success': True,
            'submission': {
                'id': submission.id,
                'status': submission.status,
                'score': submission.score,
                'tests_passed': submission.tests_passed,
                'tests_total': submission.tests_total,
                'execution_time': submission.execution_time,
                'test_results': submission.test_results,
                'ai_feedback': submission.ai_feedback,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Submission error: {str(e)}'
        })


# Utility Functions
import requests
import time
import base64
from django.conf import settings

def execute_code_safely(code, language, lesson=None, timeout=10):
    """Execute code using Judge0 API"""
    try:
        # Judge0 language IDs
        language_ids = {
            'python': 71,      # Python 3.8.1
            'javascript': 63,  # JavaScript (Node.js 12.14.0)
            'java': 62,        # Java (OpenJDK 13.0.1)
            'cpp': 54,         # C++ (GCC 9.2.0)
            'c': 50,           # C (GCC 9.2.0)
            'csharp': 51,      # C# (Mono 6.6.0.161)
            'go': 60,          # Go (1.13.5)
            'rust': 73,        # Rust (1.40.0)
            'php': 68,         # PHP (7.4.1)
            'ruby': 72,        # Ruby (2.7.0)
        }
        
        lang_id = language_ids.get(language.name.lower(), 71)  # Default to Python
        
        # Judge0 API configuration
        api_key = "9a99780a04msh553f9e3886a82b4p1390b1jsnb8610d7b3942"
        base_url = "https://judge0-ce.p.rapidapi.com"
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        
        # Prepare submission payload
        payload = {
            "language_id": lang_id,
            "source_code": code,  # Send as plain text, Judge0 will handle encoding
            "stdin": "",
        }
        
        start_time = time.time()
        
        # Submit code for execution
        submission_url = f"{base_url}/submissions"
        response = requests.post(submission_url, json=payload, headers=headers)
        
        if response.status_code != 201:
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': f'Failed to submit code: {response.text}'
            }
        
        token = response.json()['token']
        
        # Poll for result
        get_url = f"{base_url}/submissions/{token}"
        max_attempts = 20  # Max 20 seconds wait
        
        for attempt in range(max_attempts):
            result_response = requests.get(get_url, headers=headers)
            
            if result_response.status_code != 200:
                return {
                    'status': 'error',
                    'output': '',
                    'execution_time': time.time() - start_time,
                    'error': f'Failed to get result: {result_response.text}'
                }
            
            result = result_response.json()
            status_id = result['status']['id']
            
            # Status codes: 1=In Queue, 2=Processing, 3=Accepted, 4=Wrong Answer, 5=Time Limit Exceeded, 6=Compilation Error, etc.
            if status_id in [1, 2]:  # Still processing
                time.sleep(1)
                continue
            
            execution_time = time.time() - start_time
            
            # FIXED: Improved Base64 decode with proper error handling
            def safe_decode(encoded_data):
                if not encoded_data:
                    return ''
                
                # If it's already a string (not base64), return as-is
                if isinstance(encoded_data, str):
                    try:
                        # Try to decode as base64
                        decoded_bytes = base64.b64decode(encoded_data)
                        return decoded_bytes.decode('utf-8', errors='replace')
                    except Exception:
                        # If base64 decode fails, assume it's plain text
                        return encoded_data
                
                try:
                    # Handle bytes input
                    if isinstance(encoded_data, bytes):
                        return encoded_data.decode('utf-8', errors='replace')
                    
                    # Fix base64 padding if needed
                    encoded_str = str(encoded_data).strip()
                    missing_padding = len(encoded_str) % 4
                    if missing_padding:
                        encoded_str += '=' * (4 - missing_padding)
                    
                    # Decode base64
                    decoded_bytes = base64.b64decode(encoded_str)
                    return decoded_bytes.decode('utf-8', errors='replace')
                    
                except Exception as e:
                    # Ultimate fallback - return original data as string
                    return str(encoded_data) if encoded_data else ''
            
            stdout = safe_decode(result.get('stdout'))
            stderr = safe_decode(result.get('stderr'))
            compile_output = safe_decode(result.get('compile_output'))
            
            if status_id == 3:  # Accepted (Success)
                return {
                    'status': 'success',
                    'output': stdout,
                    'execution_time': execution_time,
                    'error': None,
                    'memory_used': result.get('memory', 0),
                    'time_used': result.get('time', 0)
                }
            
            elif status_id == 6:  # Compilation Error
                return {
                    'status': 'error',
                    'output': stdout,
                    'execution_time': execution_time,
                    'error': f'Compilation Error: {compile_output}'
                }
            
            elif status_id == 5:  # Time Limit Exceeded
                return {
                    'status': 'error',
                    'output': stdout,
                    'execution_time': execution_time,
                    'error': 'Time Limit Exceeded'
                }
            
            elif status_id == 7:  # Memory Limit Exceeded
                return {
                    'status': 'error',
                    'output': stdout,
                    'execution_time': execution_time,
                    'error': 'Memory Limit Exceeded'
                }
            
            else:  # Other errors
                error_msg = stderr or compile_output or result['status']['description']
                return {
                    'status': 'error',
                    'output': stdout,
                    'execution_time': execution_time,
                    'error': f'Runtime Error: {error_msg}'
                }
        
        # Timeout waiting for result
        return {
            'status': 'error',
            'output': '',
            'execution_time': time.time() - start_time,
            'error': 'Execution timeout - code took too long to complete'
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'output': '',
            'execution_time': 0,
            'error': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'execution_time': 0,
            'error': f'API error: {str(e)}'
        }
def execute_code_with_tests(code, language, lesson):
    """Execute code with test cases using Judge0 API"""
    if not lesson.test_cases:
        return execute_code_safely(code, language, lesson)
    
    test_results = []
    tests_passed = 0
    tests_total = len(lesson.test_cases)
    total_execution_time = 0
    
    for i, test_case in enumerate(lesson.test_cases):
        # Prepare test code with input
        test_code = prepare_test_code_for_judge0(code, test_case.get('input', ''), language)
        
        result = execute_code_safely(test_code, language, lesson)
        total_execution_time += result.get('execution_time', 0)
        
        expected_output = test_case.get('expected_output', '').strip()
        actual_output = result.get('output', '').strip()
        
        test_passed = actual_output == expected_output
        if test_passed:
            tests_passed += 1
            
        test_results.append({
            'test_number': i + 1,
            'input': test_case.get('input', ''),
            'expected_output': expected_output,
            'actual_output': actual_output,
            'passed': test_passed,
            'execution_time': result.get('execution_time', 0),
            'error': result.get('error')
        })
    
    # Calculate score
    score = (tests_passed / tests_total * 100) if tests_total > 0 else 0
    
    return {
        'status': 'passed' if score >= 80 else 'failed',
        'test_results': test_results,
        'tests_passed': tests_passed,
        'tests_total': tests_total,
        'score': score,
        'output': f'Passed {tests_passed}/{tests_total} tests (Score: {score:.1f}%)',
        'execution_time': total_execution_time
    }


def prepare_test_code_for_judge0(original_code, test_input, language):
    """Prepare code with test input for Judge0 execution"""
    if language.name.lower() == 'python':
        # Mock input() function for Python
        lines = test_input.strip().split('\n') if test_input.strip() else ['']
        input_data = repr(lines)
        
        input_mock = f"""# Auto-generated input mock
import sys
input_data = {input_data}
input_index = 0

def input(prompt=''):
    global input_index
    if input_index < len(input_data):
        result = input_data[input_index]
        input_index += 1
        return result
    return ''

# Original code below:
"""
        return input_mock + original_code
    
    elif language.name.lower() == 'java':
        # For Java, we need to mock Scanner input
        lines = test_input.strip().split('\n') if test_input.strip() else ['']
        input_data = ', '.join(f'"{line}"' for line in lines)
        
        # This is more complex for Java - basic implementation
        return original_code.replace(
            'Scanner', 
            f'// Mock Scanner\nString[] mockInput = {{{input_data}}};\nint mockIndex = 0;\n// Scanner'
        )
    
    elif language.name.lower() == 'javascript':
        # For Node.js, mock readline or process.stdin
        lines = test_input.strip().split('\n') if test_input.strip() else ['']
        input_data = '[' + ', '.join(f'"{line}"' for line in lines) + ']'
        
        input_mock = f"""// Auto-generated input mock
const mockInput = {input_data};
let mockIndex = 0;

// Mock readline function
function readline() {{
    if (mockIndex < mockInput.length) {{
        return mockInput[mockIndex++];
    }}
    return '';
}}

// Original code below:
"""
        return input_mock + original_code
    
    # For other languages, return as-is for now
    return original_code


def get_execution_command(language, filename):
    """Get appropriate execution command for language (not needed for Judge0)"""
    # This function is kept for compatibility but not used with Judge0
    commands = {
        'python': 'python main.py',
        'javascript': 'node main.js',
        'java': 'javac main.java && java Main',
        'cpp': 'g++ -o main main.cpp && ./main',
        'c': 'gcc -o main main.c && ./main'
    }
    
    return commands.get(language.name, 'python main.py')

def prepare_test_code(original_code, test_input, language):
    """Prepare code with test input for execution"""
    if language.name == 'python':
        # For Python, we can mock input()
        lines = test_input.strip().split('\n')
        input_mock = f"input_data = {lines}\ninput_index = 0\ndef input(prompt=''):\n    global input_index\n    if input_index < len(input_data):\n        result = input_data[input_index]\n        input_index += 1\n        return result\n    return ''\n\n"
        return input_mock + original_code
    
    # For other languages, similar logic would be needed
    return original_code


def get_ai_code_feedback(code, lesson, test_results, score):
    """Get AI feedback on submitted code"""
    try:
        # Import AI functionality from existing views
        from .views import call_gemini_api
        
        prompt = f"""
        Bạn là mentor lập trình chuyên nghiệp. Hãy review code sau và đưa ra feedback:
        
        Bài tập: {lesson.title}
        Mô tả: {lesson.problem_statement}
        
        Code của học viên:
        ```{lesson.course.language.name}
        {code}
        ```
        
        Kết quả test: {score:.1f}% ({sum(1 for t in test_results if t['passed'])}/{len(test_results)} tests passed)
        
        Hãy đưa ra:
        1. Nhận xét về logic và cách tiếp cận
        2. Điểm mạnh và điểm cần cải thiện
        3. Gợi ý tối ưu hóa (nếu có)
        4. Khuyến khích và hướng dẫn tiếp theo
        
        Giữ feedback ngắn gọn, tích cực và hữu ích.
        """
        
        messages = [{'role': 'user', 'content': prompt}]
        response = call_gemini_api(messages)
        
        if response.get('success'):
            return response.get('content', 'Không thể tạo feedback')
        else:
            return 'AI feedback tạm thời không khả dụng'
            
    except Exception as e:
        return f'Lỗi khi tạo AI feedback: {str(e)}'


@login_required
def code_dashboard(request):
    """Coding dashboard with user progress and stats"""
    # Get or create user coding profile
    profile, created = UserCodingProfile.objects.get_or_create(
        user=request.user,
        defaults={'skill_level': 'beginner'}
    )
    
    # Get user's enrollments with progress
    enrollments = CodeEnrollment.objects.filter(
        user=request.user
    ).select_related('course__language').order_by('-last_accessed')
    
    # Get recent submissions
    recent_submissions = CodeSubmission.objects.filter(
        user=request.user
    ).select_related('lesson__course').order_by('-created_at')[:10]
    
    # Get recommended courses based on user's preferences
    recommended_courses = CodeCourse.objects.filter(
        status='published',
        language=profile.preferred_language if profile.preferred_language else None
    ).exclude(
        id__in=enrollments.values_list('course_id', flat=True)
    ).order_by('-enrollment_count', '-rating_average')[:6]
    
    # Calculate statistics
    total_submissions = CodeSubmission.objects.filter(user=request.user).count()
    successful_submissions = CodeSubmission.objects.filter(
        user=request.user, 
        score__gte=80
    ).count()
    success_rate = (successful_submissions / total_submissions * 100) if total_submissions > 0 else 0
    
    # Get skill distribution
    languages_stats = {}
    for enrollment in enrollments:
        lang = enrollment.course.language.display_name
        if lang not in languages_stats:
            languages_stats[lang] = {'courses': 0, 'progress': 0}
        languages_stats[lang]['courses'] += 1
        languages_stats[lang]['progress'] += enrollment.completion_percentage
    
    for lang in languages_stats:
        languages_stats[lang]['avg_progress'] = languages_stats[lang]['progress'] / languages_stats[lang]['courses']
    
    context = {
        'profile': profile,
        'enrollments': enrollments,
        'recent_submissions': recent_submissions,
        'recommended_courses': recommended_courses,
        'total_submissions': total_submissions,
        'successful_submissions': successful_submissions,
        'success_rate': success_rate,
        'languages_stats': languages_stats,
        'active_courses': enrollments.filter(is_completed=False).count(),
        'completed_courses': enrollments.filter(is_completed=True).count()
    }
    
    return render(request, 'code/dashboard.html', context)
