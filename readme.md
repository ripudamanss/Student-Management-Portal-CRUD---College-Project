# 🎓 Student Management System

A web-based Student Management System built using **Flask, SQLite, HTML, CSS, and Bootstrap**.  
This system allows admins to manage student records and announcements, while students can securely access their own dashboard.

---

## 🚀 Features

### 👨‍💼 Admin / Faculty
- Add, edit, and delete student records
- Upload student images
- Mark students as favorites ⭐
- Search students with live suggestions
- Export data (CSV & PDF)
- Generate QR codes for student profiles
- Create and manage announcements 📢

### 🎓 Student
- Secure login using username & password
- View personal profile
- Access announcements
- Clean dashboard UI

### 🔐 Authentication & Security
- Role-based login (Admin / Faculty / Student)
- Session management
- Auto logout after inactivity ⏳
- Idle detection + countdown timer

---

## 🛠️ Technologies Used

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** HTML, CSS, Bootstrap
- **Libraries:**
  - ReportLab (PDF export)
  - qrcode (QR generation)

---

## 📊 System Modules

- Login System
- Dashboard (Admin & Student)
- Student Management (CRUD)
- Announcement System
- Search & Filter
- Export (CSV/PDF)
- Session Timeout System

---

## 🖥️ Screenshots

> Screenshot Not Added , It will Be added Later

- Login Page  
- Admin Dashboard  
- Student Dashboard  

---

## ⚙️ Installation

```bash
# Clone repo
git clone https://githubcomripudamanssStudent-Management-Portal-CRUD----College-Project.git

# Go into folder
cd project

# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py