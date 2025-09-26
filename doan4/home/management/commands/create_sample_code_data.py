from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from home.models import (
    CodeLanguage, CodeCourse, CodeLesson, CodeCourseTag,
    User, University
)
import json

class Command(BaseCommand):
    help = 'Create sample coding courses and lessons'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample coding courses and lessons...')
        
        # Create/get admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.username}')
        
        # Create/get university
        university, created = University.objects.get_or_create(
            name='Đại học Công nghệ Thông tin',
            defaults={
                'short_name': 'UIT',
                'address': 'TP.HCM, Việt Nam',
                'website': 'https://uit.edu.vn'
            }
        )
        
        # Create programming languages
        languages_data = [
            {'name': 'python', 'display_name': 'Python 3.9', 'file_extension': '.py', 'syntax_highlight': 'python'},
            {'name': 'javascript', 'display_name': 'JavaScript ES6', 'file_extension': '.js', 'syntax_highlight': 'javascript'},
            {'name': 'java', 'display_name': 'Java 11', 'file_extension': '.java', 'syntax_highlight': 'java'},
            {'name': 'cpp', 'display_name': 'C++ 17', 'file_extension': '.cpp', 'syntax_highlight': 'cpp'},
            {'name': 'csharp', 'display_name': 'C# 9.0', 'file_extension': '.cs', 'syntax_highlight': 'csharp'},
        ]
        
        languages = {}
        for lang_data in languages_data:
            lang, created = CodeLanguage.objects.get_or_create(
                name=lang_data['name'],
                defaults=lang_data
            )
            languages[lang_data['name']] = lang
            if created:
                self.stdout.write(f'Created language: {lang.display_name}')
        
        # Create course tags
        tags_data = [
            {'name': 'Beginner', 'color': '#10B981'},
            {'name': 'Web Development', 'color': '#3B82F6'}, 
            {'name': 'Data Structures', 'color': '#F59E0B'},
            {'name': 'Algorithms', 'color': '#EF4444'},
            {'name': 'OOP', 'color': '#8B5CF6'},
            {'name': 'Game Development', 'color': '#EC4899'},
        ]
        
        tags = {}
        for tag_data in tags_data:
            tag, created = CodeCourseTag.objects.get_or_create(
                name=tag_data['name'],
                defaults=tag_data
            )
            tags[tag_data['name']] = tag
        
        # Create 5 sample courses
        courses_data = [
            {
                'title': 'Python cho Người Mới Bắt Đầu',
                'description': 'Khóa học Python từ cơ bản đến nâng cao, bao gồm cú pháp, cấu trúc dữ liệu, và lập trình hướng đối tượng.',
                'language': 'python',
                'difficulty': 'beginner',
                'estimated_hours': 40,
                'tags': ['Beginner'],
                'lessons': [
                    {
                        'title': 'Hello World và Biến',
                        'description': 'Học cách in ra màn hình và làm việc với biến',
                        'lesson_type': 'coding',
                        'theory_content': '<h3>Chào mừng đến với Python!</h3><p>Python là ngôn ngữ lập trình đơn giản và mạnh mẽ.</p>',
                        'problem_statement': 'Viết chương trình in ra "Hello, World!" và tạo biến để lưu tên của bạn.',
                        'starter_code': '# Viết code của bạn ở đây\nprint("Hello, World!")\n\n# Tạo biến name và in ra\nname = ""\nprint(f"Xin chào, {name}!")',
                        'solution_code': 'print("Hello, World!")\n\nname = "Python"\nprint(f"Xin chào, {name}!")',
                        'test_cases': [
                            {'input': '', 'expected_output': 'Hello, World!\nXin chào, Python!'},
                        ],
                        'hints': [
                            {'title': 'Gợi ý 1', 'content': 'Sử dụng hàm print() để in ra màn hình'},
                            {'title': 'Gợi ý 2', 'content': 'Gán giá trị cho biến name bằng dấu ='}
                        ]
                    },
                    {
                        'title': 'Vòng lặp For',
                        'description': 'Học cách sử dụng vòng lặp for',
                        'lesson_type': 'coding',
                        'problem_statement': 'Viết chương trình in ra các số từ 1 đến 10.',
                        'starter_code': '# Sử dụng vòng lặp for để in số từ 1 đến 10\nfor i in range(?, ?):\n    print(?)',
                        'solution_code': 'for i in range(1, 11):\n    print(i)',
                        'test_cases': [
                            {'input': '', 'expected_output': '1\n2\n3\n4\n5\n6\n7\n8\n9\n10'},
                        ]
                    }
                ]
            },
            {
                'title': 'JavaScript Cơ Bản',
                'description': 'Học JavaScript từ đầu: biến, hàm, DOM và các khái niệm cơ bản của web development.',
                'language': 'javascript',
                'difficulty': 'beginner',
                'estimated_hours': 35,
                'tags': ['Beginner', 'Web Development'],
                'lessons': [
                    {
                        'title': 'Biến và Kiểu Dữ Liệu',
                        'description': 'Học về var, let, const và các kiểu dữ liệu',
                        'lesson_type': 'coding',
                        'problem_statement': 'Tạo các biến với kiểu dữ liệu khác nhau và in ra.',
                        'starter_code': '// Tạo biến số\nlet number = 42;\n\n// Tạo biến chuỗi\nlet text = "Hello";\n\n// Tạo biến boolean\nlet isTrue = true;\n\nconsole.log(number);\nconsole.log(text);\nconsole.log(isTrue);',
                        'solution_code': 'let number = 42;\nlet text = "Hello";\nlet isTrue = true;\n\nconsole.log(number);\nconsole.log(text);\nconsole.log(isTrue);',
                        'test_cases': [
                            {'input': '', 'expected_output': '42\nHello\ntrue'},
                        ]
                    },
                    {
                        'title': 'Hàm JavaScript',
                        'description': 'Học cách tạo và sử dụng hàm',
                        'lesson_type': 'coding',
                        'problem_statement': 'Tạo hàm tính tổng hai số.',
                        'starter_code': 'function sum(a, b) {\n    // Viết code ở đây\n}\n\nconsole.log(sum(5, 3));',
                        'solution_code': 'function sum(a, b) {\n    return a + b;\n}\n\nconsole.log(sum(5, 3));',
                        'test_cases': [
                            {'input': '', 'expected_output': '8'},
                        ]
                    }
                ]
            },
            {
                'title': 'Cấu Trúc Dữ Liệu với C++',
                'description': 'Khóa học về cấu trúc dữ liệu cơ bản: mảng, danh sách liên kết, stack, queue.',
                'language': 'cpp',
                'difficulty': 'intermediate',
                'estimated_hours': 50,
                'tags': ['Data Structures', 'Algorithms'],
                'lessons': [
                    {
                        'title': 'Mảng và Vector',
                        'description': 'Học cách sử dụng mảng và vector trong C++',
                        'lesson_type': 'coding',
                        'problem_statement': 'Tạo vector số nguyên và in ra tất cả phần tử.',
                        'starter_code': '#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n    vector<int> numbers = {1, 2, 3, 4, 5};\n    \n    // In ra tất cả phần tử\n    for(int i = 0; i < numbers.size(); i++) {\n        cout << numbers[i] << " ";\n    }\n    \n    return 0;\n}',
                        'solution_code': '#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n    vector<int> numbers = {1, 2, 3, 4, 5};\n    \n    for(int i = 0; i < numbers.size(); i++) {\n        cout << numbers[i] << " ";\n    }\n    \n    return 0;\n}',
                        'test_cases': [
                            {'input': '', 'expected_output': '1 2 3 4 5 '},
                        ]
                    }
                ]
            },
            {
                'title': 'Lập Trình Hướng Đối Tượng với Java',
                'description': 'Học các khái niệm OOP: class, object, inheritance, polymorphism trong Java.',
                'language': 'java',
                'difficulty': 'intermediate',
                'estimated_hours': 45,
                'tags': ['OOP'],
                'lessons': [
                    {
                        'title': 'Class và Object',
                        'description': 'Tạo class đầu tiên trong Java',
                        'lesson_type': 'coding',
                        'problem_statement': 'Tạo class Student với thuộc tính name và method introduce().',
                        'starter_code': 'public class Student {\n    String name;\n    \n    public Student(String name) {\n        this.name = name;\n    }\n    \n    public void introduce() {\n        System.out.println("Hello, I am " + name);\n    }\n    \n    public static void main(String[] args) {\n        Student student = new Student("John");\n        student.introduce();\n    }\n}',
                        'solution_code': 'public class Student {\n    String name;\n    \n    public Student(String name) {\n        this.name = name;\n    }\n    \n    public void introduce() {\n        System.out.println("Hello, I am " + name);\n    }\n    \n    public static void main(String[] args) {\n        Student student = new Student("John");\n        student.introduce();\n    }\n}',
                        'test_cases': [
                            {'input': '', 'expected_output': 'Hello, I am John'},
                        ]
                    }
                ]
            },
            {
                'title': 'Game Development với C#',
                'description': 'Khóa học phát triển game cơ bản với C# và Unity engine.',
                'language': 'csharp',
                'difficulty': 'advanced',
                'estimated_hours': 60,
                'tags': ['Game Development'],
                'lessons': [
                    {
                        'title': 'Player Controller',
                        'description': 'Tạo script điều khiển nhân vật',
                        'lesson_type': 'coding',
                        'problem_statement': 'Tạo class Player với method Move().',
                        'starter_code': 'using System;\n\npublic class Player {\n    public string name;\n    public int health;\n    \n    public Player(string playerName) {\n        name = playerName;\n        health = 100;\n    }\n    \n    public void Move(string direction) {\n        Console.WriteLine($"{name} moves {direction}");\n    }\n}\n\nclass Program {\n    static void Main() {\n        Player player = new Player("Hero");\n        player.Move("forward");\n    }\n}',
                        'solution_code': 'using System;\n\npublic class Player {\n    public string name;\n    public int health;\n    \n    public Player(string playerName) {\n        name = playerName;\n        health = 100;\n    }\n    \n    public void Move(string direction) {\n        Console.WriteLine($"{name} moves {direction}");\n    }\n}\n\nclass Program {\n    static void Main() {\n        Player player = new Player("Hero");\n        player.Move("forward");\n    }\n}',
                        'test_cases': [
                            {'input': '', 'expected_output': 'Hero moves forward'},
                        ]
                    }
                ]
            }
        ]
        
        # Create courses and lessons
        for course_data in courses_data:
            # Create course
            course, created = CodeCourse.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    'slug': slugify(course_data['title']),
                    'description': course_data['description'],
                    'language': languages[course_data['language']],
                    'difficulty': course_data['difficulty'],
                    'estimated_hours': course_data['estimated_hours'],
                    'created_by': admin_user,
                    'university': university,
                    'status': 'published',
                    'published_at': timezone.now(),
                    'is_free': True
                }
            )
            
            if created:
                # Add tags
                for tag_name in course_data['tags']:
                    if tag_name in tags:
                        course.tags.add(tags[tag_name])
                
                self.stdout.write(f'Created course: {course.title}')
                
                # Create lessons
                for i, lesson_data in enumerate(course_data['lessons']):
                    lesson, lesson_created = CodeLesson.objects.get_or_create(
                        course=course,
                        title=lesson_data['title'],
                        defaults={
                            'slug': slugify(lesson_data['title']),
                            'description': lesson_data.get('description', ''),
                            'lesson_type': lesson_data['lesson_type'],
                            'theory_content': lesson_data.get('theory_content', ''),
                            'problem_statement': lesson_data.get('problem_statement', ''),
                            'starter_code': lesson_data.get('starter_code', ''),
                            'solution_code': lesson_data.get('solution_code', ''),
                            'test_cases': lesson_data.get('test_cases', []),
                            'hints': lesson_data.get('hints', []),
                            'order_index': i + 1,
                            'is_published': True,
                            'estimated_time': 30,
                            'points_reward': 10
                        }
                    )
                    
                    if lesson_created:
                        self.stdout.write(f'  Created lesson: {lesson.title}')
        
        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!'))
        self.stdout.write('\nCourses created:')
        for course in CodeCourse.objects.all():
            lesson_count = course.lessons.count()
            self.stdout.write(f'  • {course.title} ({lesson_count} lessons)')
