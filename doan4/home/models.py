from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from cloudinary.models import CloudinaryField
import uuid


class User(AbstractUser):
    """Mở rộng bảng auth_user của Django"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    avatar = CloudinaryField('avatar', blank=True, null=True, folder="avatars/")
    bio = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    premium_expiry = models.DateTimeField(null=True, blank=True)
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
    file_type = models.CharField(max_length=50, null=True, blank=True)
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
        ('system', 'System'),
    ]

    room = models.ForeignKey('ChatRoom', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    file_url = CloudinaryField('chat_file', resource_type='raw', blank=True, null=True, folder="chat_files/")
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"

    class Meta:
        db_table = 'chat_messages'


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