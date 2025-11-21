from django import forms
from home.models import Document, University, Course

class DocumentForm(forms.ModelForm):
    university = forms.ModelChoiceField(
        queryset=University.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),  # Initially empty
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    academic_year = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    semester = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    class Meta:
        model = Document
        fields = ['title', 'description', 'university', 'course', 'document_type', 'academic_year', 'semester']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VD: Đề thi cuối kỳ Giải tích 1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mô tả ngắn về tài liệu...'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'Tiêu đề tài liệu',
            'description': 'Mô tả',
            'university': 'Trường Đại học',
            'course': 'Môn học',
            'document_type': 'Loại tài liệu',
            'academic_year': 'Năm học',
            'semester': 'Học kỳ',
        }

    def __init__(self, *args, **kwargs):
        # Pop custom kwargs before calling super
        academic_years_choices = kwargs.pop('academic_years', [])
        semesters_choices = kwargs.pop('semesters', [])
        
        super().__init__(*args, **kwargs)

        # Set choices for dynamic fields
        self.fields['academic_year'].choices = [('', '---------')] + academic_years_choices
        self.fields['semester'].choices = [('', '---------')] + semesters_choices
        
        # Dynamic queryset for courses based on university, handling formset prefixes
        # self.prefix will be 'form-0', 'form-1', etc. when used in a formset
        university_key = f'{self.prefix}-university' if self.prefix else 'university'

        if self.data and university_key in self.data:
            try:
                university_id = int(self.data.get(university_key))
                self.fields['course'].queryset = Course.objects.filter(university_id=university_id, is_active=True).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from a malicious user
        elif self.instance.pk and self.instance.university:
            self.fields['course'].queryset = self.instance.university.course_set.filter(is_active=True).order_by('name')
