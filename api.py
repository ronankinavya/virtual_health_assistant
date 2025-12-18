# api.py
import os
import re
import sqlite3
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# ---------- APP ----------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------- DATABASE ----------
DB_FILE = "health.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            gender TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            relation TEXT
        )
    """)
    conn.commit()
    conn.close()

create_tables()

# ---------- TWILIO ----------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ---------- NLP HELPERS ----------
def normalize_text(t):
    return re.sub(r'[^a-z0-9\s]', ' ', (t or "").lower()).strip()

def tokenize(t):
    return normalize_text(t).split()

# ---------- DISEASES & QUESTIONS ----------
DISEASES = {
    "chest pain": {
        "questions": [
            "How long have you been experiencing this?",
            "Does the pain spread to left arm, jaw, or back?",
            "Are you experiencing sweating, dizziness, or nausea?",
            "Do you have breathing difficulty?"
        ],
        "danger": ["chest pain", "heart attack", "shortness of breath", "fainting"],
        "suggestions": [
            "Seek immediate medical attention if severe or sudden.",
            "Rest and monitor symptoms carefully."
        ]
    },
    "fever": {
        "questions": [
            "What is your current temperature?",
            "Do you have chills or shivering?",
            "Any body aches or fatigue?",
            "Any rashes or cough?"
        ],
        "danger": ["high fever", "persistent fever", "breathing difficulty"],
        "suggestions": [
            "Stay hydrated and monitor temperature.",
            "Consult a doctor if fever persists or is very high."
        ]
    },
    "cold": {
        "questions": [
            "Do you have a runny nose or congestion?",
            "Any sneezing or sore throat?",
            "Are you experiencing fatigue?",
            "Any fever or chills?"
        ],
        "danger": [],
        "suggestions": [
            "Rest, drink warm fluids, and consider OTC remedies.",
            "Consult a doctor if symptoms worsen."
        ]
    },
    "migraine": {
        "questions": [
            "Which side of the head is affected?",
            "Do you experience nausea or vomiting?",
            "Is there sensitivity to light or sound?",
            "How severe is the pain on a scale of 1-10?"
        ],
        "danger": ["sudden severe headache", "vision loss", "fainting"],
        "suggestions": [
            "Rest in a dark, quiet room.",
            "Use prescribed migraine medications."
        ]
    },
    "diabetes symptoms": {
        "questions": [
            "Are you experiencing excessive thirst?",
            "Frequent urination?",
            "Unexplained weight loss?",
            "Fatigue or blurred vision?"
        ],
        "danger": ["extremely high blood sugar", "confusion", "loss of consciousness"],
        "suggestions": [
            "Monitor blood sugar regularly.",
            "Consult a doctor for treatment."
        ]
    },
    "hypertension": {
        "questions": [
            "Do you experience frequent headaches?",
            "Any dizziness or blurred vision?",
            "Any chest pain or shortness of breath?",
            "Do you monitor your blood pressure?"
        ],
        "danger": ["very high blood pressure", "chest pain", "stroke"],
        "suggestions": [
            "Maintain a healthy diet and monitor BP.",
            "Consult a doctor for medications if needed."
        ]
    },
    "asthma": {
        "questions": [
            "Do you experience shortness of breath?",
            "Any wheezing or tightness in chest?",
            "Are symptoms triggered by exercise or allergens?",
            "How severe is your breathing difficulty?"
        ],
        "danger": ["severe asthma attack", "unable to breathe", "cyanosis"],
        "suggestions": [
            "Use your prescribed inhaler.",
            "Seek emergency care if breathing difficulty worsens."
        ]
    },
    "stomach pain": {
        "questions": [
            "Where is the pain located?",
            "Do you have nausea or vomiting?",
            "Any diarrhea or constipation?",
            "Any fever?"
        ],
        "danger": ["severe abdominal pain", "blood in stool", "persistent vomiting"],
        "suggestions": [
            "Rest and monitor symptoms.",
            "Consult a doctor if severe or persistent."
        ]
    },
    "diarrhea": {
        "questions": [
            "How long have you had diarrhea?",
            "Any blood or mucus in stool?",
            "Do you have fever or cramps?",
            "Are you hydrated?"
        ],
        "danger": ["dehydration", "blood in stool", "high fever"],
        "suggestions": [
            "Drink plenty of fluids.",
            "Consult a doctor if severe or persistent."
        ]
    },
    "cough": {
        "questions": [
            "Is it dry or productive?",
            "How long have you been coughing?",
            "Any fever or shortness of breath?",
            "Do you have chest pain?"
        ],
        "danger": ["persistent cough with blood", "breathing difficulty", "high fever"],
        "suggestions": [
            "Stay hydrated and rest.",
            "Consult a doctor if severe."
        ]
    },
    "allergy": {
        "questions": [
            "What are you allergic to?",
            "Do you have skin rashes?",
            "Any difficulty breathing?",
            "Are symptoms seasonal or constant?"
        ],
        "danger": ["anaphylaxis", "swelling of lips or tongue", "breathing difficulty"],
        "suggestions": [
            "Avoid known allergens.",
            "Use prescribed antihistamines."
        ]
    },
    "dehydration": {
        "questions": [
            "Are you feeling very thirsty?",
            "Any dizziness or confusion?",
            "Are you urinating less than usual?",
            "Any dry mouth or lips?"
        ],
        "danger": ["severe dehydration", "confusion", "fainting"],
        "suggestions": [
            "Drink water or oral rehydration solution.",
            "Seek medical help if severe."
        ]
    },
    "anxiety": {
        "questions": [
            "Do you feel nervous or restless?",
            "Any rapid heartbeat?",
            "Difficulty sleeping?",
            "Any panic attacks?"
        ],
        "danger": ["suicidal thoughts", "panic attacks with fainting"],
        "suggestions": [
            "Practice breathing exercises.",
            "Consult a mental health professional."
        ]
    },
    "depression": {
        "questions": [
            "Do you feel sad most of the day?",
            "Loss of interest in activities?",
            "Any changes in sleep or appetite?",
            "Any thoughts of self-harm?"
        ],
        "danger": ["suicidal thoughts", "self-harm"],
        "suggestions": [
            "Reach out to a mental health professional.",
            "Talk to trusted friends or family."
        ]
    },
    "insomnia": {
        "questions": [
            "Do you have trouble falling asleep?",
            "Waking up during night?",
            "Feeling tired during day?",
            "Any use of sleep aids?"
        ],
        "danger": [],
        "suggestions": [
            "Maintain a regular sleep schedule.",
            "Avoid caffeine and screen before sleep."
        ]
    },
    "migraine with aura": {
        "questions": [
            "Do you see flashing lights or zigzag patterns?",
            "Headache on one side?",
            "Nausea or vomiting?",
            "Sensitivity to light or sound?"
        ],
        "danger": ["sudden severe headache", "vision loss", "fainting"],
        "suggestions": [
            "Rest in a quiet dark room.",
            "Consult doctor if severe."
        ]
    },
    "back pain": {
        "questions": [
            "Where is your back pain located?",
            "Is it sharp or dull?",
            "Does it radiate to legs?",
            "Any numbness or weakness?"
        ],
        "danger": ["loss of bladder control", "severe numbness"],
        "suggestions": [
            "Rest and gentle stretches.",
            "Consult doctor if severe."
        ]
    },
    "joint pain": {
        "questions": [
            "Which joints are affected?",
            "Any swelling or redness?",
            "Is pain constant or intermittent?",
            "Any fever?"
        ],
        "danger": ["severe swelling", "high fever"],
        "suggestions": [
            "Rest affected joints.",
            "Consult doctor if severe."
        ]
    }
}

# ---------- EMERGENCY SMS ----------
def get_emergency_contacts(email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    if not user:
        return []
    cur.execute("SELECT name, phone FROM emergency_contacts WHERE user_id=?", (user["id"],))
    contacts = cur.fetchall()
    conn.close()
    return contacts


def send_emergency_sms(email, disease, symptom):
    print("Attempting to send SMS")
    contacts = get_emergency_contacts(email)
    print("To contacts:", contacts)  # show contact numbers
    for c in contacts:
        print("Sending to:", c["phone"])
        twilio_client.messages.create(
            body=f"🚨 EMERGENCY ALERT 🚨\nUser ({email}) reported: {disease}\nSymptom: {symptom}",
            from_=TWILIO_PHONE_NUMBER,
            to=c["phone"]
    )



# ---------- CHAT SESSIONS ----------
sessions = {}

# ---------- GREETINGS ----------
GREETINGS = ["hi","hello","hey","good morning","good evening"]
BYE_WORDS = ["bye","thank you","thanks","see you"]

# ---------- ANALYZE ----------
@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    message = data.get("message", "")
    email = data.get("email", "")
    session_id = data.get("session_id", "")

    text = normalize_text(message)

    # Handle greetings and bye
    if any(g in text for g in GREETINGS):
        return {"reply": "Hello 👋 How can I help you today?", "followup": False}
    if any(b in text for b in BYE_WORDS):
        return {"reply": "You're welcome! Take care 😄", "followup": False}

    # Check if session exists
    if session_id not in sessions:
        # Detect disease keyword
        detected = None
        for disease in DISEASES:
            if disease in text:
                detected = disease
                break
        sessions[session_id] = {
            "disease": detected,
            "answers": [],
            "current_q": 0
        }

    session = sessions[session_id]
    disease = session.get("disease")

    if not disease:
        return {"reply": "Can you describe your main symptom or problem?", "followup": True}

    # ask next question
    questions = DISEASES[disease]["questions"]
    if session["current_q"] < len(questions):
        reply = questions[session["current_q"]]
        session["answers"].append(message)
        session["current_q"] += 1
        return {"reply": reply, "followup": True}

    # final response
    session["answers"].append(message)
    danger_symptoms = DISEASES[disease]["danger"]
    emergency = any(ds in text for ds in danger_symptoms)
    if emergency and email:
        send_emergency_sms(email, disease, text)

    # confidence estimate
    confidence = 85 if emergency else 70

    reply_text = f"The symptoms match with: {disease}. Please consult a doctor.\n\nSuggestions:\n- " + "\n- ".join(DISEASES[disease]["suggestions"])

    sessions.pop(session_id, None)
    return {"reply": reply_text, "confidence": confidence, "emergency": emergency, "followup": False}

# ---------- REGISTER ----------
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    age = data.get("age")
    gender = data.get("gender")
    contacts = data.get("contacts", [])

    if not name or not email or not password:
        raise HTTPException(400, "Missing fields")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name,email,password,age,gender) VALUES (?,?,?,?,?)",
                    (name,email,password,age,gender))
        user_id = cur.lastrowid
        for c in contacts:
            cur.execute("INSERT INTO emergency_contacts (user_id,name,phone,relation) VALUES (?,?,?,?)",
                        (user_id,c.get("name"),c.get("phone"),c.get("relation")))
        conn.commit()
        conn.close()
        return {"status":"ok","message":"User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(400,"Email already exists")

# ---------- LOGIN ----------
@app.post("/login")
async def login(request: Request):
    data = await request.json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                (data["email"], data["password"]))
    user = cur.fetchone()
    conn.close()
    if not user:
        raise HTTPException(401,"Invalid credentials")
    return {"status":"ok","email": data["email"], "name": user["name"]}

# ---------- SET CONTACTS ----------
@app.post("/set_contacts")
async def set_contacts(request: Request):
    data = await request.json()
    email = data.get("email")
    contacts = data.get("contacts", [])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    if not user:
        raise HTTPException(404,"User not found")
    for c in contacts:
        cur.execute("INSERT INTO emergency_contacts (user_id,name,phone,relation) VALUES (?,?,?,?)",
                    (user["id"],c["name"],c["phone"],c["relation"]))
    conn.commit()
    conn.close()
    return {"status":"ok"}

# ---------- RESET PASSWORD ----------
@app.post("/reset_password")
async def reset_password(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password=? WHERE email=?", (password,email))
    conn.commit()
    conn.close()
    return {"status":"ok"}

# ---------- UI ----------
@app.get("/")
def read_index():
    return FileResponse("index.html")

