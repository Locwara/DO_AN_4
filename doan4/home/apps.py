from django.apps import AppConfig


class YourAppConfig(AppConfig):
    """
    Cấu hình ứng dụng StudyShare
    Thay 'your_app' bằng tên app thực tế của bạn
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'  # Thay bằng tên app thực tế
    verbose_name = 'StudyShare - Document Management'
    
    def ready(self):
        """
        Được gọi khi Django khởi tạo ứng dụng
        Import signals để đăng ký các signal handlers
        """
        try:
            # Import signals để đăng ký các signal handlers
            import your_app.signals  # Thay 'your_app' bằng tên app thực tế
        except ImportError as e:
            print(f"Warning: Could not import signals: {e}")
            
        # Có thể thêm các setup khác ở đây
        self.setup_logging()
        self.check_required_settings()
    
    def setup_logging(self):
        """Setup logging cho app"""
        import logging
        import os
        from django.conf import settings
        
        # Tạo logger cho app
        logger = logging.getLogger(self.name)
        
        # Chỉ setup nếu chưa có handler
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def check_required_settings(self):
        """Kiểm tra các cài đặt bắt buộc"""
        from django.conf import settings
        import warnings
        
        # Kiểm tra Cloudinary config
        if not hasattr(settings, 'CLOUDINARY_STORAGE'):
            warnings.warn(
                "CLOUDINARY_STORAGE not configured. File uploads may not work properly.",
                UserWarning
            )
        
        # Kiểm tra các setting khác nếu cần
        required_settings = [
            'MEDIA_URL',
            'MEDIA_ROOT',
        ]
        
        for setting_name in required_settings:
            if not hasattr(settings, setting_name):
                warnings.warn(
                    f"Required setting {setting_name} is not configured.",
                    UserWarning
                )