from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import (
    User, University, CodeCourse, CodeLesson, 
    CodeLanguage, CodeCourseTag
)
import json

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email của bạn',
            'id': 'email'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Họ',
            'id': 'first_name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên',
            'id': 'last_name'
        })
    )
    
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Số điện thoại (không bắt buộc)',
            'id': 'phone'
        })
    )
    
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Giới thiệu về bản thân (không bắt buộc)',
            'rows': 3,
            'id': 'bio'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'bio', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tùy chỉnh widget cho các field mặc định
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Tên đăng nhập',
            'id': 'username'
        })
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mật khẩu',
            'id': 'password1'
        })
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Xác nhận mật khẩu',
            'id': 'password2'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Tên đăng nhập này đã tồn tại.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.bio = self.cleaned_data.get('bio', '')
        
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tên đăng nhập hoặc Email',
            'id': 'login_username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu',
            'id': 'login_password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'remember_me'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Cho phép đăng nhập bằng email hoặc username
            user = None
            if '@' in username:
                try:
                    user_obj = User.objects.get(email=username)
                    username = user_obj.username
                except User.DoesNotExist:
                    pass

            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Tên đăng nhập/Email hoặc mật khẩu không đúng.")
            if not user.is_active:
                raise forms.ValidationError("Tài khoản đã bị vô hiệu hóa.")

        return self.cleaned_data
    
# forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.contrib.auth.forms import SetPasswordForm as BaseSetPasswordForm
from django.contrib.auth import authenticate
from .models import User


class ProfileUpdateForm(forms.ModelForm):
    """Form cập nhật thông tin profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Họ của bạn'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên của bạn'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0123456789'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Viết vài dòng về bản thân...'
            }),
        }
        labels = {
            'first_name': 'Họ',
            'last_name': 'Tên',
            'email': 'Email',
            'phone': 'Số điện thoại',
            'bio': 'Giới thiệu bản thân',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email này đã được sử dụng bởi tài khoản khác.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError('Số điện thoại chỉ được chứa số.')
        if phone and len(phone) not in [10, 11]:
            raise forms.ValidationError('Số điện thoại phải có 10-11 chữ số.')
        return phone


class PasswordChangeForm(BasePasswordChangeForm):
    """Form đổi mật khẩu với custom styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mật khẩu hiện tại'
        })
        self.fields['old_password'].label = 'Mật khẩu hiện tại'
        
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mật khẩu mới (ít nhất 8 ký tự)'
        })
        self.fields['new_password1'].label = 'Mật khẩu mới'
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nhập lại mật khẩu mới'
        })
        self.fields['new_password2'].label = 'Xác nhận mật khẩu mới'

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Mật khẩu hiện tại không đúng.')
        return old_password


class PasswordResetForm(forms.Form):
    """Form yêu cầu reset mật khẩu"""
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập email của bạn',
            'autocomplete': 'email'
        }),
        label='Email'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email này không tồn tại trong hệ thống.')
        return email


class SetPasswordForm(BaseSetPasswordForm):
    """Form đặt mật khẩu mới từ reset link"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mật khẩu mới (ít nhất 8 ký tự)'
        })
        self.fields['new_password1'].label = 'Mật khẩu mới'
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nhập lại mật khẩu mới'
        })
        self.fields['new_password2'].label = 'Xác nhận mật khẩu mới'


# Course Management Forms
class CodeCourseForm(forms.ModelForm):
    """Form tạo/chỉnh sửa khóa học"""
    class Meta:
        model = CodeCourse
        fields = [
            'title', 'description', 'thumbnail', 'language', 
            'difficulty', 'estimated_hours', 'university',
            'is_free', 'requires_premium', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'VD: Python cơ bản cho người mới bắt đầu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Mô tả khóa học: mục tiêu, nội dung chính, đối tượng học...'
            }),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1000,
                'placeholder': 'VD: 20'
            }),
            'university': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_premium': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['language'].queryset = CodeLanguage.objects.filter(is_active=True)
        self.fields['university'].queryset = University.objects.filter(is_active=True)
        self.fields['tags'].queryset = CodeCourseTag.objects.all()
        
        # Make some fields optional
        self.fields['university'].required = False
        self.fields['estimated_hours'].required = False
        self.fields['thumbnail'].required = False

class CodeLessonForm(forms.ModelForm):
    """Form tạo/chỉnh sửa bài học - IMPROVED VERSION"""
    
    # Thêm dynamic test case fields
    test_case_count = forms.IntegerField(
        initial=2,
        min_value=1,
        max_value=10,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'test_case_count'
        })
    )
    
    # Thêm dynamic hint fields
    hint_count = forms.IntegerField(
        initial=2,
        min_value=0,
        max_value=5,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'hint_count'
        })
    )
    
    class Meta:
        model = CodeLesson
        fields = [
            'title', 'description', 'theory_content',
            'problem_statement', 'starter_code', 'solution_code',
            'hints', 'test_cases', 'estimated_time', 'points_reward'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'VD: Vòng lặp For trong Python'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mô tả ngắn về nội dung bài học...'
            }),
            'theory_content': forms.Textarea(attrs={
                'class': 'form-control rich-editor',
                'rows': 10,
                'placeholder': 'Viết nội dung lý thuyết ở đây. Bạn có thể sử dụng định dạng văn bản đơn giản.'
            }),
            'problem_statement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Mô tả đề bài: Hãy viết chương trình... Input: ... Output: ...'
            }),
            'starter_code': forms.Textarea(attrs={
                'class': 'form-control code-editor',
                'rows': 10,
                'placeholder': '# Code mẫu ban đầu\ndef solve():\n    pass'
            }),
            'solution_code': forms.Textarea(attrs={
                'class': 'form-control code-editor',
                'rows': 10,
                'placeholder': '# Lời giải mẫu (chỉ giáo viên thấy)'
            }),
            'hints': forms.HiddenInput(),  # Ẩn field JSON gốc
            'test_cases': forms.HiddenInput(),  # Ẩn field JSON gốc
            'estimated_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 300,
                'placeholder': '30'
            }),
            'points_reward': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 100,
                'value': 10
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make most fields optional
        self.fields['description'].required = False
        self.fields['theory_content'].required = False
        self.fields['starter_code'].required = False
        self.fields['solution_code'].required = False
        self.fields['hints'].required = False
        self.fields['test_cases'].required = False
        self.fields['estimated_time'].required = False
        
        # Pre-populate test case count and hint count if editing
        if self.instance.pk:
            try:
                if self.instance.test_cases:
                    if isinstance(self.instance.test_cases, str):
                        test_cases = json.loads(self.instance.test_cases)
                    else:
                        test_cases = self.instance.test_cases
                    self.fields['test_case_count'].initial = len(test_cases) if isinstance(test_cases, list) else 2
            except:
                pass
            
            try:
                if self.instance.hints:
                    if isinstance(self.instance.hints, str):
                        hints = json.loads(self.instance.hints)
                    else:
                        hints = self.instance.hints
                    self.fields['hint_count'].initial = len(hints) if isinstance(hints, list) else 2
            except:
                pass
    
    def save(self, commit=True):
        """Override save to set default lesson_type"""
        lesson = super().save(commit=False)
        if not lesson.pk:  # New lesson
            lesson.lesson_type = 'coding'  # Default to coding
        if commit:
            lesson.save()
        return lesson
    
    def clean_hints(self):
        """Validate hints - accept both JSON string and Python objects"""
        hints = self.cleaned_data.get('hints')
        if not hints:
            return None
            
        try:
            if isinstance(hints, str):
                parsed_hints = json.loads(hints)
            elif isinstance(hints, (list, dict)):
                parsed_hints = hints
            else:
                return None
            
            # Validate structure
            if parsed_hints and isinstance(parsed_hints, list):
                for hint in parsed_hints:
                    if not isinstance(hint, dict) or 'title' not in hint or 'content' not in hint:
                        raise forms.ValidationError('Mỗi gợi ý phải có tiêu đề và nội dung')
            
            # Return as JSON string for storage
            return json.dumps(parsed_hints) if not isinstance(hints, str) else hints
            
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Định dạng gợi ý không hợp lệ: {str(e)}')
        except Exception as e:
            raise forms.ValidationError(f'Lỗi xử lý gợi ý: {str(e)}')
    
    def clean_test_cases(self):
        """Validate test cases - accept both JSON string and Python objects"""
        test_cases = self.cleaned_data.get('test_cases')
        if not test_cases:
            return None
            
        try:
            if isinstance(test_cases, str):
                parsed_cases = json.loads(test_cases)
            elif isinstance(test_cases, (list, dict)):
                parsed_cases = test_cases
            else:
                return None
            
            if not isinstance(parsed_cases, list):
                raise forms.ValidationError('Test cases phải là danh sách')
            
            for case in parsed_cases:
                if not isinstance(case, dict) or 'input' not in case or 'expected_output' not in case:
                    raise forms.ValidationError('Mỗi test case phải có "input" và "expected_output"')
            
            # Return as JSON string for storage
            return json.dumps(parsed_cases) if not isinstance(test_cases, str) else test_cases
            
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'Định dạng test cases không hợp lệ: {str(e)}')
        except Exception as e:
            raise forms.ValidationError(f'Lỗi xử lý test cases: {str(e)}')