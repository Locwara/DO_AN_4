# Premium Integration với VNPay

## Tổng quan

Chức năng premium cho phép người dùng nâng cấp tài khoản để sử dụng không giới hạn.

## Tính năng

### Premium Features
- Tải tài liệu không giới hạn (free: 10 lần/ngày)
- Đăng ký khóa học không giới hạn (free: 3 khóa)
- Huy hiệu Premium trên profile và navbar
- Sử dụng vĩnh viễn (trả 1 lần 100,000 VND)

### Models

#### User
- `is_premium`: Boolean flag
- `premium_activated_at`: Ngày kích hoạt premium

#### PremiumTransaction
- Lưu trữ lịch sử giao dịch nâng cấp premium
- Tích hợp với VNPay sandbox

#### DocumentDownloadLog
- Track số lần download của user
- Sử dụng để enforce giới hạn cho free users

## Flow thanh toán

1. User click "Nâng cấp Premium"
2. System tạo PremiumTransaction với status='pending'
3. Redirect user đến VNPay với params đã ký
4. User thanh toán trên VNPay sandbox
5. VNPay callback về `premium_return` URL
6. Verify signature và update transaction
7. Nếu thành công: set user.is_premium=True

## VNPay Configuration

```python
# settings.py
VNPAY_TMN_CODE = '7S2U6NBX'  # Sandbox code
VNPAY_HASH_SECRET = 'ZFM9RGJD793MWQS8V20ZSVTQCXKW2V0Z'
VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
SITE_URL = 'http://localhost:8000'
```

## URLs

- `/premium/upgrade/` - Trang giới thiệu premium
- `/premium/process/` - Xử lý thanh toán VNPay
- `/premium/return/` - Callback từ VNPay

## Testing

### VNPay Sandbox Test Cards

```
Ngân hàng: NCB
Số thẻ: 9704198526191432198
Tên chủ thẻ: NGUYEN VAN A
Ngày phát hành: 07/15
Mật khẩu OTP: 123456
```

### Test Flow

1. Đăng nhập với user thường
2. Truy cập `/premium/upgrade/`
3. Click "Nâng cấp ngay với VNPay"
4. Nhập thông tin test card
5. Verify redirect về dashboard với premium badge

## Restrictions

### Download Limit
```python
from .premium_views import check_download_limit

can_download, count = check_download_limit(user)
if not can_download:
    # Show upgrade message
```

### Course Enrollment Limit
```python
from .premium_views import check_course_enrollment_limit

can_enroll, count = check_course_enrollment_limit(user)
if not can_enroll:
    # Show upgrade message
```

## Admin

- `/admin/home/premiumtransaction/` - Quản lý giao dịch
- `/admin/home/documentdownloadlog/` - Xem log downloads

## Security Notes

1. VNPay signature được verify ở callback
2. CSRF token required cho tất cả POST requests
3. Login required cho premium URLs
4. Transaction IDs are unique and sequential

## Deployment Notes

1. Update `SITE_URL` trong settings.py cho production
2. Đổi sang VNPay production credentials
3. Setup logging cho VNPay transactions
4. Configure proper error monitoring

## Future Enhancements

- [ ] Email notification khi upgrade thành công
- [ ] Premium membership tiers (monthly, yearly)
- [ ] Refund functionality
- [ ] Analytics dashboard cho admin
- [ ] Automatic retry cho failed transactions
