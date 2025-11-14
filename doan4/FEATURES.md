# Tổng quan chức năng dự án

Dự án này là một hệ thống web đa chức năng được xây dựng trên nền tảng Django, bao gồm các tính năng chính liên quan đến quản lý người dùng, tài liệu, khóa học lập trình, giải bài tập bằng AI, và chat thời gian thực.

## 1. Module Quản lý Người dùng và Xác thực (App: `home`)

Module này xử lý tất cả các nghiệp vụ liên quan đến tài khoản người dùng.

### 1.1. Xác thực
- **Đăng ký:** Người dùng mới có thể tạo tài khoản.
- **Đăng nhập / Đăng xuất:** Cơ chế xác thực người dùng an toàn.
- **Quên mật khẩu:** Người dùng có thể yêu cầu đặt lại mật khẩu qua email.
- **Đặt lại mật khẩu:** Thay đổi mật khẩu sau khi xác thực qua email.

### 1.2. Quản lý hồ sơ
- **Xem hồ sơ:** Người dùng có thể xem thông tin cá nhân của mình.
- **Chỉnh sửa hồ sơ:** Cho phép người dùng cập nhật thông tin cá nhân.
- **Thay đổi mật khẩu:** Người dùng đã đăng nhập có thể tự đổi mật khẩu.

### 1.3. Phân quyền
- **Middleware kiểm tra đăng nhập (`LoginRequiredMiddleware`):** Tự động yêu cầu đăng nhập cho các khu vực được bảo vệ.
- **Decorators phân quyền:** Sử dụng các decorator như `@admin_required` để giới hạn quyền truy cập vào các chức năng quản trị cụ thể.

## 2. Module Quản lý Tài liệu (Apps: `home`, `uploads`)

Cung cấp các chức năng để người dùng chia sẻ và quản lý tài liệu học tập.

### 2.1. Chức năng chính
- **Tải lên tài liệu:** Người dùng có thể tải lên các tệp tài liệu (hỗ trợ nhiều định dạng như .pdf, .doc, .xls).
- **Xem danh sách tài liệu:** Hiển thị danh sách các tài liệu có trên hệ thống, kèm bộ lọc và tìm kiếm.
- **Xem chi tiết tài liệu:** Xem thông tin chi tiết về một tài liệu cụ thể.
- **Tải xuống tài liệu:** Cho phép người dùng tải tài liệu về máy.

### 2.2. Theo dõi và Thống kê
- **Lịch sử tải xuống (`DocumentDownloadLog`):** Ghi lại thông tin mỗi khi một tài liệu được tải xuống.
- **Đếm lượt xem/tải:** Theo dõi và hiển thị số lượt xem và lượt tải của tài liệu.

## 3. Module Khóa học Lập trình (App: `home`)

Xây dựng một hệ thống học lập trình trực tuyến.

### 3.1. Quản lý (dành cho Quản trị viên)
- **Quản lý khóa học (`CodeCourse`):** Tạo, chỉnh sửa, và xóa các khóa học lập trình.
- **Quản lý bài học (`CodeLesson`):** Thêm, sửa, xóa các bài học trong một khóa học.
- **Trình soạn thảo code:** Tích hợp trình soạn thảo mã nguồn (ví dụ: Ace Editor) để quản lý nội dung bài học.

### 3.2. Học viên
- **Danh sách khóa học:** Xem tất cả các khóa học có sẵn.
- **Chi tiết khóa học:** Xem nội dung chi tiết của từng khóa học và các bài học bên trong.
- **Dashboard học tập:** Giao diện tổng quan về tiến độ học tập của người dùng.
- **Nộp bài và Chấm điểm:** Hệ thống cho phép thực thi code, chạy với các test case và chấm điểm tự động.

### 3.3. Phản hồi Code bằng AI (Code with AI)
- **Tích hợp AI Review:** Sau khi người dùng nộp bài giải, hệ thống có khả năng (hiện đang tắt) gửi code đến dịch vụ AI (Gemini).
- **Nhận xét chuyên sâu:** AI đóng vai trò là một mentor, đưa ra các nhận xét về logic, cách tiếp cận, điểm mạnh, điểm yếu và gợi ý tối ưu hóa cho đoạn code của người dùng.

## 4. Module AI - Giải bài tập bằng hình ảnh (App: `home`)

Tích hợp trí tuệ nhân tạo để hỗ trợ người dùng giải bài tập.

### 4.1. Chức năng
- **Tải lên hình ảnh:** Người dùng chụp và tải lên hình ảnh chứa câu hỏi hoặc bài tập.
- **Xử lý AI:** Hệ thống gửi hình ảnh đến một dịch vụ AI bên ngoài để phân tích và đưa ra lời giải.
- **Lịch sử lời giải:** Người dùng có thể xem lại lịch sử các bài tập đã được giải.
- **Xem chi tiết lời giải:** Xem nội dung chi tiết của lời giải do AI cung cấp.

## 5. Module Chat Thời gian thực (App: `home`)

Cung cấp một nền tảng để người dùng có thể trò chuyện với nhau.

### 5.1. Quản lý phòng Chat
- **Tạo phòng chat:** Người dùng có thể tạo phòng chat mới, có thể đặt mật khẩu bảo vệ.
- **Danh sách phòng chat:** Hiển thị danh sách các phòng chat đang hoạt động.
- **Tham gia phòng chat:** Người dùng có thể tham gia vào các phòng chat (nhập mật khẩu nếu được yêu cầu).
- **Chỉnh sửa phòng chat:** Chủ phòng có thể chỉnh sửa thông tin của phòng.

### 5.2. Tương tác
- **Nhắn tin thời gian thực:** Gửi và nhận tin nhắn ngay lập tức (sử dụng Django Channels và WebSockets).
- **Hiển thị thành viên:** Xem danh sách các thành viên đang có mặt trong phòng chat.

## 6. Module Premium (App: `home`)

Cung cấp các tính năng trả phí và quản lý quyền lợi của người dùng Premium.

### 6.1. Chức năng
- **Trang thông tin Premium:** Giới thiệu các lợi ích của việc nâng cấp tài khoản.
- **Nâng cấp tài khoản:** Quy trình để người dùng nâng cấp tài khoản của mình lên Premium (có thể tích hợp cổng thanh toán).
- **Xử lý thanh toán:** Giao diện xử lý và xác nhận sau khi thanh toán thành công.
- **Giới hạn truy cập:** Các tính năng đặc biệt sẽ được giới hạn chỉ dành cho người dùng Premium.