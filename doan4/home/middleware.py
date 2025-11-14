from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from .models import User

class PremiumExpiryMiddleware(MiddlewareMixin):
    """Middleware to check and deactivate expired premium accounts"""
    
    def process_request(self, request):
        if request.user.is_authenticated and request.user.is_premium:
            # Check if premium has expired
            if request.user.premium_expiry and request.user.premium_expiry < timezone.now():
                # Deactivate premium
                request.user.is_premium = False
                request.user.save(update_fields=['is_premium'])
                
                # Optional: Add a message to notify user
                from django.contrib import messages
                messages.warning(
                    request, 
                    'Tài khoản Premium của bạn đã hết hạn. Vui lòng gia hạn để tiếp tục sử dụng!'
                )
        
        return None
