from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import formset_factory
import json
import os
import uuid
from datetime import datetime

import cloudinary
import cloudinary.uploader
from cloudinary.models import CloudinaryField

from home.models import (
    Document, 
    University, 
    Course, 
    DocumentTag, 
    DocumentTagRelation, 
    User, 
    UserActivity
)
from .forms import DocumentForm


@login_required
def upload_step1(request):
    """Trang chọn file - Bước 1"""
    # Clear any previous session data
    if 'temp_files' in request.session:
        del request.session['temp_files']
        
    context = {
        'user': request.user,
        'step': 1,
        'max_file_size': 50 * 1024 * 1024,  # 50MB
        'allowed_extensions': ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
    }
    return render(request, 'uploads/upload_step1.html', context)


@login_required
def upload_step2(request):
    """Trang điền thông tin - Bước 2, sử dụng FormSet"""
    temp_files = request.session.get('temp_files', [])
    if not temp_files:
        messages.warning(request, 'Không có file nào để xử lý. Vui lòng bắt đầu lại từ bước 1.')
        return redirect('upload_step1')

    # Define choices to be passed to the form
    academic_year_choices = generate_academic_years()
    semester_choices = [
        ('HK1', 'Học kỳ 1'),
        ('HK2', 'Học kỳ 2'),
        ('HK3', 'Học kỳ 3')
    ]
    
    form_kwargs = {
        'academic_years': academic_year_choices,
        'semesters': semester_choices,
    }
    
    DocumentFormSet = formset_factory(DocumentForm, extra=0)
    
    # Prepare initial data for the formset
    initial_data = [{'title': os.path.splitext(f['original_name'])[0]} for f in temp_files]
    
    formset = DocumentFormSet(initial=initial_data, prefix='form', form_kwargs=form_kwargs)

    # Attach file info directly to each form
    for i, form in enumerate(formset):
        form.file_info = temp_files[i]

    context = {
        'user': request.user,
        'step': 2,
        'formset': formset,
    }
    return render(request, 'uploads/upload_step2.html', context)


@login_required
def api_temp_files_info(request):
    """API to get temporary file info from the session"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    temp_files = request.session.get('temp_files', [])
    
    return JsonResponse({
        'success': True,
        'files': temp_files
    })

@login_required
@csrf_exempt
def api_finalize_upload(request):
    """API hoàn tất upload - sử dụng FormSet"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})

    temp_files = request.session.get('temp_files', [])
    if not temp_files:
        return JsonResponse({'success': False, 'message': 'Session hết hạn hoặc không có file tạm.'})

    # Define choices and pass them to the formset for validation
    academic_year_choices = generate_academic_years()
    semester_choices = [
        ('HK1', 'Học kỳ 1'),
        ('HK2', 'Học kỳ 2'),
        ('HK3', 'Học kỳ 3')
    ]
    form_kwargs = {
        'academic_years': academic_year_choices,
        'semesters': semester_choices,
    }

    DocumentFormSet = formset_factory(DocumentForm, extra=0)
    formset = DocumentFormSet(request.POST, form_kwargs=form_kwargs)

    if formset.is_valid():
        documents_created = []
        failed_files = []
        
        try:
            with transaction.atomic():
                for i, form in enumerate(formset):
                    temp_file = temp_files[i]
                    
                    try:
                        # Check if file exists on Cloudinary
                        cloudinary.api.resource(temp_file['cloudinary_public_id'], resource_type="raw")
                        
                        # Create Document instance
                        document = Document.objects.create(
                            title=form.cleaned_data.get('title'),
                            description=form.cleaned_data.get('description'),
                            university=form.cleaned_data.get('university'),
                            course=form.cleaned_data.get('course'),
                            document_type=form.cleaned_data.get('document_type'),
                            academic_year=form.cleaned_data.get('academic_year'),
                            semester=form.cleaned_data.get('semester'),
                            file_path=temp_file['cloudinary_public_id'],
                            file_size=temp_file['size'],
                            file_type=temp_file['type'],
                            uploaded_by=request.user,
                            status='pending',
                            is_public=True # Default to public, can be changed later
                        )
                        documents_created.append(document)
                        
                        # Log activity
                        UserActivity.objects.create(
                            user=request.user,
                            action='upload_document',
                            description=f'Tải lên tài liệu: {document.title}',
                            document=document,
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                    except cloudinary.exceptions.NotFound:
                        failed_files.append(temp_file['original_name'])
                        continue
                    except Exception as e:
                        failed_files.append(f"{temp_file['original_name']} (Lỗi: {str(e)})")
                        continue
            
            # Clear session after successful processing
            if 'temp_files' in request.session:
                del request.session['temp_files']

            success_count = len(documents_created)
            message = f'Đã tải lên thành công {success_count}/{len(temp_files)} tài liệu.'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'data': {
                    'redirect_url': f"{redirect('upload_success').url}?docs={'&docs='.join(map(str, [doc.id for doc in documents_created]))}"
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'})
    else:
        # Formset is not valid, return errors
        errors = formset.errors
        print(f"--- DEBUG: Formset validation failed. Errors: {errors} ---")
        return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.', 'errors': errors})


@login_required
@csrf_exempt
def api_temporary_upload(request):
    """API tải file tạm thời lên Cloudinary"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        uploaded_files = request.FILES.getlist('files')
        if not uploaded_files:
            return JsonResponse({'success': False, 'message': 'No files provided'})
        
        temporary_files = []
        
        for file in uploaded_files:
            if not validate_uploaded_file(file):
                continue
            
            try:
                upload_result = cloudinary.uploader.upload(
                    file,
                    resource_type="raw",
                    folder="documents_temp/",
                    use_filename=True,
                    unique_filename=True
                )
                
                temporary_files.append({
                    'original_name': file.name,
                    'cloudinary_public_id': upload_result['public_id'],
                    'size': upload_result['bytes'],
                    'type': file.content_type,
                })
                
            except Exception as e:
                print(f"Lỗi upload tạm thời lên Cloudinary: {e}")
                continue
        
        request.session['temp_files'] = temporary_files
        
        return JsonResponse({
            'success': True,
            'message': f'Uploaded {len(temporary_files)} files temporarily',
            'data': {'files_count': len(temporary_files)}
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


# --- Other existing views ---

@login_required
def upload_success(request):
    """Trang thành công"""
    document_ids = request.GET.getlist('docs')
    valid_doc_ids = [int(doc_id) for doc_id in document_ids if doc_id.isdigit()]
    
    documents = Document.objects.filter(
        id__in=valid_doc_ids,
        uploaded_by=request.user
    ) if valid_doc_ids else Document.objects.none()
    
    context = {
        'documents': documents,
        'user': request.user,
        'documents_count': len(valid_doc_ids)
    }
    return render(request, 'uploads/upload_success.html', context)

@login_required
def my_uploads(request):
    """Danh sách tài liệu đã upload của user"""
    documents = Document.objects.filter(
        uploaded_by=request.user
    ).order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter in ['pending', 'approved', 'rejected']:
        documents = documents.filter(status=status_filter)
    
    search = request.GET.get('search', '').strip()
    if search:
        documents = documents.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(course__name__icontains=search)
        )
    
    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search': search,
        'status_choices': Document.STATUS_CHOICES
    }
    return render(request, 'uploads/my_uploads.html', context)

@login_required
@csrf_exempt
def api_delete_document(request, document_id):
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        document = get_object_or_404(Document, id=document_id, uploaded_by=request.user)
        
        if document.status not in ['pending', 'rejected']:
            return JsonResponse({'success': False, 'message': 'Không thể xóa tài liệu đã được phê duyệt'})
        
        if document.file_path:
            try:
                cloudinary.uploader.destroy(document.file_path, resource_type="raw")
            except Exception as e:
                print(f"Lỗi xóa file trên Cloudinary: {e}")
        
        UserActivity.objects.create(
            user=request.user,
            action='delete_document',
            description=f'Xóa tài liệu: {document.title}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        document.delete()
        
        return JsonResponse({'success': True, 'message': 'Tài liệu đã được xóa thành công'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'})

# --- Utility functions ---

def validate_uploaded_file(file):
    MAX_SIZE = 50 * 1024 * 1024
    ALLOWED_TYPES = [
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-powerpoint', 
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain', 'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/jpeg', 'image/png', 'image/gif'
    ]
    return file.size <= MAX_SIZE and file.content_type in ALLOWED_TYPES

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

def generate_academic_years(count=10):
    current_year = datetime.now().year
    return [(f"{start_year}-{start_year+1}", f"{start_year}-{start_year+1}") for start_year in range(current_year, current_year - count, -1)]

# --- API views for dynamic forms ---

@login_required
@csrf_exempt
def api_universities(request):
    search = request.GET.get('search', '')
    universities = University.objects.filter(is_active=True)
    if search:
        universities = universities.filter(Q(name__icontains=search) | Q(short_name__icontains=search))
    data = [{'id': uni.id, 'text': f"{uni.name} ({uni.short_name})"} for uni in universities.order_by('name')]
    return JsonResponse(data, safe=False)

@login_required
@csrf_exempt
def api_courses(request):
    # Handle POST request for creating a new course
    if request.method == 'POST':
        print("--- DEBUG: api_courses POST request received ---")
        try:
            data = json.loads(request.body)
            print(f"--- DEBUG: Request body decoded: {data}")

            name = data.get('name')
            code = data.get('code')
            university_id = data.get('university')
            description = data.get('description', '')

            if not all([name, code, university_id]):
                print("--- DEBUG: Validation failed - Missing name, code, or university_id ---")
                return JsonResponse({'success': False, 'message': 'Tên, mã môn học và trường đại học là bắt buộc.'})

            # Check for existing course with the same code at the same university
            if Course.objects.filter(university_id=university_id, code__iexact=code).exists():
                print(f"--- DEBUG: Course with code '{code}' already exists for university '{university_id}' ---")
                return JsonResponse({'success': False, 'message': f'Mã môn học "{code}" đã tồn tại cho trường này.'})

            university = get_object_or_404(University, id=university_id)
            
            print(f"--- DEBUG: Creating new course '{name}' with code '{code}' for university '{university.name}' ---")
            new_course = Course.objects.create(
                name=name,
                code=code,
                description=description,
                university=university,
                created_by=request.user
            )
            print(f"--- DEBUG: Course created successfully with ID: {new_course.id} ---")

            response_data = {
                'success': True,
                'message': 'Thêm môn học thành công!',
                'data': {
                    'id': new_course.id,
                    'text': f"{new_course.name} ({new_course.code})"
                }
            }
            return JsonResponse(response_data)

        except Exception as e:
            print(f"--- DEBUG: An exception occurred: {str(e)} ---")
            return JsonResponse({'success': False, 'message': f'Lỗi máy chủ: {str(e)}'})

    # Handle GET request for searching courses
    if request.method == 'GET':
        university_id = request.GET.get('university_id')
        if not university_id:
            return JsonResponse([], safe=False)
        
        search = request.GET.get('search', '')
        courses = Course.objects.filter(university_id=university_id, is_active=True)
        if search:
            courses = courses.filter(Q(name__icontains=search) | Q(code__icontains=search))
        
        data = [{'id': course.id, 'text': f"{course.name} ({course.code})"} for course in courses.order_by('name')]
        return JsonResponse(data, safe=False)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)