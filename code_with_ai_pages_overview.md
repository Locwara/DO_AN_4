# Code with AI - Chi tiết từng trang và chức năng

## 📚 **1. Trang Code Courses List** 
**URL**: `/code/courses/`
**Chức năng**: Danh sách tất cả khóa học lập trình

### Features:
- **Course Cards**: Hiển thị thumbnail, tên khóa học, mô tả, ngôn ngữ, độ khó
- **Filter & Search**: Lọc theo ngôn ngữ (Python, JS, Java), độ khó (Beginner → Expert)
- **Enrollment Status**: Hiển thị "Enrolled" hoặc nút "Enroll" 
- **Stats**: Số học viên, thời gian ước tính, rating
- **Create Course Button**: Cho instructors tạo khóa học mới

### UI Components:
```html
<div class="courses-grid">
  <div class="course-card">
    <img class="course-thumbnail" />
    <div class="difficulty-badge beginner">Beginner</div>
    <h3>Python Fundamentals</h3>
    <p>Learn Python from basics to advanced</p>
    <div class="course-meta">
      <span>🐍 Python</span>
      <span>⏱️ 20h</span> 
      <span>👥 1.2k students</span>
    </div>
    <button class="enroll-btn">Enroll Now</button>
  </div>
</div>
```

---

## 📖 **2. Trang Course Detail**
**URL**: `/code/courses/{slug}/`
**Chức năng**: Chi tiết khóa học với danh sách bài học

### Features:
- **Course Header**: Thông tin đầy đủ, instructor, curriculum overview
- **Lessons List**: Progress bar, unlock status, estimated time
- **Enrollment Management**: Enroll/Continue learning
- **Student Progress**: Completion percentage, points earned
- **Course Discussion**: Comment section cho students

### UI Layout:
```
┌─────────────────┬─────────────────┐
│  Course Info    │   Instructor    │
│  Description    │   Profile       │
│  Prerequisites │   Stats         │
├─────────────────┴─────────────────┤
│           Lessons List            │
│  ✅ Lesson 1: Variables (Done)    │
│  🔒 Lesson 2: Functions (Locked)  │
│  ⏳ Lesson 3: Loops (In Progress) │
└───────────────────────────────────┘
```

---

## 💻 **3. Trang Code Editor/Lesson Detail**
**URL**: `/code/courses/{slug}/lessons/{lesson_slug}/`
**Chức năng**: Trang chính để code - giống VS Code

### Layout (3 panels):

#### **Panel trái - Problem Statement (30%)**
- **Đề bài**: Markdown formatted problem description
- **Input/Output Examples**: Test cases mẫu
- **Hints Section**: Progressive hints (unlock theo attempt)
- **Discussion**: Chat với students khác

#### **Panel giữa - Code Editor (50%)**
- **Monaco Editor**: Syntax highlighting, autocomplete
- **Language Selector**: Python/JS/Java/C++
- **Starter Code**: Code template có sẵn
- **Toolbar**: 
  ```
  [▶️ Run Code] [📤 Submit] [🤖 AI Help] [💡 Hint] [💾 Save]
  ```
- **File Explorer**: Multi-file projects (advanced lessons)

#### **Panel phải - Output & AI (20%)**
- **Console Output**: Kết quả chạy code
- **Test Results**: ✅/❌ từng test case
- **AI Chat Panel**: Real-time chat với AI mentor
- **AI Suggestions**: Code review và improvement tips

### Code Editor Features:
```javascript
// Monaco Editor configuration
monaco.editor.create(container, {
  language: 'python',
  theme: 'vs-dark',
  minimap: { enabled: true },
  fontSize: 14,
  wordWrap: 'on',
  automaticLayout: true
});

// Real-time AI integration
function getAIHelp(code, problem) {
  return fetch('/api/code/ai-help/', {
    method: 'POST',
    body: JSON.stringify({ code, problem })
  });
}
```

---

## 🤖 **4. AI Chat Interface**
**Chức năng**: AI mentor tích hợp trong code editor

### AI Capabilities:
- **Code Review**: Phân tích logic, suggest improvements
- **Debug Help**: Tìm lỗi và giải thích
- **Concept Explanation**: Giải thích concepts khi user hỏi
- **Progressive Hints**: Gợi ý theo level (không spoil solution)
- **Code Optimization**: Suggest better algorithms

### Chat UI:
```html
<div class="ai-chat-panel">
  <div class="chat-messages">
    <div class="message ai-message">
      <div class="avatar">🤖</div>
      <div class="content">
        Code của bạn đúng logic nhưng có thể tối ưu hơn...
      </div>
    </div>
    
    <div class="message user-message">
      <div class="content">Làm sao tối ưu được?</div>
      <div class="avatar">👤</div>
    </div>
  </div>
  
  <div class="chat-input">
    <input placeholder="Hỏi AI mentor..." />
    <button>Send</button>
  </div>
</div>
```

---

## 📊 **5. Trang Code Submission Results**
**URL**: `/code/submissions/{id}/`
**Chức năng**: Chi tiết kết quả sau khi submit code

### Features:
- **Overall Score**: Percentage với visual progress bar
- **Test Cases Results**: Table với từng test case
- **Execution Stats**: Runtime, memory usage
- **AI Detailed Review**: Comprehensive feedback
- **Code Comparison**: Your code vs optimal solution
- **Next Steps**: Suggestions để improve

### Results Layout:
```
┌─────────────────────────────────────┐
│          Score: 85/100 ⭐          │
│    ████████████░░░░ 85%            │
├─────────────────────────────────────┤
│ Test Cases:                         │
│ ✅ Test 1: Basic input (2ms)        │
│ ✅ Test 2: Edge case (5ms)          │
│ ❌ Test 3: Large input (Timeout)    │
├─────────────────────────────────────┤
│ 🤖 AI Feedback:                     │
│ "Your solution works but can be     │
│  optimized using dynamic programming │
│  to handle larger inputs..."        │
└─────────────────────────────────────┘
```

---

## 👨‍🏫 **6. Trang Course Management** (cho Instructors)
**URL**: `/code/courses/manage/`
**Chức năng**: Tạo và quản lý khóa học

### Features:
- **Course Builder**: Drag-drop curriculum builder
- **Lesson Editor**: Rich text editor cho problem statements
- **Test Case Manager**: Add/edit input/output test cases
- **AI Prompt Templates**: Configure AI behavior per lesson
- **Student Analytics**: Progress tracking, common mistakes
- **Auto-grading Setup**: Configure scoring algorithms

### Course Creation Flow:
```
1. Basic Info → 2. Curriculum → 3. Lessons → 4. Test Cases → 5. Publish
```

---

## 📈 **7. Student Progress Dashboard**
**URL**: `/code/dashboard/`
**Chức năng**: Theo dõi tiến độ học tập

### Features:
- **Learning Path**: Visual progress through courses
- **Achievements System**: Badges và milestones
- **Code Statistics**: Lines written, problems solved
- **Skill Radar Chart**: Strengths/weaknesses analysis
- **Leaderboard**: Compete với students khác
- **Recommendation Engine**: AI suggest next courses

### Dashboard Widgets:
```
┌─────────┬─────────┬─────────┐
│ Points  │Problems │ Streak  │
│  2,450  │   127   │  15🔥   │
├─────────┴─────────┴─────────┤
│      Skill Progress         │
│  Python: ████████░░ 80%     │
│  JavaScript: ██████░░░ 60%  │
├─────────────────────────────┤
│     Recent Achievements     │
│  🏆 First 100 Problems      │
│  🔥 7-Day Streak            │
└─────────────────────────────┘
```

---

## 🔧 **8. Admin Panel Extensions**
**URL**: `/admin/code/`
**Chức năng**: Admin quản lý hệ thống

### Features:
- **Language Management**: Add new programming languages
- **Docker Image Configuration**: Setup execution environments
- **AI Model Settings**: Configure Gemini API parameters
- **System Monitoring**: Code execution stats, error rates
- **Content Moderation**: Review reported solutions
- **Performance Analytics**: Response times, success rates

---

## 🚀 **Technical Architecture**

### Frontend Stack:
- **Monaco Editor**: VS Code-like experience
- **WebSocket**: Real-time chat và collaboration
- **Chart.js**: Progress visualizations
- **Bootstrap 5**: Responsive UI framework

### Backend APIs:
```python
# Key API endpoints
POST /api/code/execute/     # Run code with test cases
POST /api/code/submit/      # Submit final solution
POST /api/code/ai-help/     # Get AI assistance
GET  /api/code/hint/        # Get progressive hints
WS   /ws/code-room/{id}/    # Real-time collaboration
```

### AI Integration:
- **Gemini API**: Code review và explanation
- **Custom Prompts**: Per-lesson AI behavior
- **Context Awareness**: AI biết về problem và user progress
- **Multi-language Support**: AI hiểu Python, JS, Java, C++

### Security & Sandboxing:
- **Docker Containers**: Isolated code execution
- **Resource Limits**: CPU/Memory constraints
- **Timeout Protection**: Prevent infinite loops
- **Input Validation**: Sanitize user code

Tất cả trang này sẽ tạo nên một hệ thống học lập trình hoàn chỉnh với AI mentor thông minh! 🎯