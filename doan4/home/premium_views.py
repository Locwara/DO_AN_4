from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta

from .models import User, PremiumTransaction, CodeEnrollment, DocumentDownloadLog

# VNPay Configuration (from settings)
VNPAY_TMN_CODE = getattr(settings, 'VNPAY_TMN_CODE', '7S2U6NBX')
VNPAY_HASH_SECRET = getattr(settings, 'VNPAY_HASH_SECRET', 'ZFM9RGJD793MWQS8V20ZSVTQCXKW2V0Z')
VNPAY_URL = getattr(settings, 'VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html')
SITE_URL = getattr(settings, 'SITE_URL', 'http://localhost:8000')

# Premium Configuration
PREMIUM_PRICE = 100000  # 100k VND per month
PREMIUM_DURATION_DAYS = 30  # 1 month = 30 days
FREE_DOWNLOAD_LIMIT = 10  # downloads per day
FREE_COURSE_LIMIT = 3  # max courses

def create_vnpay_signature(params, secret_key):
    """Tạo chữ ký VNPay"""
    filtered_params = {k: v for k, v in params.items() if k != 'vnp_SecureHash' and v is not None and str(v) != ''}
    sorted_params = sorted(filtered_params.items())
    query_parts = [f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params]
    sign_data = "&".join(query_parts)
    h = hmac.new(secret_key.encode('utf-8'), sign_data.encode('utf-8'), hashlib.sha512)
    return h.hexdigest()

def get_client_ip(request):
    """Lấy IP client"""
    ip_headers = ['HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'REMOTE_ADDR']
    for header in ip_headers:
        ip = request.META.get(header)
        if ip:
            ip = ip.split(',')[0].strip()
            if ip and ip != '127.0.0.1' and not ip.startswith('192.168.'):
                return ip
    return '203.162.71.6'

@login_required
def premium_upgrade_view(request):
    """Trang giới thiệu premium"""
    user = request.user
    
    # Check nếu đã premium và còn trên 5 ngày
    if user.is_premium and user.premium_expiry:
        days_left = (user.premium_expiry - timezone.now()).days
        # If premium and more than 4 days left (i.e., 5 days or more)
        if days_left >= 5:
            messages.info(request, 'Bạn đã là thành viên Premium và gói của bạn vẫn còn hơn 5 ngày. Bạn có thể gia hạn khi gói của bạn còn dưới 5 ngày!')
            return redirect('premium_info') # Redirect to premium info page, not dashboard
    elif user.is_premium and not user.premium_expiry:
        # This case should ideally not happen if user.is_premium is true, but as a safeguard
        messages.info(request, 'Bạn đã là thành viên Premium! Vui lòng kiểm tra thông tin gói của bạn.')
        return redirect('premium_info')
    
    # Thống kê user hiện tại
    today = timezone.now().date()
    downloads_today = DocumentDownloadLog.objects.filter(
        user=user,
        downloaded_at__date=today
    ).count()
    
    enrolled_courses = CodeEnrollment.objects.filter(user=user).count()
    
    context = {
        'premium_price': PREMIUM_PRICE,
        'downloads_today': downloads_today,
        'download_limit': FREE_DOWNLOAD_LIMIT,
        'enrolled_courses': enrolled_courses,
        'course_limit': FREE_COURSE_LIMIT,
    }
    
    return render(request, 'premium/upgrade.html', context)

# Sửa trong views.py

from django.utils import timezone as django_timezone
import pytz

# Thêm vào đầu file
vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')

@login_required
def process_premium_payment(request):
    """Xử lý thanh toán premium qua VNPay"""
    print("\n" + "="*50)
    print("[PREMIUM] Starting payment process")
    print(f"[PREMIUM] User: {request.user.username} (ID: {request.user.id})")
    print("="*50 + "\n")
    
    try:
        user = request.user
        print(f"[PREMIUM] User is_premium: {user.is_premium}")
        
        # Check nếu đã premium và còn trên 5 ngày
        if user.is_premium and user.premium_expiry:
            days_left = (user.premium_expiry - timezone.now()).days
            if days_left >= 5:
                print(f"[PREMIUM] User already premium with {days_left} days left, redirecting...")
                messages.error(request, 'Gói Premium của bạn vẫn còn hạn trên 5 ngày. Bạn không cần gia hạn lúc này.')
                return redirect('premium_info')
        
        # ALWAYS create new transaction to avoid expired ones
        print(f"[PREMIUM] Creating new transaction...")
        # Mark ALL old pending transactions as failed
        old_count = PremiumTransaction.objects.filter(
            user=user,
            status='pending'
        ).update(status='failed')
        print(f"[PREMIUM] Marked {old_count} old transactions as failed")
        
        # Tạo transaction mới
        with transaction.atomic():
            premium_transaction = PremiumTransaction.objects.create(
                user=user,
                plan_type='monthly',
                amount=Decimal(str(PREMIUM_PRICE)),
                currency='VND',
                payment_method='VNPay',
                status='pending'
            )
            
            print(f"[PREMIUM] Created new transaction ID: {premium_transaction.id}")
            
            # Lưu transaction ID vào session
            request.session['premium_transaction_id'] = premium_transaction.id
            request.session.save()
            print(f"[PREMIUM] Saved transaction to session")
        
        # ===== FIX: Sử dụng timezone Việt Nam =====
        vn_now = datetime.now(vietnam_tz)
        
        # Tạo VNPay parameters
        print(f"[PREMIUM] Building VNPay parameters...")
        print(f"[PREMIUM] Transaction ID: {premium_transaction.id}")
        print(f"[PREMIUM] Amount: {PREMIUM_PRICE}")
        print(f"[PREMIUM] Vietnam time: {vn_now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        vnpay_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': VNPAY_TMN_CODE,  # DFGFDNTM
            'vnp_Amount': int(PREMIUM_PRICE * 100),
            'vnp_CreateDate': vn_now.strftime('%Y%m%d%H%M%S'),  # FIX: Dùng VN time
            'vnp_CurrCode': 'VND',
            'vnp_IpAddr': get_client_ip(request),
            'vnp_Locale': 'vn',
            'vnp_OrderInfo': f'Nang-cap-Premium-{premium_transaction.id}',
            'vnp_OrderType': 'other',
            'vnp_ReturnUrl': f"{SITE_URL}{reverse('premium_return')}",
            'vnp_TxnRef': str(premium_transaction.id),
            # FIX: Giảm timeout xuống 15 phút (thay vì 30)
            'vnp_ExpireDate': (vn_now + timedelta(minutes=15)).strftime('%Y%m%d%H%M%S'),
        }
        
        # Tạo signature
        print(f"[PREMIUM] Creating VNPay signature...")
        signature = create_vnpay_signature(vnpay_params, VNPAY_HASH_SECRET)  # FVTT5K53USTT43KOPDD8UICRSGH8TYP5
        vnpay_params['vnp_SecureHash'] = signature
        print(f"[PREMIUM] Signature: {signature[:20]}...")
        print(f"[PREMIUM] Create Date: {vnpay_params['vnp_CreateDate']}")
        print(f"[PREMIUM] Expire Date: {vnpay_params['vnp_ExpireDate']}")
        
        # Tạo URL
        query_string = urllib.parse.urlencode(vnpay_params, quote_via=urllib.parse.quote)
        vnpay_url = f"{VNPAY_URL}?{query_string}"
        
        print(f"[PREMIUM] VNPay URL created (length: {len(vnpay_url)})")
        print(f"\n[PREMIUM] FULL VNPAY URL:")
        print(vnpay_url)
        print("\n" + "="*50)
        print("[PREMIUM] Redirect to VNPay")
        print("="*50 + "\n")
        
        return HttpResponseRedirect(vnpay_url)
        
    except Exception as e:
        import traceback
        print(f"[PREMIUM ERROR] {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        return redirect('premium_upgrade')
def premium_return(request):
    """Callback từ VNPay"""
    import logging
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*50)
    print("[PREMIUM RETURN] VNPay Callback Received")
    print(f"Callback URL: {request.get_full_path()}")
    print("-" * 20)
    
    input_data = request.GET.dict()
    for key, value in input_data.items():
        print(f"- {key}: {value}")
    print("="*50 + "\n")

    try:
        vnp_SecureHash = input_data.get('vnp_SecureHash')
        vnp_TxnRef = input_data.get('vnp_TxnRef')
        vnp_ResponseCode = input_data.get('vnp_ResponseCode')
        
        if not all([vnp_SecureHash, vnp_TxnRef, vnp_ResponseCode]):
            print("[PREMIUM RETURN ERROR] Missing required VNPay parameters!")
            messages.error(request, 'Dữ liệu VNPay trả về không hợp lệ.')
            return redirect('premium_upgrade')

        # Verify signature
        verify_params = {k: v for k, v in input_data.items() if k != 'vnp_SecureHash'}
        expected_hash = create_vnpay_signature(verify_params, VNPAY_HASH_SECRET)
        
        print(f"[PREMIUM RETURN] Our Calculated Hash: {expected_hash}")
        print(f"[PREMIUM RETURN] VNPay's Hash:        {vnp_SecureHash}")

        if vnp_SecureHash.lower() != expected_hash.lower():
            print("[PREMIUM RETURN ERROR] Signature mismatch!")
            logger.error(f'Invalid VNPay signature for transaction {vnp_TxnRef}')
            messages.error(request, 'Chữ ký không hợp lệ. Giao dịch bị hủy để đảm bảo an toàn.')
            return redirect('premium_upgrade')
        
        print("[PREMIUM RETURN] Signature verified successfully!")
        
        # Lấy transaction
        try:
            premium_transaction = PremiumTransaction.objects.get(id=vnp_TxnRef)
            print(f"[PREMIUM RETURN] Found transaction: {premium_transaction.id}, Status: {premium_transaction.status}")
        except PremiumTransaction.DoesNotExist:
            print(f"[PREMIUM RETURN ERROR] Transaction with ID {vnp_TxnRef} not found!")
            messages.error(request, f'Không tìm thấy giao dịch với mã {vnp_TxnRef}.')
            return redirect('premium_upgrade')

        if premium_transaction.status != 'pending':
            print(f"[PREMIUM RETURN WARNING] Transaction {vnp_TxnRef} is already processed. Status: {premium_transaction.status}")
            messages.warning(request, 'Giao dịch này đã được xử lý trước đó.')
            if premium_transaction.status == 'completed':
                return redirect('dashboard')
            else:
                return redirect('premium_upgrade')

        if vnp_ResponseCode == '00':
            print(f"[PREMIUM RETURN] Payment SUCCESS (Code: 00). Activating premium for user {premium_transaction.user.id}")
            # Thanh toán thành công
            with transaction.atomic():
                premium_transaction.status = 'completed'
                premium_transaction.transaction_id = input_data.get('vnp_TransactionNo', '')
                premium_transaction.started_at = timezone.now()
                # Calculate new expiry date based on cumulative logic
                user = premium_transaction.user
                
                if user.is_premium and user.premium_expiry and user.premium_expiry > timezone.now():
                    # If user has an existing active premium, add to their current expiry
                    new_expiry = user.premium_expiry + timedelta(days=PREMIUM_DURATION_DAYS)
                    print(f"[PREMIUM RETURN] Cumulative renewal: Old expiry {user.premium_expiry}, New expiry {new_expiry}")
                else:
                    # Otherwise, set expiry from now
                    new_expiry = timezone.now() + timedelta(days=PREMIUM_DURATION_DAYS)
                    print(f"[PREMIUM RETURN] Fresh activation: New expiry {new_expiry}")
                    
                premium_transaction.expires_at = new_expiry
                premium_transaction.save()
                
                # Cập nhật user
                user.is_premium = True
                user.premium_activated_at = timezone.now() # Update activation time to now
                user.premium_expiry = new_expiry
                user.save()
            
            logger.info(f'Premium activated for user {user.id} until {user.premium_expiry}')
            
            # Save session to ensure it persists after redirect
            request.session.modified = True
            request.session.save()
            
            return redirect('premium_success')
        else:
            print(f"[PREMIUM RETURN] Payment FAILED (Code: {vnp_ResponseCode}).")
            # Thanh toán thất bại
            premium_transaction.status = 'failed'
            premium_transaction.save()
            
            logger.warning(f'Payment failed for transaction {vnp_TxnRef}, code: {vnp_ResponseCode}')
            messages.error(request, f'Thanh toán thất bại. Mã lỗi VNPay: {vnp_ResponseCode}')
            return redirect('premium_upgrade')
            
    except Exception as e:
        import traceback
        print(f"[PREMIUM RETURN CRITICAL ERROR] {str(e)}")
        print(traceback.format_exc())
        logger.error(f"Critical error in VNPay callback: {str(e)}")
        messages.error(request, f'Đã xảy ra lỗi nghiêm trọng khi xử lý thanh toán.')
        return redirect('premium_upgrade')

# Helper functions for restrictions
def check_download_limit(user):
    """Check if user can download"""
    if user.is_premium:
        return True, 0
    
    today = timezone.now().date()
    downloads_today = DocumentDownloadLog.objects.filter(
        user=user,
        downloaded_at__date=today
    ).count()
    
    if downloads_today >= FREE_DOWNLOAD_LIMIT:
        return False, downloads_today
    
    return True, downloads_today

def check_course_enrollment_limit(user):
    """Check if user can enroll in more courses"""
    if user.is_premium:
        return True, 0
    
    enrolled_count = CodeEnrollment.objects.filter(user=user).count()
    
    if enrolled_count >= FREE_COURSE_LIMIT:
        return False, enrolled_count
    
    return True, enrolled_count

def log_download(user, document, ip_address=None):
    """Log document download"""
    if not user or not document:
        return
    
    try:
        DocumentDownloadLog.objects.create(
            user=user,
            document=document,
            ip_address=ip_address
        )
    except Exception as e:
        # Log error but don't fail the download
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to log download: {str(e)}')

@login_required
def premium_info_view(request):
    """Premium information page"""
    user = request.user
    
    # Get user's premium transactions
    transactions = PremiumTransaction.objects.filter(
        user=user
    ).order_by('-created_at')
    
    context = {
        'transactions': transactions,
    }
    
    return render(request, 'premium/info.html', context)

def premium_success_view(request):
    """Premium success page after payment"""
    # Don't require login - user might have just returned from payment gateway
    if not request.user.is_authenticated:
        messages.info(request, 'Vui lòng đăng nhập để xem thông tin premium của bạn.')
        return redirect('home_login')
    
    return render(request, 'premium/success.html')
