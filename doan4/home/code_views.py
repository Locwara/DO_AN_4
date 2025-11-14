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
from django.db import models as db_models
import json
import time
import uuid
import tempfile
import subprocess
from datetime import timedelta
from decimal import Decimal

from .premium_views import check_course_enrollment_limit

from .models import (
    CodeLanguage, CodeCourse, CodeLesson, CodeEnrollment,
    CodeSubmission, CodeLessonProgress, CodeExecutionSession,
    CodeHint, CodeDiscussion, CodeReviewRequest, UserCodingProfile,
    User, University
)

# Code Courses Views
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
    
    # User's enrollments - chỉ khi đã đăng nhập
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


def code_course_detail(request, course_slug):
    """Course detail with lessons list"""
    course = get_object_or_404(
        CodeCourse,
        slug=course_slug,
        status='published'
    )
    
    # Check if user is enrolled (chỉ khi đã đăng nhập)
    enrollment = None
    if request.user.is_authenticated:
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


@require_http_methods(["POST"])
def code_course_enroll(request, course_slug):
    """Enroll in a course"""
    course = get_object_or_404(CodeCourse, slug=course_slug, status='published')
    
    # Yêu cầu đăng nhập để enroll
    if not request.user.is_authenticated:
        messages.info(request, f'Vui lòng đăng nhập để đăng ký khóa học "{course.title}"')
        return redirect('home_login')
    
    # Check if already enrolled
    if CodeEnrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, f'Bạn đã đăng ký khóa học "{course.title}" rồi!')
        return redirect('code_course_detail', course_slug=course.slug)
    
    # Check enrollment limit for free users
    can_enroll, enrolled_count = check_course_enrollment_limit(request.user)
    if not can_enroll:
        messages.warning(
            request,
            f'Bạn đã đăng ký {enrolled_count} khóa học (giới hạn cho tài khoản thường). '
            f'Nâng cấp Premium để đăng ký không giới hạn!'
        )
        return redirect('premium_upgrade')
    
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
        stdin_input = data.get('input', '')  # Get stdin input from request
        
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
            lesson=lesson,
            stdin_input=stdin_input
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
            if progress.status != 'completed':
                progress.status = 'completed'
                progress.completed_at = timezone.now()
            progress.points_earned = lesson.points_reward
            progress.best_score = max(progress.best_score, execution_result.get('score', 0))
        
        progress.save()

        # Update enrollment stats
        total_lessons = CodeLesson.objects.filter(course=enrollment.course, is_published=True).count()
        completed_lessons = CodeLessonProgress.objects.filter(
            enrollment=enrollment,
            status='completed'
        ).count()
        
        if total_lessons > 0:
            enrollment.completion_percentage = Decimal((completed_lessons / total_lessons) * 100)
        else:
            enrollment.completion_percentage = Decimal(0)
        
        # Update total points from all completed lessons
        enrollment.total_points = CodeLessonProgress.objects.filter(
            enrollment=enrollment,
            status='completed'
        ).aggregate(total=db_models.Sum('points_earned'))['total'] or 0
        
        # Update total time spent using estimated time from completed lessons
        enrollment.total_time_spent = CodeLessonProgress.objects.filter(
            enrollment=enrollment,
            status='completed'
        ).aggregate(total=db_models.Sum('lesson__estimated_time'))['total'] or 0
        
        enrollment.save()

        # Get AI feedback (async in background) - DISABLED to reduce API calls
        # TODO: Re-enable with rate limiting or make it optional
        # if lesson.ai_prompt_template:
        #     ai_feedback = get_ai_code_feedback(
        #         code=code,
        #         lesson=lesson,
        #         test_results=execution_result.get('test_results', []),
        #         score=execution_result.get('score', 0)
        #     )
        #     submission.ai_feedback = ai_feedback
        #     submission.save()
        
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

from django.conf import settings

def execute_code_safely(code, language, lesson=None, stdin_input='', timeout=10):
    """Execute code using Judge0 API with settings configuration"""
    try:
        # Judge0 language IDs
        language_ids = {
            'python': 71,      
            'javascript': 63,  
            'java': 62,        
            'cpp': 54,         
            'c': 50,           
            'csharp': 51,      
            'go': 60,          
            'rust': 73,        
            'php': 68,         
            'ruby': 72,        
        }
        
        lang_id = language_ids.get(language.name.lower(), 71)
        
        # Use API key from settings
        api_key = getattr(settings, 'JUDGE0_API_KEY', None)
        base_url = f"https://{getattr(settings, 'JUDGE0_BASE_URL', 'judge0-ce.p.rapidapi.com')}"
        
        if not api_key:
            # Fallback to local execution if no API key
            if language.name.lower() == 'python':
                return execute_python_locally(code, stdin_input)
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'No Judge0 API key configured'
            }
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": settings.JUDGE0_BASE_URL,
            "Content-Type": "application/json"
        }
        
        # Smart input handling for Judge0
        # Convert space-separated values to newline-separated
        processed_stdin = stdin_input or ""
        if processed_stdin and ' ' in processed_stdin.strip() and '\n' not in processed_stdin:
            # Single line with spaces - convert to multiple lines
            processed_stdin = processed_stdin.strip().replace(' ', '\n')
        
        payload = {
            "language_id": lang_id,
            "source_code": code,
            "stdin": processed_stdin,
        }
        
        start_time = time.time()
        
        print(f"Using Judge0 API Key: {api_key[:20]}...")  # Debug log
        
        # Submit code for execution
        try:
            response = requests.post(
                f"{base_url}/submissions",
                json=payload,
                headers=headers,
                timeout=15
            )
        except requests.exceptions.Timeout:
            if language.name.lower() == 'python':
                return execute_python_locally(code)
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'Request timeout. Using local fallback...'
            }
        
        print(f"Judge0 Response Status: {response.status_code}")  # Debug log
        
        if response.status_code == 429:
            print("Rate limit hit, falling back to local execution")
            if language.name.lower() == 'python':
                return execute_python_locally(code)
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'API rate limit exceeded. Please try again later.'
            }
        
        if response.status_code != 201:
            print(f"Judge0 Error Response: {response.text}")
            if language.name.lower() == 'python':
                return execute_python_locally(code)
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': f'Judge0 API error (HTTP {response.status_code})'
            }
        
        try:
            result_data = response.json()
            token = result_data.get('token')
            if not token:
                raise ValueError("No token received")
        except Exception as e:
            print(f"Token parsing error: {e}")
            if language.name.lower() == 'python':
                return execute_python_locally(code)
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'Invalid API response'
            }
        
        # Poll for result
        get_url = f"{base_url}/submissions/{token}"
        max_attempts = 20
        
        for attempt in range(max_attempts):
            if time.time() - start_time > 30:  # 30 second hard limit
                break
                
            try:
                result_response = requests.get(get_url, headers=headers, timeout=5)
                
                if result_response.status_code != 200:
                    time.sleep(1)
                    continue
                
                result = result_response.json()
                status_id = result.get('status', {}).get('id')
                
                if not status_id:
                    time.sleep(1)
                    continue
                
                # Still processing
                if status_id in [1, 2]:
                    time.sleep(1)
                    continue
                
                # Got final result
                execution_time = time.time() - start_time
                
                stdout = safe_decode(result.get('stdout', ''))
                stderr = safe_decode(result.get('stderr', ''))
                compile_output = safe_decode(result.get('compile_output', ''))
                
                if status_id == 3:  # Success
                    return {
                        'status': 'success',
                        'output': stdout or 'Code executed successfully',
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
                        'error': f'Compilation Error: {compile_output or "Unknown error"}'
                    }
                
                elif status_id in [5, 7]:  # Time/Memory limit
                    return {
                        'status': 'error',
                        'output': stdout,
                        'execution_time': execution_time,
                        'error': 'Time or memory limit exceeded'
                    }
                
                else:  # Other errors
                    error_msg = stderr or compile_output or result['status'].get('description', 'Unknown error')
                    return {
                        'status': 'error',
                        'output': stdout,
                        'execution_time': execution_time,
                        'error': f'Runtime Error: {error_msg}'
                    }
                    
            except requests.exceptions.Timeout:
                time.sleep(1)
                continue
            except Exception as e:
                print(f"Polling error: {e}")
                time.sleep(1)
                continue
        
        # Timeout or max attempts reached
        if language.name.lower() == 'python':
            return execute_python_locally(code, stdin_input)
            
        return {
            'status': 'error',
            'output': '',
            'execution_time': time.time() - start_time,
            'error': 'Execution timeout. Please try again.'
        }
        
    except Exception as e:
        print(f"Execute code error: {e}")
        if language.name.lower() == 'python':
            return execute_python_locally(code, stdin_input)
        return {
            'status': 'error',
            'output': '',
            'execution_time': 0,
            'error': f'System error: {str(e)}'
        }


def safe_decode(encoded_data):
    """Safe Base64 decode function"""
    if not encoded_data:
        return ''
    
    try:
        if isinstance(encoded_data, str):
            import re
            if re.match(r'^[A-Za-z0-9+/]*={0,2}$', encoded_data.strip()):
                try:
                    import base64
                    encoded_str = encoded_data.strip()
                    missing_padding = len(encoded_str) % 4
                    if missing_padding:
                        encoded_str += '=' * (4 - missing_padding)
                    
                    decoded_bytes = base64.b64decode(encoded_str)
                    return decoded_bytes.decode('utf-8', errors='replace')
                except:
                    return encoded_data
            return encoded_data
        
        if isinstance(encoded_data, bytes):
            return encoded_data.decode('utf-8', errors='replace')
        
        return str(encoded_data) if encoded_data else ''
        
    except:
        return str(encoded_data) if encoded_data else ''

# REPLACE execute_python_locally function with this:

def execute_python_locally(code, test_input=''):
    """Simple, working Python executor with smart input handling"""
    try:
        import sys
        from io import StringIO
        
        # Basic security check
        forbidden_words = ['import os', 'subprocess', 'exec(', 'eval(', 'open(', '__import__']
        if any(word in code.lower() for word in forbidden_words):
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'Code contains forbidden operations'
            }
        
        # Smart input handling:
        # - Each line = separate input() call
        # - OR single line with space-separated values
        input_values = []
        if test_input and test_input.strip():
            lines = test_input.strip().split('\n')
            for line in lines:
                # Check if line has multiple values (space-separated)
                if ' ' in line.strip():
                    # Split by space and add each as separate input
                    values = line.strip().split()
                    input_values.extend(values)
                else:
                    # Single value per line
                    input_values.append(line.strip())
        
        input_iterator = iter(input_values) if input_values else iter([''])
        
        # Mock input function
        def mock_input(prompt=''):
            try:
                return next(input_iterator)
            except StopIteration:
                return ''  # Return empty if no more input
        
        # Capture stdout
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        start_time = time.time()
        
        try:
            # Create safe execution environment
            exec_globals = {
                '__builtins__': {
                    # Safe built-in functions
                    'print': print,
                    'input': mock_input,  # Our custom input
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'range': range,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'abs': abs,
                    'max': max,
                    'min': min,
                    'sum': sum,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'round': round,
                    'pow': pow,
                }
            }
            
            # Execute the user's code
            exec(code, exec_globals, {})
            
            execution_time = time.time() - start_time
            output = captured_output.getvalue().strip()
            
            return {
                'status': 'success',
                'output': output if output else 'Code executed successfully',
                'execution_time': execution_time,
                'error': None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            output = captured_output.getvalue().strip()
            
            # Clean up error message
            error_msg = str(e)
            if 'line' in error_msg.lower() and 'file' in error_msg.lower():
                # Extract just the error type and message
                error_parts = error_msg.split(':')
                if len(error_parts) > 1:
                    error_msg = error_parts[-1].strip()
            
            return {
                'status': 'error',
                'output': output,
                'execution_time': execution_time,
                'error': f'Error: {error_msg}'
            }
            
        finally:
            # Always restore stdout
            sys.stdout = old_stdout
            
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'execution_time': 0,
            'error': f'System error: {str(e)}'
        }

def execute_python_simple_with_input(code, test_input=''):
    """Simple in-memory execution with smart input mocking"""
    try:
        import sys
        from io import StringIO
        import builtins
        
        # Security check
        forbidden = ['import os', 'subprocess', '__import__', 'exec(', 'eval(', 'open(']
        if any(f in code.lower() for f in forbidden):
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'Code contains forbidden operations'
            }
        
        # Smart input handling (same as execute_python_locally)
        input_values = []
        if test_input and test_input.strip():
            lines = test_input.strip().split('\n')
            for line in lines:
                if ' ' in line.strip():
                    # Multiple space-separated values
                    input_values.extend(line.strip().split())
                else:
                    # Single value
                    input_values.append(line.strip())
        
        input_iterator = iter(input_values) if input_values else iter([''])
        
        # Mock input function
        def mock_input(prompt=''):
            try:
                return next(input_iterator)
            except StopIteration:
                return ''
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        # Save original input
        original_input = builtins.input
        
        start_time = time.time()
        
        try:
            # Override input function
            builtins.input = mock_input
            
            # Execute user code
            exec(code)
            
            execution_time = time.time() - start_time
            output = mystdout.getvalue().strip()
            
            return {
                'status': 'success',
                'output': output if output else 'Code executed successfully',
                'execution_time': execution_time,
                'error': None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            output = mystdout.getvalue().strip()
            
            return {
                'status': 'error',
                'output': output,
                'execution_time': execution_time,
                'error': f'Python Error: {str(e)}'
            }
            
        finally:
            # Restore everything
            sys.stdout = old_stdout
            builtins.input = original_input
            
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'execution_time': 0,
            'error': f'Execution error: {str(e)}'
        }

def execute_code_with_tests(code, language, lesson):
    """Execute code with test cases - FIXED VERSION"""
    if not lesson.test_cases:
        return execute_python_simple_with_input(code)
    
    test_results = []
    tests_passed = 0
    tests_total = len(lesson.test_cases)
    total_execution_time = 0
    
    for i, test_case in enumerate(lesson.test_cases):
        test_input = test_case.get('input', '')
        expected_output = test_case.get('expected_output', '').strip()
        
        # Execute with test input
        if language.name.lower() == 'python':
            result = execute_python_simple_with_input(code, test_input)
        else:
            # For other languages, use Judge0 with prepared code
            prepared_code = prepare_test_code_for_judge0(code, test_input, language)
            result = execute_code_safely(prepared_code, language, lesson)
        
        total_execution_time += result.get('execution_time', 0)
        
        actual_output = result.get('output', '').strip()
        test_passed = (actual_output == expected_output)
        
        if test_passed:
            tests_passed += 1
            
        test_results.append({
            'test_number': i + 1,
            'input': test_input,
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

# Update functions in views.py

def prepare_test_code_for_judge0(original_code, test_input, language):
    """FIXED: Prepare code with test input - no more builtins error"""
    
    if language.name.lower() == 'python':
        if test_input and test_input.strip():
            lines = test_input.strip().split('\n')
            input_data = repr(lines)
            
            # FIXED: Use globals() instead of __builtins__
            input_mock = f'''# Auto-generated input mock
import builtins
input_data = {input_data}
input_index = 0

def mock_input(prompt=''):
    global input_index
    if input_index < len(input_data):
        result = input_data[input_index]
        input_index += 1
        return result
    return ''

# Override input function safely
builtins.input = mock_input

# Original user code:
{original_code}
'''
        else:
            # No input provided - mock to return empty string
            input_mock = f'''# Auto-generated input mock (no input)
import builtins

def mock_input(prompt=''):
    return ''

# Override input function safely
builtins.input = mock_input

# Original user code:
{original_code}
'''
        
        return input_mock
    
    # For other languages, return original
    return original_code

def execute_python_locally_with_input(code, test_input=''):
    """FIXED: Proper indentation handling for user code"""
    try:
        import subprocess
        import tempfile
        import os
        
        # Security check
        forbidden = ['import os', 'subprocess', '__import__', 'exec(', 'eval(', 'open(']
        if any(f in code.lower() for f in forbidden):
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'Code contains forbidden operations'
            }
        
        # FIXED: Proper indentation of user code
        if test_input and test_input.strip():
            lines = test_input.strip().split('\n')
            input_data = repr(lines)
            
            # Add proper indentation to user code
            user_code_lines = code.split('\n')
            indented_user_code = '\n'.join('    ' + line for line in user_code_lines)
            
            wrapped_code = f'''import builtins
import sys

# Input data from test
input_data = {input_data}
input_index = 0

def mock_input(prompt=''):
    global input_index
    if input_index < len(input_data):
        result = input_data[input_index]
        input_index += 1
        return result
    return ''

# Override input safely
original_input = builtins.input
builtins.input = mock_input

try:
{indented_user_code}
except Exception as e:
    print(f"Error: {{e}}")
finally:
    builtins.input = original_input
'''
        else:
            # No input provided
            user_code_lines = code.split('\n')
            indented_user_code = '\n'.join('    ' + line for line in user_code_lines)
            
            wrapped_code = f'''import builtins
import sys

def mock_input(prompt=''):
    return ''

# Override input safely  
original_input = builtins.input
builtins.input = mock_input

try:
{indented_user_code}
except Exception as e:
    print(f"Error: {{e}}")
finally:
    builtins.input = original_input
'''
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(wrapped_code)
            temp_file = f.name
        
        start_time = time.time()
        
        try:
            # Execute with timeout
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return {
                    'status': 'success',
                    'output': output if output else 'Code executed successfully',
                    'execution_time': execution_time,
                    'error': None
                }
            else:
                return {
                    'status': 'error',
                    'output': result.stdout.strip(),
                    'execution_time': execution_time,
                    'error': f'Python Error: {result.stderr.strip()}'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'output': '',
                'execution_time': 10,
                'error': 'Code execution timeout (10 seconds)'
            }
            
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'execution_time': 0,
            'error': f'Execution error: {str(e)}'
        }

def execute_python_simple_with_input_fixed(code, test_input=''):
    """Better approach using exec() with proper scope"""
    try:
        import sys
        from io import StringIO
        import builtins
        
        # Security check
        forbidden = ['import os', 'subprocess', '__import__', 'exec(', 'eval(', 'open(']
        if any(f in code.lower() for f in forbidden):
            return {
                'status': 'error',
                'output': '',
                'execution_time': 0,
                'error': 'Code contains forbidden operations'
            }
        
        # Setup input data
        if test_input and test_input.strip():
            input_lines = test_input.strip().split('\n')
            input_iterator = iter(input_lines)
        else:
            input_iterator = iter([''])  # Empty input
        
        # Mock input function
        def mock_input(prompt=''):
            try:
                return next(input_iterator)
            except StopIteration:
                return ''
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        # Save original functions
        original_input = builtins.input
        
        start_time = time.time()
        
        try:
            # Create execution environment
            execution_globals = {
                '__builtins__': __builtins__,
                'input': mock_input,  # Override input in globals
            }
            execution_locals = {}
            
            # Execute user code
            exec(code, execution_globals, execution_locals)
            
            execution_time = time.time() - start_time
            output = mystdout.getvalue().strip()
            
            return {
                'status': 'success',
                'output': output if output else 'Code executed successfully',
                'execution_time': execution_time,
                'error': None
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            output = mystdout.getvalue().strip()
            
            return {
                'status': 'error',
                'output': output,
                'execution_time': execution_time,
                'error': f'Python Error: {str(e)}'
            }
            
        finally:
            # Restore everything
            sys.stdout = old_stdout
            builtins.input = original_input
            
    except Exception as e:
        return {
            'status': 'error',
            'output': '',
            'execution_time': 0,
            'error': f'Execution error: {str(e)}'
        }

# Update the main execute_code_safely function to handle input properly

# Quick test function to verify input handling
def test_input_handling():
    """Test function for input handling"""
    test_code = '''name = input("Enter your name: ")
age = input("Enter your age: ")
print(f"Hello {name}, you are {age} years old!")
'''
    
    test_input_data = '''John Doe
25'''
    
    result = execute_python_locally_with_input(test_code, test_input_data)
    print("Test Result:", result)
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
