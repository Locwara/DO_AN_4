from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from cloudinary.models import CloudinaryField
import uuid
from django.conf import settings

class User(AbstractUser):
    """Mở rộng bảng auth_user của Django"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    avatar = CloudinaryField('avatar', blank=True, null=True, folder="avatars/")
    bio = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    premium_expiry = models.DateTimeField(null=True, blank=True)
    premium_activated_at = models.DateTimeField(null=True, blank=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(null=True, blank=True)
    google_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'auth_user'


class University(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    website = models.CharField(max_length=255, null=True, blank=True)
    logo = CloudinaryField('logo', blank=True, null=True, folder="university_logos/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'universities'
        verbose_name_plural = 'Universities'


class Course(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        db_table = 'courses'
        unique_together = ['code', 'university']


class Document(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('textbook', 'Textbook'),
        ('exercise', 'Exercise'),
        ('exam', 'Exam'),
        ('thesis', 'Thesis'),
        ('lecture', 'Lecture'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    file_path = CloudinaryField(
        'document', 
        resource_type='raw',
        folder="documents/",
        null=True, 
        blank=True
    )
    file_size = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=150, null=True, blank=True)
    thumbnail = CloudinaryField('thumbnail', blank=True, null=True, folder="thumbnails/")
    
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, default='other')
    academic_year = models.CharField(max_length=10, null=True, blank=True)
    semester = models.CharField(max_length=20, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_public = models.BooleanField(default=True)
    admin_notes = models.TextField(null=True, blank=True)
    
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    
    ai_summary = models.TextField(null=True, blank=True)
    ai_keywords = ArrayField(models.CharField(max_length=100), null=True, blank=True)
    search_vector = SearchVectorField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'documents'
        indexes = [
            models.Index(fields=['status', 'is_public', '-view_count']),
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['university', '-created_at']),
        ]
    def get_download_url(self):
        """Trả về URL download trực tiếp"""
        if not self.file_path:
            return None
            
        try:
            if hasattr(self.file_path, 'public_id') and self.file_path.public_id:
                import cloudinary
                return cloudinary.CloudinaryImage(self.file_path.public_id).build_url(
                    secure=True,
                    resource_type="raw",
                    flags="attachment"  # Force download
                )
            else:
                return self.file_path.url
        except:
            return self.file_path.url
    def get_search_keywords(self):
        """Extract keywords for better search"""
        keywords = []
        if self.title:
            keywords.extend(self.title.split())
        if self.course:
            keywords.extend([self.course.name, self.course.code])
        if self.university:
            keywords.append(self.university.name)
        return keywords
    def get_secure_file_url(self):
        """Trả về secure URL cho file"""
        if not self.file_path:
            return None
        
        try:
            # Kiểm tra xem có phải Cloudinary file không
            if hasattr(self.file_path, 'public_id') and self.file_path.public_id:
                import cloudinary
                # Dùng public_id để tạo URL
                return cloudinary.CloudinaryImage(self.file_path.public_id).build_url(
                    secure=True,
                    resource_type="raw"  # Quan trọng cho files không phải image
                )
            else:
                # Fallback về URL thông thường
                url = self.file_path.url
                if not settings.DEBUG and url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                return url
                
        except Exception as e:
            print(f"Error getting secure URL: {e}")
            # Fallback về URL gốc
            url = self.file_path.url
            if not settings.DEBUG and url.startswith('http://'):
                url = url.replace('http://', 'https://')
            return url
    def get_cloudinary_secure_url(self):
        """Trả về Cloudinary secure URL"""
        if hasattr(self.file_path, 'public_id'):
            import cloudinary
            return cloudinary.CloudinaryImage(self.file_path.public_id).build_url(secure=True)
        return self.get_secure_file_url()

class DocumentTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#6B7280')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'document_tags'


class DocumentTagRelation(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    tag = models.ForeignKey(DocumentTag, on_delete=models.CASCADE)

    class Meta:
        db_table = 'document_tag_relations'
        unique_together = ['document', 'tag']


class DocumentLike(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_likes'
        unique_together = ['document', 'user']


class DocumentView(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_views'


class DocumentDownload(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_downloads'


class StudyList(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'study_lists'


class StudyListItem(models.Model):
    study_list = models.ForeignKey(StudyList, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'study_list_items'
        unique_together = ['study_list', 'document']


class ChatRoom(models.Model):
    ROOM_TYPE_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('group', 'Group'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='public')
    max_members = models.IntegerField(default=100)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'chat_rooms'
        indexes = [
            models.Index(fields=['is_active', 'room_type', '-created_at']),
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['university', '-created_at']),
        ]

class ChatRoomMember(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_room_members'
        unique_together = ['room', 'user']


class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('document_share', 'Document Share'),  # ← THÊM MỚI
        ('system', 'System'),
    ]

    room = models.ForeignKey('ChatRoom', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)  # Cho phép trống cho file/image
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    
    # File attachments
    file_url = CloudinaryField('chat_file', resource_type='auto', blank=True, null=True, folder="chat_files/")
    file_name = models.CharField(max_length=255, blank=True, null=True)  # ← THÊM MỚI
    file_size = models.BigIntegerField(blank=True, null=True)  # ← THÊM MỚI
    file_type = models.CharField(max_length=50, blank=True, null=True)  # ← THÊM MỚI
    
    # Document sharing
    shared_document = models.ForeignKey('Document', on_delete=models.SET_NULL, blank=True, null=True)  # ← THÊM MỚI
    
    # Image dimensions for better display
    image_width = models.IntegerField(blank=True, null=True)  # ← THÊM MỚI
    image_height = models.IntegerField(blank=True, null=True)  # ← THÊM MỚI
    
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.message_type == 'document_share':
            return f"{self.user.username} shared: {self.shared_document.title if self.shared_document else 'Document'}"
        elif self.message_type in ['image', 'file']:
            return f"{self.user.username} sent: {self.file_name or 'File'}"
        return f"{self.user.username}: {self.message[:50] if self.message else 'Message'}"

    class Meta:
        db_table = 'chat_messages'
    
    def get_file_icon(self):
        """Trả về icon phù hợp cho loại file"""
        if not self.file_type:
            return 'fa-file'
        
        file_icons = {
            'pdf': 'fa-file-pdf text-danger',
            'doc': 'fa-file-word text-primary',
            'docx': 'fa-file-word text-primary',
            'xls': 'fa-file-excel text-success',
            'xlsx': 'fa-file-excel text-success',
            'ppt': 'fa-file-powerpoint text-warning',
            'pptx': 'fa-file-powerpoint text-warning',
            'txt': 'fa-file-alt text-info',
            'zip': 'fa-file-archive text-secondary',
            'rar': 'fa-file-archive text-secondary',
            'mp3': 'fa-file-audio text-info',
            'mp4': 'fa-file-video text-danger',
            'jpg': 'fa-file-image text-success',
            'png': 'fa-file-image text-success',
            'gif': 'fa-file-image text-success',
        }
        
        return file_icons.get(self.file_type.lower(), 'fa-file')
    
    def get_file_size_display(self):
        """Hiển thị kích thước file dễ đọc"""
        if not self.file_size:
            return ''
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"


# Thêm model mới cho Document Search trong Chat
class ChatDocumentSearch(models.Model):
    """Model lưu lịch sử tìm kiếm tài liệu trong chat"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_document_searches'



class AIQuizSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    total_questions = models.IntegerField(default=0)
    time_limit = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'ai_quiz_sessions'


class AIQuizQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]

    quiz_session = models.ForeignKey(AIQuizSession, on_delete=models.CASCADE)
    question = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    options = models.JSONField(null=True, blank=True)
    correct_answer = models.TextField(null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)
    points = models.IntegerField(default=1)
    order_index = models.IntegerField(default=0)

    def __str__(self):
        return f"Q{self.order_index}: {self.question[:50]}"

    class Meta:
        db_table = 'ai_quiz_questions'


class AIQuizAttempt(models.Model):
    quiz_session = models.ForeignKey(AIQuizSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_answers = models.JSONField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    time_spent = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_quiz_attempts'


class AIExerciseSolution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = CloudinaryField('exercise_image', blank=True, null=True, folder="exercise_images/")
    question_text = models.TextField(null=True, blank=True)
    solution_text = models.TextField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    processing_time = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_exercise_solutions'


# AI Image/Document Solution Model - FIXED VERSION
# Sửa model AIImageSolution - thêm text_chat choice
class AIImageSolution(models.Model):
    """Enhanced model to handle image, document, and text chat solutions"""
    SOLUTION_TYPE_CHOICES = [
        ('image', 'Image Analysis'),
        ('document', 'Document Analysis'),
        ('text_chat', 'Text Chat'),  # ← THÊM DÒNG NÀY
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Type of solution
    solution_type = models.CharField(max_length=20, choices=SOLUTION_TYPE_CHOICES, default='image')
    
    # File storage (can be image, document, or text chat marker)
    image_url = CloudinaryField('ai_content', blank=True, null=True, folder="ai_files/")
    original_filename = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    # Content extraction
    extracted_text = models.TextField(null=True, blank=True)  # Text from image OCR or document
    
    # AI Processing results
    ai_solution = models.TextField(null=True, blank=True)     # AI response/solution
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    processing_time = models.IntegerField(null=True, blank=True)  # milliseconds
    
    # Metadata
    title = models.CharField(max_length=255, default="AI Solution")
    is_public = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    
    # Additional fields for document analysis
    keywords = models.JSONField(null=True, blank=True)
    document_type = models.CharField(max_length=10, null=True, blank=True)  # pdf, docx, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        db_table = 'ai_image_solutions'
        ordering = ['-created_at']
        
    def is_document_analysis(self):
        return self.solution_type == 'document'
        
    def is_image_analysis(self):
        return self.solution_type == 'image'
        
    def is_text_chat(self):  # ← THÊM METHOD NÀY
        return self.solution_type == 'text_chat'
        
    def get_file_icon(self):
        """Return appropriate icon for the file type"""
        if self.solution_type == 'image':
            return 'fa-image text-primary'
        elif self.solution_type == 'text_chat':  # ← THÊM CASE NÀY
            return 'fa-comments text-info'
        
        if self.document_type:
            icons = {
                'pdf': 'fa-file-pdf text-danger',
                'docx': 'fa-file-word text-primary',
                'doc': 'fa-file-word text-primary',
                'pptx': 'fa-file-powerpoint text-warning',
                'ppt': 'fa-file-powerpoint text-warning',
                'xlsx': 'fa-file-excel text-success',
                'xls': 'fa-file-excel text-success',
                'txt': 'fa-file-alt text-info',
                'csv': 'fa-file-csv text-success'
            }
            return icons.get(self.document_type, 'fa-file')
        
        return 'fa-file-alt'

class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_solution = models.ForeignKey(
        AIImageSolution, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        db_table = 'ai_conversations'


class AIConversationMessage(models.Model):
    """Model lưu từng tin nhắn trong cuộc trò chuyện với AI"""
    MESSAGE_ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=MESSAGE_ROLE_CHOICES)
    content = models.TextField()
    
    # Optional: attach image nếu user gửi thêm ảnh trong conversation
    image_url = CloudinaryField('conversation_image', blank=True, null=True, folder="conversation_images/")
    
    # Metadata
    tokens_used = models.IntegerField(null=True, blank=True)
    response_time = models.IntegerField(null=True, blank=True)  # milliseconds
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.conversation} - {self.role}: {self.content[:50]}"

    class Meta:
        db_table = 'ai_conversation_messages'
        ordering = ['created_at']


class AIImageSolutionLike(models.Model):
    """Like cho AI solutions để user có thể bookmark solutions hay"""
    solution = models.ForeignKey(AIImageSolution, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_image_solution_likes'
        unique_together = ['solution', 'user']


class UserReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('copyright', 'Copyright Violation'),
        ('harassment', 'Harassment'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    REASON_CHOICES = [
        ('inappropriate', 'Nội dung không phù hợp'),
        ('wrong', 'Bài giải sai'),
        ('spam', 'Spam'),
        ('copyright', 'Vi phạm bản quyền'),
        ('other', 'Khác'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    study_list = models.ForeignKey(StudyList, on_delete=models.CASCADE, null=True, blank=True)
    solution = models.ForeignKey(AIImageSolution, on_delete=models.CASCADE, null=True, blank=True)
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES, default='other')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='other')
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_reports'
        unique_together = ['reporter', 'solution']  # Prevent duplicate reports
    
    def __str__(self):
        return f"Report by {self.reporter.username}"


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES, default='info')
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    class Meta:
        db_table = 'notifications'


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.action}"

    class Meta:
        db_table = 'user_activities'


class PremiumTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PLAN_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='VND')
    transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.plan_type} - {self.status}"

    class Meta:
        db_table = 'premium_transactions'


##### code 
# Thêm vào models.py của bạn

class CodeLanguage(models.Model):
    """Các ngôn ngữ lập trình được hỗ trợ"""
    name = models.CharField(max_length=50, unique=True)  # python, javascript, java, c++
    display_name = models.CharField(max_length=100)  # Python 3.9, JavaScript ES6
    version = models.CharField(max_length=20, null=True, blank=True)
    file_extension = models.CharField(max_length=10)  # .py, .js, .java
    syntax_highlight = models.CharField(max_length=50)  # For code editor
    docker_image = models.CharField(max_length=200, null=True, blank=True)  # Để run code
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.display_name
    
    class Meta:
        db_table = 'code_languages'


class CodeCourse(models.Model):
    """Khóa học lập trình"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'), 
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    thumbnail = CloudinaryField('thumbnail', blank=True, null=True, folder="course_thumbnails/")
    
    # Course info
    language = models.ForeignKey(CodeLanguage, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    estimated_hours = models.IntegerField(null=True, blank=True)
    
    # Author & publishing
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_courses')
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Stats
    enrollment_count = models.IntegerField(default=0)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    rating_count = models.IntegerField(default=0)
    
    # Settings
    is_free = models.BooleanField(default=True)
    requires_premium = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # SEO & Search
    tags = models.ManyToManyField('CodeCourseTag', blank=True)
    search_vector = SearchVectorField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'code_courses'
        indexes = [
            models.Index(fields=['status', 'is_featured', '-created_at']),
            models.Index(fields=['language', 'difficulty', '-enrollment_count']),
        ]


class CodeCourseTag(models.Model):
    """Tags cho khóa học"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6B7280')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'code_course_tags'


class CodeLesson(models.Model):
    """Bài học trong khóa học"""
    LESSON_TYPE_CHOICES = [
        ('theory', 'Theory'),           # Lý thuyết
        ('coding', 'Coding Exercise'),  # Bài tập code
        ('project', 'Project'),         # Dự án
        ('quiz', 'Quiz'),              # Trắc nghiệm
    ]
    
    course = models.ForeignKey(CodeCourse, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(null=True, blank=True)
    
    # Content
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, default='coding')
    theory_content = models.TextField(null=True, blank=True)  # HTML content cho theory
    
    # Coding exercise
    problem_statement = models.TextField(null=True, blank=True)  # Đề bài
    starter_code = models.TextField(null=True, blank=True)       # Code mẫu ban đầu
    solution_code = models.TextField(null=True, blank=True)      # Lời giải mẫu
    hints = models.JSONField(null=True, blank=True)             # Gợi ý theo bước
    
    # Test cases
    test_cases = models.JSONField(null=True, blank=True)        # Input/Output test cases
    hidden_test_cases = models.JSONField(null=True, blank=True) # Hidden tests
    
    # AI Configuration
    ai_prompt_template = models.TextField(null=True, blank=True) # Template cho AI feedback
    ai_difficulty_level = models.IntegerField(default=1)        # 1-10 độ khó cho AI
    
    # Settings
    order_index = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    estimated_time = models.IntegerField(null=True, blank=True)  # phút
    points_reward = models.IntegerField(default=10)
    
    # Stats
    completion_count = models.IntegerField(default=0)
    average_attempts = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    class Meta:
        db_table = 'code_lessons'
        unique_together = ['course', 'slug']
        indexes = [
            models.Index(fields=['course', 'order_index']),
            models.Index(fields=['lesson_type', 'is_published']),
        ]


class CodeEnrollment(models.Model):
    """Đăng ký học khóa học"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(CodeCourse, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # Progress tracking
    current_lesson = models.ForeignKey(
        CodeLesson, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='current_enrollments'
    )
    completed_lessons = models.ManyToManyField(
        CodeLesson, 
        through='CodeLessonProgress', 
        blank=True,
        related_name='completed_enrollments'
    )
    
    # Stats
    total_time_spent = models.IntegerField(default=0)  # minutes
    total_points = models.IntegerField(default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'code_enrollments'
        unique_together = ['user', 'course']


class CodeLessonProgress(models.Model):
    """Tiến độ từng bài học"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]
    
    enrollment = models.ForeignKey(CodeEnrollment, on_delete=models.CASCADE)
    lesson = models.ForeignKey(CodeLesson, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Stats
    attempts_count = models.IntegerField(default=0)
    time_spent = models.IntegerField(default=0)  # seconds
    points_earned = models.IntegerField(default=0)
    best_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'code_lesson_progress'
        unique_together = ['enrollment', 'lesson']


class CodeSubmission(models.Model):
    """Bài nộp code của học viên"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),         # Đang chờ chấm
        ('running', 'Running'),         # Đang run code
        ('passed', 'Passed'),           # Đạt
        ('failed', 'Failed'),           # Sai
        ('error', 'Error'),             # Lỗi runtime
        ('timeout', 'Timeout'),         # Quá thời gian
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(CodeLesson, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(CodeEnrollment, on_delete=models.CASCADE)
    
    # Code content
    submitted_code = models.TextField()
    language = models.ForeignKey(CodeLanguage, on_delete=models.CASCADE)
    
    # Execution results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_output = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    execution_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)  # seconds
    memory_used = models.IntegerField(null=True, blank=True)  # KB
    
    # Test results
    test_results = models.JSONField(null=True, blank=True)  # Results for each test case
    tests_passed = models.IntegerField(default=0)
    tests_total = models.IntegerField(default=0)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # AI Feedback
    ai_feedback = models.TextField(null=True, blank=True)
    ai_suggestions = models.JSONField(null=True, blank=True)
    ai_code_review = models.TextField(null=True, blank=True)
    ai_response_time = models.IntegerField(null=True, blank=True)  # ms
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    submission_count = models.IntegerField(default=1)  # Lần thử thứ mấy
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} #{self.submission_count}"
    
    class Meta:
        db_table = 'code_submissions'
        indexes = [
            models.Index(fields=['user', 'lesson', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]


class CodeExecutionSession(models.Model):
    """Session để chạy code - tracking real-time"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(CodeLesson, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    
    # Current state
    current_code = models.TextField(null=True, blank=True)
    language = models.ForeignKey(CodeLanguage, on_delete=models.CASCADE)
    
    # Session metadata
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    total_keystrokes = models.IntegerField(default=0)
    total_runs = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'code_execution_sessions'


class CodeHint(models.Model):
    """Gợi ý cho bài tập"""
    lesson = models.ForeignKey(CodeLesson, on_delete=models.CASCADE, related_name='lesson_hints')
    title = models.CharField(max_length=200)
    content = models.TextField()
    hint_type = models.CharField(max_length=50, default='general')  # general, syntax, logic, optimization
    order_index = models.IntegerField(default=0)
    
    # Conditions to show hint
    show_after_attempts = models.IntegerField(default=3)
    show_after_minutes = models.IntegerField(default=10)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'code_hints'


class CodeDiscussion(models.Model):
    """Discussion/Comments cho từng bài học"""
    lesson = models.ForeignKey(CodeLesson, on_delete=models.CASCADE, related_name='discussions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    code_snippet = models.TextField(null=True, blank=True)  # Nếu có share code
    
    # Voting system
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    
    # Status
    is_solution = models.BooleanField(default=False)  # Được đánh dấu là solution
    is_pinned = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'code_discussions'


class CodeDiscussionVote(models.Model):
    """Vote cho discussion"""
    VOTE_CHOICES = [
        (1, 'Upvote'),
        (-1, 'Downvote'),
    ]
    
    discussion = models.ForeignKey(CodeDiscussion, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'code_discussion_votes'
        unique_together = ['discussion', 'user']


class CodeReviewRequest(models.Model):
    """Yêu cầu review code từ AI hoặc mentor"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REVIEWER_CHOICES = [
        ('ai', 'AI Review'),
        ('mentor', 'Mentor Review'),
        ('peer', 'Peer Review'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submission = models.ForeignKey(CodeSubmission, on_delete=models.CASCADE)
    reviewer_type = models.CharField(max_length=20, choices=REVIEWER_CHOICES, default='ai')
    
    # Request details
    specific_questions = models.TextField(null=True, blank=True)
    focus_areas = models.JSONField(null=True, blank=True)  # performance, readability, logic
    
    # Review results
    review_content = models.TextField(null=True, blank=True)
    suggestions = models.JSONField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_given')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'code_review_requests'


class CodeCourseRating(models.Model):
    """Đánh giá khóa học"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(CodeCourse, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review = models.TextField(null=True, blank=True)
    
    # Detailed ratings
    content_quality = models.IntegerField(null=True, blank=True)
    difficulty_appropriate = models.IntegerField(null=True, blank=True)
    instructor_helpful = models.IntegerField(null=True, blank=True)
    
    is_recommended = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'code_course_ratings'
        unique_together = ['user', 'course']


class CodeAchievement(models.Model):
    """Thành tựu/Badges cho user"""
    ACHIEVEMENT_TYPE_CHOICES = [
        ('completion', 'Completion'),   # Hoàn thành khóa học
        ('streak', 'Streak'),          # Streak ngày học
        ('mastery', 'Mastery'),        # Thành thạo ngôn ngữ
        ('helping', 'Helping'),        # Giúp đỡ người khác
        ('challenge', 'Challenge'),    # Thử thách đặc biệt
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)  # Font awesome class
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPE_CHOICES)
    
    # Conditions
    required_value = models.IntegerField(default=1)  # Số lượng cần đạt
    language = models.ForeignKey(CodeLanguage, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(CodeCourse, on_delete=models.CASCADE, null=True, blank=True)
    
    # Rewards
    points_reward = models.IntegerField(default=0)
    is_rare = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'code_achievements'


class UserCodeAchievement(models.Model):
    """Thành tựu của user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(CodeAchievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    # Context
    related_course = models.ForeignKey(CodeCourse, on_delete=models.SET_NULL, null=True, blank=True)
    related_submission = models.ForeignKey(CodeSubmission, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'user_code_achievements'
        unique_together = ['user', 'achievement']


# Cập nhật User model để thêm coding stats
class UserCodingProfile(models.Model):
    """Profile mở rộng cho coding"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coding_profile')
    
    # Stats
    total_submissions = models.IntegerField(default=0)
    successful_submissions = models.IntegerField(default=0)
    total_courses_enrolled = models.IntegerField(default=0)
    total_courses_completed = models.IntegerField(default=0)
    total_coding_time = models.IntegerField(default=0)  # minutes
    total_points = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)  # days
    longest_streak = models.IntegerField(default=0)
    
    # Preferences
    preferred_language = models.ForeignKey(CodeLanguage, on_delete=models.SET_NULL, null=True, blank=True)
    coding_theme = models.CharField(max_length=20, default='vs-dark')  # vs-dark, vs-light, monokai
    font_size = models.IntegerField(default=14)
    auto_save = models.BooleanField(default=True)
    
    # Learning path
    skill_level = models.CharField(max_length=20, default='beginner')
    learning_goals = models.JSONField(null=True, blank=True)
    
    last_coding_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_coding_profiles'


class DocumentDownloadLog(models.Model):
    """Track document downloads for rate limiting"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'document_download_logs'
        indexes = [
            models.Index(fields=['user', 'downloaded_at']),
        ]


class SearchHistory(models.Model):
    """Track user search history and popular searches"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=255)
    result_count = models.IntegerField(default=0)
    clicked_result_id = models.IntegerField(null=True, blank=True)
    clicked_result_type = models.CharField(max_length=20, null=True, blank=True)  # document, course, university
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_history'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['query', '-created_at']),
        ]