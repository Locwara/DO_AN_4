from django.shortcuts import render
import cloudinary
import cloudinary.uploader
from cloudinary.models import CloudinaryField
# Create your views here.
# uploads/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
import json
import os
import uuid
from datetime import datetime

from home.models import (
    Document, 
    University, 
    Course, 
    DocumentTag, 
    DocumentTagRelation, 
    User, 
    UserActivity
)
    


@login_required
def upload_step1(request):
    """Trang chọn file - Bước 1"""
    context = {
        'user': request.user,
        'step': 1,
        'max_file_size': 50 * 1024 * 1024,  # 50MB
        'allowed_extensions': ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif']
    }
    return render(request, 'uploads/upload_step1.html', context)


@login_required
def upload_step2(request):
    """Trang điền thông tin - Bước 2"""
    # FIXED: Không kiểm tra session nữa vì files được lưu trong browser sessionStorage
    # JavaScript sẽ xử lý việc kiểm tra files
    
    context = {
        'user': request.user,
        'step': 2,
        'document_types': Document.DOCUMENT_TYPE_CHOICES,
        'current_year': datetime.now().year,
        'academic_years': generate_academic_years(),
        'semesters': [
            ('HK1', 'Học kỳ 1'),
            ('HK2', 'Học kỳ 2'), 
            ('HK3', 'Học kỳ 3 (Hè)')
        ]
    }
    return render(request, 'uploads/upload_step2.html', context)
@login_required
@csrf_exempt
def api_universities(request):
    """API lấy danh sách trường đại học"""
    if request.method == 'GET':
        search = request.GET.get('search', '')
        universities = University.objects.filter(is_active=True)
        
        if search:
            universities = universities.filter(
                Q(name__icontains=search) | Q(short_name__icontains=search)
            )
        
        data = [{
            'id': uni.id,
            'name': uni.name,
            'short_name': uni.short_name,
            'display_name': f"{uni.name} ({uni.short_name})"
        } for uni in universities.order_by('name')]
        
        return JsonResponse({'success': True, 'data': data})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})


@login_required
@csrf_exempt
def api_courses(request):
    """API lấy danh sách môn học theo trường"""
    if request.method == 'GET':
        university_id = request.GET.get('university')
        search = request.GET.get('search', '')
        
        if not university_id:
            return JsonResponse({'success': False, 'message': 'University ID required'})
        
        try:
            university = University.objects.get(id=university_id, is_active=True)
            courses = Course.objects.filter(university=university, is_active=True)
            
            if search:
                courses = courses.filter(
                    Q(name__icontains=search) | Q(code__icontains=search)
                )
            
            data = [{
                'id': course.id,
                'name': course.name,
                'code': course.code,
                'display_name': f"{course.name} ({course.code})"
            } for course in courses.order_by('name')]
            
            return JsonResponse({'success': True, 'data': data})
            
        except University.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'University not found'})
    
    elif request.method == 'POST':
        # Thêm môn học mới
        try:
            data = json.loads(request.body)
            university_id = data.get('university')
            name = data.get('name', '').strip()
            code = data.get('code', '').strip()
            description = data.get('description', '').strip()
            
            if not all([university_id, name, code]):
                return JsonResponse({
                    'success': False, 
                    'message': 'Vui lòng điền đầy đủ thông tin'
                })
            
            university = University.objects.get(id=university_id, is_active=True)
            
            # Kiểm tra trung lặp mã môn học
            if Course.objects.filter(university=university, code=code).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Mã môn học "{code}" đã tồn tại trong trường này'
                })
            
            course = Course.objects.create(
                name=name,
                code=code,
                description=description,
                university=university,
                created_by=request.user
            )
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='create_course',
                description=f'Tạo môn học mới: {course.name} ({course.code})',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Môn học đã được thêm thành công',
                'data': {
                    'id': course.id,
                    'name': course.name,
                    'code': course.code,
                    'display_name': f"{course.name} ({course.code})"
                }
            })
            
        except University.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Trường đại học không tồn tại'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Dữ liệu không hợp lệ'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})


@login_required
@csrf_exempt


@login_required
@csrf_exempt
def api_upload_document(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        with transaction.atomic():
            # ... code validation ...
            
            documents_created = []
            
            for file in uploaded_files:
                if not validate_uploaded_file(file):
                    continue
                
                try:
                    # Upload file lên Cloudinary
                    print(f"Uploading file: {file.name}")
                    upload_result = cloudinary.uploader.upload(
                        file,
                        resource_type="raw",
                        folder="documents/",
                        use_filename=True,
                        unique_filename=True
                    )
                    print(f"Upload result: {upload_result}")
                    
                    # Lấy thông tin từ kết quả upload
                    public_id = upload_result['public_id']
                    file_size = upload_result['bytes']
                    
                    print(f"Creating document in database...")
                    
                    # Create document record
                    document = Document.objects.create(
                        title=title if len(uploaded_files) == 1 else f"{title} - {file.name}",
                        description=description,
                        file_path=public_id,  # Lưu public_id
                        file_size=file_size,
                        file_type=file.content_type,
                        university=university,
                        course=course,
                        uploaded_by=request.user,
                        document_type=document_type,
                        academic_year=academic_year or None,
                        semester=semester or None,
                        is_public=is_public,
                        status='pending'
                    )
                    
                    print(f"Document created with ID: {document.id}")
                    documents_created.append(document)
                    
                except Exception as e:
                    print(f"Lỗi khi xử lý file {file.name}: {str(e)}")
                    # Xóa file trên Cloudinary nếu có lỗi database
                    try:
                        if 'public_id' in locals():
                            cloudinary.uploader.destroy(public_id, resource_type="raw")
                    except:
                        pass
                    continue
            
            print(f"Total documents created: {len(documents_created)}")
            
            return JsonResponse({
                'success': True,
                'message': f'Đã tải lên thành công {len(documents_created)} tài liệu',
                'data': {
                    'documents_count': len(documents_created),
                    'documents': [doc.id for doc in documents_created]
                }
            })
            
    except Exception as e:
        print(f"Lỗi general: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })
@login_required
@login_required
def upload_success(request):
    """Trang thành công"""
    document_ids = request.GET.getlist('docs')
    
    # Lọc bỏ các giá trị rỗng và convert sang int
    valid_doc_ids = []
    for doc_id in document_ids:
        try:
            if doc_id.strip():  # Kiểm tra không rỗng
                valid_doc_ids.append(int(doc_id))
        except (ValueError, AttributeError):
            continue  # Bỏ qua các giá trị không hợp lệ
    
    # Chỉ query khi có ID hợp lệ
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
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter in ['pending', 'approved', 'rejected']:
        documents = documents.filter(status=status_filter)
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        documents = documents.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(course__name__icontains=search)
        )
    
    # Pagination
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
    """API xóa tài liệu - bao gồm xóa trên Cloudinary"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        document = get_object_or_404(
            Document,
            id=document_id,
            uploaded_by=request.user
        )
        
        # Only allow delete if document is pending or rejected
        if document.status not in ['pending', 'rejected']:
            return JsonResponse({
                'success': False,
                'message': 'Không thể xóa tài liệu đã được phê duyệt'
            })
        
        # Delete file from Cloudinary
        if document.file_path:
            try:
                cloudinary.uploader.destroy(document.file_path, resource_type="raw")
            except Exception as e:
                print(f"Lỗi xóa file trên Cloudinary: {e}")
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='delete_document',
            description=f'Xóa tài liệu: {document.title}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Delete document record
        document.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Tài liệu đã được xóa thành công'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })

# Utility functions
def validate_uploaded_file(file):
    """Validate uploaded file"""
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_TYPES = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-powerpoint', 
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/jpeg',
        'image/png',
        'image/gif'
    ]
    
    if file.size > MAX_SIZE:
        return False
        
    if file.content_type not in ALLOWED_TYPES:
        return False
    
    return True


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_academic_years(count=5):
    """Generate academic years list"""
    current_year = datetime.now().year
    years = []
    
    for i in range(count):
        start_year = current_year - i
        end_year = start_year + 1
        years.append((f"{start_year}-{end_year}", f"{start_year}-{end_year}"))
    
    return years


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
            # Validate file
            if not validate_uploaded_file(file):
                continue
            
            try:
                # Upload tạm thời lên Cloudinary
                upload_result = cloudinary.uploader.upload(
                    file,
                    resource_type="raw",
                    folder="documents/",  # Thư mục tạm thời
                    use_filename=True,
                    unique_filename=True
                )
                
                temporary_files.append({
                    'original_name': file.name,
                    'cloudinary_public_id': upload_result['public_id'],
                    'cloudinary_url': upload_result['secure_url'],
                    'size': upload_result['bytes'],
                    'type': file.content_type,
                    'uploaded_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"Lỗi upload tạm thời lên Cloudinary: {e}")
                continue
        
        # Save temporary file info to session
        request.session['temp_files'] = temporary_files
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': f'Uploaded {len(temporary_files)} files temporarily',
            'data': {
                'files_count': len(temporary_files),
                'session_key': request.session.session_key
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})



@login_required
@csrf_exempt 
@login_required
@csrf_exempt
def api_finalize_upload(request):
    
    """API hoàn tất upload - KHÔNG chuyển file, chỉ tạo document record"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        # Get temporary files from session
        temp_files = request.session.get('temp_files', [])
        print(f"Temp files from session: {temp_files}")
        
        if not temp_files:
            return JsonResponse({'success': False, 'message': 'No temporary files found'})
        
        # Parse form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        document_type = request.POST.get('document_type')
        university_id = request.POST.get('university')
        course_id = request.POST.get('course')
        academic_year = request.POST.get('academic_year', '').strip()
        semester = request.POST.get('semester', '').strip()
        is_public = request.POST.get('is_public') == 'true'
        tags = request.POST.get('tags', '').strip()
        
        # Validation
        if not all([title, document_type, university_id, course_id]):
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng điền đầy đủ thông tin bắt buộc'
            })
        
        try:
            university = University.objects.get(id=university_id, is_active=True)
            course = Course.objects.get(id=course_id, university=university, is_active=True)
        except (University.DoesNotExist, Course.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Trường đại học hoặc môn học không hợp lệ'
            })
        
        documents_created = []
        failed_files = []
        
        with transaction.atomic():
            for temp_file in temp_files:
                try:
                    print(f"Processing file: {temp_file['original_name']}")
                    
                    # Kiểm tra file có tồn tại trên Cloudinary không
                    try:
                        print(f"DEBUG DATA: {temp_file}")
                        print(f"Processing file: {temp_file['original_name']}")
                        cloudinary.api.resource(
                            temp_file['cloudinary_public_id'], 
                            resource_type="raw"
                        )
                        print(f"File exists on Cloudinary: {temp_file['cloudinary_public_id']}")
                    except cloudinary.exceptions.NotFound:
                        print(f"File not found on Cloudinary: {temp_file['cloudinary_public_id']}")
                        failed_files.append(temp_file['original_name'])
                        continue
                    
                    # KHÔNG chuyển file, chỉ tạo document record với public_id hiện tại
                    document = Document.objects.create(
                        title=title if len(temp_files) == 1 else f"{title} - {temp_file['original_name']}",
                        description=description,
                        file_path=temp_file['cloudinary_public_id'],  # Giữ nguyên public_id
                        file_size=temp_file['size'],
                        file_type=temp_file['type'],
                        university=university,
                        course=course,
                        uploaded_by=request.user,
                        document_type=document_type,
                        academic_year=academic_year or None,
                        semester=semester or None,
                        is_public=is_public,
                        status='pending'
                    )
                    
                    print(f"Document created: {document.id}")
                    
                    # Process tags
                    if tags:
                        tag_names = [tag.strip() for tag in tags.split(',') if tag.strip()]
                        ai_keywords = []
                        
                        for tag_name in tag_names:
                            tag, created = DocumentTag.objects.get_or_create(name=tag_name)
                            DocumentTagRelation.objects.create(document=document, tag=tag)
                            ai_keywords.append(tag_name)
                        
                        document.ai_keywords = ai_keywords
                        document.save()
                    
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
                    
                except Exception as e:
                    print(f"Lỗi khi tạo document cho {temp_file['original_name']}: {str(e)}")
                    failed_files.append(temp_file['original_name'])
                    continue
        
        # Clear session
        if 'temp_files' in request.session:
            del request.session['temp_files']
        
        success_count = len(documents_created)
        total_count = len(temp_files)
        
        message = f'Đã tải lên thành công {success_count}/{total_count} tài liệu'
        if failed_files:
            message += f'. Thất bại: {", ".join(failed_files)}'
        
        return JsonResponse({
            'success': success_count > 0,
            'message': message,
            'data': {
                'documents_count': success_count,
                'documents': [doc.id for doc in documents_created],
                'failed_files': failed_files
            }
        })
        
    except Exception as e:
        print(f"Lỗi general: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
# Thêm vào urls.py:
# path('api/temporary-upload/', views.api_temporary_upload, name='api_temporary_upload'),
# path('api/finalize-upload/', views.api_finalize_upload, name='api_finalize_upload'),


def documents_list(request):
    documents = Document.objects.filter(
        status='approved',
        is_public=True
    ).select_related('university', 'course', 'uploaded_by')
    
    # Filtering
    document_type = request.GET.get('type')
    if document_type:
        documents = documents.filter(document_type=document_type)
    
    university_id = request.GET.get('university')
    if university_id:
        documents = documents.filter(university_id=university_id)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    documents = documents.order_by(sort_by)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(documents, 12)
    page = request.GET.get('page', 1)
    documents = paginator.get_page(page)
    
    universities = University.objects.filter(is_active=True)
    
    context = {
        'documents': documents,
        'universities': universities,
        'current_type': document_type,
        'current_university': university_id,
        'current_sort': sort_by,
    }
    
    return render(request, 'documents/list.html', context)

def documents_search(request):
    query = request.GET.get('q', '').strip()
    documents = Document.objects.filter(status='approved', is_public=True)
    
    if query:
        # Tìm kiếm trong title, description và AI keywords
        from django.db.models import Q
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(ai_keywords__overlap=[query])
        ).distinct()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(documents, 12)
    page = request.GET.get('page', 1)
    documents = paginator.get_page(page)
    
    context = {
        'documents': documents,
        'search_query': query,
        'total_results': paginator.count,
    }
    
    return render(request, 'documents/search.html', context)
# Thêm vào views.py
@login_required
@csrf_exempt
def api_temp_files_info(request):
    """API lấy thông tin file tạm thời từ session"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Method not allowed'})
    
    try:
        temp_files = request.session.get('temp_files', [])
        
        if not temp_files:
            return JsonResponse({
                'success': False, 
                'message': 'No temporary files found',
                'files': []
            })
        
        return JsonResponse({
            'success': True,
            'files': temp_files
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}',
            'files': []
        })
