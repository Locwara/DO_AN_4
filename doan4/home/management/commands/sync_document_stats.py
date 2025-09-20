.from django.core.management.base import BaseCommand
from django.db.models import Count
from your_app.models import Document, DocumentView, DocumentDownload, DocumentLike

class Command(BaseCommand):
    help = 'Đồng bộ thống kê tài liệu từ các bảng liên quan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--document-id',
            type=int,
            help='ID của tài liệu cụ thể cần sync (tùy chọn)',
        )

    def handle(self, *args, **options):
        document_id = options.get('document_id')
        
        if document_id:
            try:
                documents = Document.objects.filter(id=document_id)
                if not documents.exists():
                    self.stdout.write(
                        self.style.ERROR(f'Không tìm thấy tài liệu với ID: {document_id}')
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Lỗi khi tìm tài liệu: {str(e)}')
                )
                return
        else:
            documents = Document.objects.all()
        
        total_updated = 0
        
        self.stdout.write('Bắt đầu đồng bộ thống kê tài liệu...')
        
        for doc in documents:
            try:
                # Cập nhật view count
                view_count = DocumentView.objects.filter(document=doc).count()
                
                # Cập nhật download count
                download_count = DocumentDownload.objects.filter(document=doc).count()
                
                # Cập nhật like count
                like_count = DocumentLike.objects.filter(document=doc).count()
                
                # Kiểm tra xem có thay đổi không
                old_stats = (doc.view_count, doc.download_count, doc.like_count)
                new_stats = (view_count, download_count, like_count)
                
                if old_stats != new_stats:
                    # Cập nhật database
                    doc.view_count = view_count
                    doc.download_count = download_count
                    doc.like_count = like_count
                    doc.save(update_fields=['view_count', 'download_count', 'like_count'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Cập nhật "{doc.title[:50]}...": '
                            f'{view_count} views, {download_count} downloads, {like_count} likes'
                        )
                    )
                    total_updated += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'- Không có thay đổi cho "{doc.title[:50]}..."')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Lỗi khi cập nhật tài liệu "{doc.title}": {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Hoàn thành! Đã cập nhật {total_updated}/{documents.count()} tài liệu'
            )
        )

    def get_version(self):
        return "1.0.0"