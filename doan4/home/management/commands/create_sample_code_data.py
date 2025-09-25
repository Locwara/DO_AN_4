from django.core.management.base import BaseCommand
from django.utils.text import slugify
from home.models import (
    CodeLanguage, CodeCourse, CodeLesson, University, User
)
import json

class Command(BaseCommand):
    help = 'Create sample data for Code with AI feature'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample coding data...')
        
        # Create code languages
        languages_data = [
            {
                'name': 'python',
                'display_name': 'Python 3.9',
                'version': '3.9',
                'file_extension': '.py',
                'syntax_highlight': 'python',
                'docker_image': 'python:3.9-slim'
            },
            {
                'name': 'javascript',
                'display_name': 'JavaScript ES6',
                'version': 'ES6',
                'file_extension': '.js',
                'syntax_highlight': 'javascript',
                'docker_image': 'node:16-slim'
            },
            {
                'name': 'java',
                'display_name': 'Java 11',
                'version': '11',
                'file_extension': '.java',
                'syntax_highlight': 'java',
                'docker_image': 'openjdk:11-slim'
            }
        ]
        
        for lang_data in languages_data:
            language, created = CodeLanguage.objects.get_or_create(
                name=lang_data['name'],
                defaults=lang_data
            )
            if created:
                self.stdout.write(f'Created language: {language.display_name}')
        
        # Get or create university
        university = University.objects.first()
        if not university:
            university = University.objects.create(
                name='Tech University',
                short_name='TU',
                is_active=True
            )
        
        # Get or create admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                is_staff=True,
                is_superuser=True
            )
        
        # Create Python course
        python_lang = CodeLanguage.objects.get(name='python')
        python_course, created = CodeCourse.objects.get_or_create(
            slug='python-fundamentals',
            defaults={
                'title': 'Python Fundamentals',
                'description': 'Learn Python programming from basics to advanced concepts. Perfect for beginners who want to start their coding journey.',
                'language': python_lang,
                'difficulty': 'beginner',
                'estimated_hours': 20,
                'created_by': admin_user,
                'university': university,
                'status': 'published',
                'is_free': True,
                'is_featured': True
            }
        )
        
        if created:
            self.stdout.write(f'Created course: {python_course.title}')
            
            # Create lessons for Python course
            lessons_data = [
                {
                    'title': 'Hello World',
                    'slug': 'hello-world',
                    'description': 'Your first Python program',
                    'lesson_type': 'coding',
                    'problem_statement': '''Viết chương trình Python đầu tiên của bạn!

Hãy tạo một chương trình in ra màn hình dòng chữ "Hello, World!".

Đây là bài tập truyền thống để bắt đầu học lập trình.''',
                    'starter_code': '# Viết code Python của bạn ở đây\n# In ra "Hello, World!"\n',
                    'solution_code': 'print("Hello, World!")',
                    'test_cases': [
                        {
                            'input': '',
                            'expected_output': 'Hello, World!'
                        }
                    ],
                    'order_index': 1,
                    'points_reward': 10
                },
                {
                    'title': 'Variables and Input',
                    'slug': 'variables-and-input',
                    'description': 'Learn about variables and user input',
                    'lesson_type': 'coding',
                    'problem_statement': '''Học cách sử dụng biến và nhập dữ liệu từ người dùng.

Viết chương trình:
1. Hỏi tên người dùng
2. In ra lời chào cá nhân hóa

Ví dụ:
Input: "Alice"
Output: "Hello, Alice!"''',
                    'starter_code': '# Nhập tên từ người dùng\nname = input()\n\n# In lời chào\n# Viết code của bạn ở đây\n',
                    'solution_code': 'name = input()\nprint(f"Hello, {name}!")',
                    'test_cases': [
                        {
                            'input': 'Alice',
                            'expected_output': 'Hello, Alice!'
                        },
                        {
                            'input': 'Bob',
                            'expected_output': 'Hello, Bob!'
                        }
                    ],
                    'order_index': 2,
                    'points_reward': 15
                },
                {
                    'title': 'Simple Calculator',
                    'slug': 'simple-calculator',
                    'description': 'Create a basic calculator',
                    'lesson_type': 'coding',
                    'problem_statement': '''Tạo máy tính đơn giản.

Nhập 2 số và tính tổng của chúng.

Input: 2 dòng, mỗi dòng 1 số nguyên
Output: Tổng của 2 số''',
                    'starter_code': '# Nhập 2 số từ người dùng\na = int(input())\nb = int(input())\n\n# Tính và in tổng\n# Viết code của bạn ở đây\n',
                    'solution_code': 'a = int(input())\nb = int(input())\nresult = a + b\nprint(result)',
                    'test_cases': [
                        {
                            'input': '5\n3',
                            'expected_output': '8'
                        },
                        {
                            'input': '10\n-2',
                            'expected_output': '8'
                        },
                        {
                            'input': '0\n0',
                            'expected_output': '0'
                        }
                    ],
                    'order_index': 3,
                    'points_reward': 20
                }
            ]
            
            for lesson_data in lessons_data:
                lesson = CodeLesson.objects.create(
                    course=python_course,
                    **lesson_data,
                    is_published=True
                )
                self.stdout.write(f'Created lesson: {lesson.title}')
        
        # Create JavaScript course
        js_lang = CodeLanguage.objects.get(name='javascript')
        js_course, created = CodeCourse.objects.get_or_create(
            slug='javascript-basics',
            defaults={
                'title': 'JavaScript Basics',
                'description': 'Master JavaScript fundamentals for web development. Learn variables, functions, and DOM manipulation.',
                'language': js_lang,
                'difficulty': 'beginner',
                'estimated_hours': 15,
                'created_by': admin_user,
                'university': university,
                'status': 'published',
                'is_free': True
            }
        )
        
        if created:
            self.stdout.write(f'Created course: {js_course.title}')
            
            # Create lessons for JavaScript course
            js_lessons = [
                {
                    'title': 'Console Output',
                    'slug': 'console-output',
                    'description': 'Learn console.log and basic output',
                    'lesson_type': 'coding',
                    'problem_statement': '''Học cách in ra console trong JavaScript.

Sử dụng console.log() để in "Hello, JavaScript!"''',
                    'starter_code': '// Viết JavaScript code ở đây\n// Sử dụng console.log()\n',
                    'solution_code': 'console.log("Hello, JavaScript!");',
                    'test_cases': [
                        {
                            'input': '',
                            'expected_output': 'Hello, JavaScript!'
                        }
                    ],
                    'order_index': 1,
                    'points_reward': 10
                }
            ]
            
            for lesson_data in js_lessons:
                lesson = CodeLesson.objects.create(
                    course=js_course,
                    **lesson_data,
                    is_published=True
                )
                self.stdout.write(f'Created lesson: {lesson.title}')
        
        self.stdout.write(self.style.SUCCESS('Sample coding data created successfully!'))
