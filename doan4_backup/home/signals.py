from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import DocumentView, DocumentDownload, DocumentLike, UserActivity, Notification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=DocumentView)
def update_view_count_on_create(sender, instance, created, **kwargs):
    """Cập nhật số lượt xem khi có view mới"""
    if created:
        try:
            document = instance.document
            # Đếm lại tổng số view
            view_count = DocumentView.objects.filter(document=document).count()
            document.view_count = view_count
            document.save(update_fields=['view_count', 'updated_at'])
            
            logger.info(f"Updated view count for document {document.id}: {view_count}")
            
        except Exception as e:
            logger.error(f"Error updating view count: {str(e)}")

@receiver(post_save, sender=DocumentDownload)
def update_download_count_on_create(sender, instance, created, **kwargs):
    """Cập nhật số lượt tải khi có download mới"""
    if created:
        try:
            document = instance.document
            # Đếm lại tổng số download
            download_count = DocumentDownload.objects.filter(document=document).count()
            document.download_count = download_count
            document.save(update_fields=['download_count', 'updated_at'])
            
            # Tạo thông báo cho người upload nếu không phải chính họ tải
            if document.uploaded_by != instance.user:
                Notification.objects.create(
                    user=document.uploaded_by,
                    title="Tài liệu được tải xuống",
                    message=f'Tài liệu "{document.title}" của bạn vừa được {instance.user.get_full_name() or instance.user.username} tải xuống.',
                    notification_type='info',
                    document=document
                )
            
            logger.info(f"Updated download count for document {document.id}: {download_count}")
            
        except Exception as e:
            logger.error(f"Error updating download count: {str(e)}")

@receiver([post_save, post_delete], sender=DocumentLike)
def update_like_count(sender, instance, **kwargs):
    """Cập nhật số lượt thích khi có like/unlike"""
    try:
        document = instance.document
        # Đếm lại tổng số like
        like_count = DocumentLike.objects.filter(document=document).count()
        document.like_count = like_count
        document.save(update_fields=['like_count', 'updated_at'])
        
        # Tạo thông báo cho người upload khi có like mới (chỉ khi post_save và created)
        if (hasattr(kwargs, 'created') and kwargs.get('created') and 
            document.uploaded_by != instance.user):
            
            Notification.objects.create(
                user=document.uploaded_by,
                title="Tài liệu được thích",
                message=f'{instance.user.get_full_name() or instance.user.username} đã thích tài liệu "{document.title}" của bạn.',
                notification_type='success',
                document=document
            )
        
        logger.info(f"Updated like count for document {document.id}: {like_count}")
        
    except Exception as e:
        logger.error(f"Error updating like count: {str(e)}")

@receiver(post_save, sender=DocumentView)
def create_view_activity(sender, instance, created, **kwargs):
    """Tạo log hoạt động khi xem tài liệu"""
    if created and instance.user:
        try:
            UserActivity.objects.create(
                user=instance.user,
                action='view_document',
                description=f'Xem tài liệu "{instance.document.title}"',
                document=instance.document,
                ip_address=instance.ip_address,
                user_agent=instance.user_agent
            )
        except Exception as e:
            logger.error(f"Error creating view activity: {str(e)}")

@receiver(post_save, sender=DocumentDownload)
def create_download_activity(sender, instance, created, **kwargs):
    """Tạo log hoạt động khi tải tài liệu"""
    if created:
        try:
            UserActivity.objects.create(
                user=instance.user,
                action='download_document',
                description=f'Tải tài liệu "{instance.document.title}"',
                document=instance.document,
                ip_address=instance.ip_address
            )
        except Exception as e:
            logger.error(f"Error creating download activity: {str(e)}")

@receiver(post_save, sender=DocumentLike)
def create_like_activity(sender, instance, created, **kwargs):
    """Tạo log hoạt động khi thích tài liệu"""
    if created:
        try:
            UserActivity.objects.create(
                user=instance.user,
                action='like_document',
                description=f'Thích tài liệu "{instance.document.title}"',
                document=instance.document
            )
        except Exception as e:
            logger.error(f"Error creating like activity: {str(e)}")

@receiver(post_delete, sender=DocumentLike)
def create_unlike_activity(sender, instance, **kwargs):
    """Tạo log hoạt động khi bỏ thích tài liệu"""
    try:
        UserActivity.objects.create(
            user=instance.user,
            action='unlike_document',
            description=f'Bỏ thích tài liệu "{instance.document.title}"',
            document=instance.document
        )
    except Exception as e:
        logger.error(f"Error creating unlike activity: {str(e)}")

# Signal để tự động tạo thông báo khi tài liệu được duyệt
from .models import Document

@receiver(post_save, sender=Document)
def document_status_changed(sender, instance, created, **kwargs):
    """Thông báo khi trạng thái tài liệu thay đổi"""
    if not created:  # Chỉ xử lý khi update, không phải tạo mới
        try:
            # Lấy instance cũ từ database
            old_instance = Document.objects.filter(id=instance.id).first()
            
            if old_instance and old_instance.status != instance.status:
                # Tạo thông báo dựa trên trạng thái mới
                if instance.status == 'approved':
                    Notification.objects.create(
                        user=instance.uploaded_by,
                        title="Tài liệu được duyệt",
                        message=f'Tài liệu "{instance.title}" của bạn đã được phê duyệt và hiển thị công khai.',
                        notification_type='success',
                        document=instance
                    )
                elif instance.status == 'rejected':
                    Notification.objects.create(
                        user=instance.uploaded_by,
                        title="Tài liệu bị từ chối",
                        message=f'Tài liệu "{instance.title}" của bạn đã bị từ chối. Lý do: {instance.admin_notes or "Không có lý do cụ thể"}',
                        notification_type='error',
                        document=instance
                    )
                
                # Tạo log hoạt động cho admin
                UserActivity.objects.create(
                    user=instance.uploaded_by,
                    action=f'document_{instance.status}',
                    description=f'Tài liệu "{instance.title}" đã được {instance.status}',
                    document=instance
                )
                
        except Exception as e:
            logger.error(f"Error handling document status change: {str(e)}")