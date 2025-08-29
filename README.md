# HealthFlow AI: Agentic Doctor Appointment Assistant  

**HealthFlow AI** is a smart, full-stack web application that leverages a large language model (LLM) to act as an intelligent agent for managing medical appointments.  

The application provides a **conversational interface** for both patients and doctors, enabling them to handle scheduling and reporting tasks using natural language.  

This project demonstrates an implementation of an **agentic AI system**, where the LLM dynamically chooses and uses backend tools to:  
- Interact with a database  
- Connect with external APIs (Google Calendar, Mailgun)  
- Manage secure communications (email confirmations, notifications)




<img width="466" height="608" alt="image" src="https://github.com/user-attachments/assets/b58fd6d7-6285-40cf-b33e-76f8ffb3a205" />


---

## 🚀 Core Features  

### 👩‍⚕️ For Patients  
- **Conversational Appointment Booking**: Book appointments using natural prompts like:  
  > “I need to see Dr. Smith tomorrow at 2 pm for a check-up.”  
- **Intelligent Scheduling**: AI checks both patient and doctor availability. Suggests closest available slots if conflicts exist.  
- **Contextual Memory**: Supports natural follow-ups, e.g. *“Okay, book the 9 am slot then.”*  
- **Automated Confirmations**: Creates Google Calendar events and sends confirmation emails.  
- **Prompt History**: Patients can review their past conversations.
- <img width="1440" height="537" alt="image" src="https://github.com/user-attachments/assets/a60ca000-2963-461a-8bb1-c9af6d1b2311" />


### 🩺 For Doctors  
- **Role-Based Dashboard**: A dedicated interface for managing practice.  
- **AI-Powered Reporting**: Ask natural queries such as:  
  - “How many appointments do I have today?”  
  - “Who are my patients for this week?”  
  - “How many patients did I see last week with a fever?”  
- **In-App Notifications**: Reports are stored in the doctor’s dashboard.  
- **Real-Time Schedule View**: See up-to-date appointment schedules.
- <img width="1438" height="708" alt="image" src="https://github.com/user-attachments/assets/6c4fdec0-2b92-4014-ab26-9dfc57532199" />


---

## 🛠️ Tech Stack  

| Category       | Technology |
|----------------|------------|
| **Backend**    | FastAPI (Python), PostgreSQL, SQLAlchemy, Alembic |
| **Frontend**   | React, TypeScript, Vite, Tailwind CSS, Shadcn/UI |
| **AI Agent**   | Groq API (LLaMA 3) |
| **External APIs** | Google Calendar API, Mailgun API |

---

## ⚙️ Setup and Installation  

You’ll need **two terminal windows**: one for the backend and one for the frontend.  

### 1️⃣ Backend Setup  

**Prerequisites:**  
- Python 3.9+  
- PostgreSQL (running locally)  

**Steps:**  
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Configure Environment Variables:**  
Create a `.env` file in the `backend` directory:  
```env
DATABASE_URL="postgresql://your_db_user:your_db_password@localhost/doc_demo_db"
SECRET_KEY="a_very_long_and_secret_random_string_for_jwt"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

GROQ_API_KEY="your_groq_api_key"

MAILGUN_API_KEY="your_mailgun_private_api_key"
MAILGUN_DOMAIN="your_mailgun_sandbox_domain"
FROM_EMAIL="test@your_mailgun_sandbox_domain"
```

**Set up Database:**  
1. Ensure PostgreSQL is running.  
2. Create database:  
   ```sql
   CREATE DATABASE doc_demo_db;
   ```  
3. The app auto-creates required tables on startup.  

**Run Backend:**  
```bash
uvicorn app.main:app --reload
```
Backend runs at: [http://127.0.0.1:8000](http://127.0.0.1:8000)  

---

### 2️⃣ Frontend Setup  

**Prerequisites:**  
- Node.js v18+  
- npm  

**Steps:**  
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

**Configure Environment Variables:**  
Create a `.env` file in the `frontend` directory:  
```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

**Run Frontend:**  
```bash
npm run dev
```
Frontend runs at: [http://localhost:5173](http://localhost:5173) (or next available port).  

---

## 🎯 Usage  

1. Start both backend & frontend servers.  
2. Open frontend in your browser.  
3. Register as **patient** or **doctor** to access respective dashboards.
4. <img width="1114" height="708" alt="image" src="https://github.com/user-attachments/assets/c27004df-2604-4dfa-93ac-e78e679dc779" />


### 🔹 Example Patient Prompts  
- “Which doctors are available tomorrow?”  
- “Is Dr. Smith free next Tuesday at 3 pm?”  
- “Book an appointment with Dr. Smith for tomorrow at 10 am for a headache.”  
- *(After availability check)* “Okay, book it.”  

### 🔹 Example Doctor Prompts  
- “How many appointments do I have today?”  
- “Who are my patients for this week?”  
- “Show me details for my appointments tomorrow.”  

---
