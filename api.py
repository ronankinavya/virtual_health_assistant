# api.py
import os, json, datetime, hashlib, re
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve sounds
app.mount("/sounds", StaticFiles(directory="sounds"), name="sounds")

# ------------------- Database Connection -------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
        port=int(os.environ.get("DB_PORT", 3306))
    )

# ------------------- Twilio -------------------
twilio_client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
TWILIO_NUMBER = os.environ["TWILIO_PHONE_NUMBER"]

# ------------------- Password hashing -------------------
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Symptom Analysis -------------------
def analyze_symptoms(message):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    words = re.findall(r"\b\w+\b", message.lower())
    symptoms_found = []

    for w in words:
        cur.execute("SELECT * FROM symptoms_data WHERE symptom LIKE %s", (f"%{w}%",))
        rows = cur.fetchall()
        for r in rows:
            symptoms_found.append(r)

    reply = ""
    emergency = False
    if symptoms_found:
        diseases = set(r["disease"] for r in symptoms_found)
        reply = f"I found these possible conditions: {', '.join(diseases)}."
        if any(r["danger_flag"] for r in symptoms_found):
            reply += " ⚠️ Some symptoms may indicate a serious condition. Please contact emergency services."
            emergency = True
    else:
        reply = "I could not find exact matches for your symptoms. Please describe them in more detail."

    cur.close()
    conn.close()
    return reply, emergency

# ------------------- UI -------------------
@app.get("/", response_class=HTMLResponse)
def ui():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>💜 AI Health Assistant</title>
<style>
body {font-family:Poppins,sans-serif;background:#0b0b0b;color:white;text-align:center;margin:0;overflow:hidden;}
h1{margin-top:20px;}
.chat-container{width:90%;max-width:700px;margin:70px auto 10px auto;background:#1c1c1c;border-radius:15px;padding:15px;height:400px;overflow-y:auto;box-shadow:0 0 15px #c77dff;}
.msg{max-width:70%;padding:10px 14px;margin:6px;border-radius:12px;word-wrap:break-word;}
.user{background:#c77dff;margin-left:auto;text-align:right;}
.bot{background:#9d4edd;text-align:left;}
.input-area{display:flex;justify-content:center;align-items:center;gap:8px;margin-top:10px;}
input#userInput{width:50%;height:40px;padding:10px;border-radius:12px;border:none;outline:none;font-size:1rem;}
button{border:none;border-radius:10px;padding:10px 15px;cursor:pointer;background:#c77dff;color:#fff;font-weight:bold;}
.extra-btn-group{display:flex;justify-content:center;gap:8px;margin-top:5px;}
.top-buttons{position:fixed;top:10px;right:15px;display:flex;gap:8px;}
.panel,.popup{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#1c1c1c;padding:20px;border-radius:15px;box-shadow:0 0 10px #c77dff;z-index:10;width:320px;color:#fff;}
.popup .row{margin-bottom:8px;text-align:left;}
.popup input{width:100%;padding:8px;border-radius:8px;border:none;outline:none;}
.forgot-link{color:#fff;cursor:pointer;text-decoration:underline;margin-top:8px;}
#bubbles{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;overflow:hidden;}
.bubble{position:absolute;bottom:0;background:#c77dff;border-radius:50%;opacity:0.4;animation:rise 10s infinite ease-in;}
@keyframes rise{0%{transform:translateY(0);}100%{transform:translateY(-120vh);opacity:0;}}
.robot{position:fixed;left:20px;bottom:30px;width:70px;height:70px;z-index:5;animation:floatBot 3s ease-in-out infinite;}
@keyframes floatBot{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}
.robot-tip{position:fixed;left:100px;bottom:40px;background:#c77dff;border-radius:12px;padding:8px 12px;font-size:0.9rem;animation:floatTip 3s ease-in-out infinite;z-index:5;}
@keyframes floatTip{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}
.time {display:block;font-size:0.75rem;margin-top:6px;opacity:0.85;}
</style>
</head>
<body>
<div id="bubbles"></div>
<h1>💜 AI Health Assistant</h1>
<div class="chat-container" id="chat"></div>
<div class="input-area">
  <input id="userInput" type="text" placeholder="Describe your symptoms...">
  <button onclick="sendMessage()">📨</button>
</div>
<div class="extra-btn-group">
  <button onclick="study()">📚 Study</button>
  <button onclick="search()">🔍 Search</button>
  <button onclick="uploadPhoto()">🖼️ Upload</button>
</div>
<div class="top-buttons">
  <button onclick="openPopup('loginPopup')">Login</button>
  <button onclick="openPopup('signupPopup')">Signup</button>
  <button onclick="togglePanel()">⚙️</button>
</div>
<div class="panel" id="panel">
  <button onclick="toggleDark()">🌙 Dark Mode</button><br><br>
  <button onclick="openPopup('trackerPopup')">📅 Tracker</button><br><br>
  <button onclick="openPopup('dietPopup')">🥗 Diet Tracker</button><br><br>
  <button onclick="openPopup('moodPopup')">😊 Mood Tracker</button><br><br>
  <button onclick="openPopup('menstrualPopup')">💖 Menstrual Cycle</button>
</div>

<!-- LOGIN POPUP -->
<div class="popup" id="loginPopup">
  <h3>Login</h3>
  <div class="row"><input placeholder='Email' id='loginEmail'></div>
  <div class="row"><input type='password' placeholder='Password' id='loginPass'></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;">
    <button onclick="login()">Login</button>
    <button onclick="closePopup('loginPopup')">Close</button>
  </div>
  <div style="margin-top:8px;text-align:left;">
    <span class="forgot-link" onclick="openForgotPopup()">Forgot Password?</span>
  </div>
</div>

<!-- SIGNUP POPUP (collects 2 emergency contacts) -->
<div class="popup" id="signupPopup">
  <h3>Signup</h3>
  <div class="row"><input placeholder='Name' id='signupName'></div>
  <div class="row"><input placeholder='Email' id='signupEmail'></div>
  <div class="row"><input type='password' placeholder='Password' id='signupPass'></div>
  <hr style="border:1px solid #2b2b2b;margin:8px 0;">
  <div style="text-align:left;font-weight:bold;margin-bottom:6px;">Emergency Contact 1</div>
  <div class="row"><input placeholder='Contact 1 Name' id='contact1Name'></div>
  <div class="row"><input placeholder='Contact 1 Phone (+countrycode)' id='contact1Phone'></div>
  <div class="row"><input placeholder='Relation' id='contact1Relation'></div>
  <div style="text-align:left;font-weight:bold;margin:6px 0;">Emergency Contact 2</div>
  <div class="row"><input placeholder='Contact 2 Name' id='contact2Name'></div>
  <div class="row"><input placeholder='Contact 2 Phone (+countrycode)' id='contact2Phone'></div>
  <div class="row"><input placeholder='Relation' id='contact2Relation'></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px;">
    <button onclick="signup()">Signup</button>
    <button onclick="closePopup('signupPopup')">Close</button>
  </div>
</div>

<!-- FORGOT PASSWORD POPUP -->
<div class="popup" id="forgotPopup" style="display:none;">
  <h3>Reset Password</h3>
  <div class="row"><input id="resetEmail" placeholder="Registered email"></div>
  <div class="row"><input id="newPass" type="password" placeholder="New password"></div>
  <div class="row"><input id="confirmPass" type="password" placeholder="Confirm password"></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px;">
    <button onclick="resetPassword()">Reset</button>
    <button onclick="closeForgotPopup()">Cancel</button>
  </div>
</div>

<!-- Trackers -->
<div class="popup" id="trackerPopup"><h3>Health Tracker</h3><input type="date"><br><br><textarea rows="4" placeholder="Notes..."></textarea><br><br><button onclick="closePopup('trackerPopup')">Close</button></div>
<div class="popup" id="dietPopup"><h3>Diet Tracker</h3><input placeholder='Enter food'><br><br><button onclick="addMessage('Bot','This food is healthy with moderate calories!')">Analyze</button><br><br><button onclick="closePopup('dietPopup')">Close</button></div>
<div class="popup" id="moodPopup"><h3>Mood Tracker</h3><input placeholder='How are you feeling today?'><br><br><button onclick="addMessage('Bot','Mood noted!')">Save</button><br><br><button onclick="closePopup('moodPopup')">Close</button></div>
<div class="popup" id="menstrualPopup"><h3>Menstrual Cycle</h3><input type="date"><br><br><textarea rows="3" placeholder="Symptoms..."></textarea><br><br><button onclick="closePopup('menstrualPopup')">Close</button></div>

<!-- Robot -->
<div class="robot">
<svg viewBox="0 0 64 64">
<rect x="10" y="20" width="44" height="30" rx="8" ry="8" fill="#c77dff"/>
<circle cx="24" cy="35" r="4" fill="#fff"/>
<circle cx="40" cy="35" r="4" fill="#fff"/>
<rect x="28" y="50" width="8" height="4" rx="2" fill="#fff"/>
<rect x="29" y="10" width="6" height="10" rx="3" fill="#c77dff"/>
</svg>
</div>
<div class="robot-tip">🤖 Stay hydrated 💧</div>

<script>
// ---------- Chat helpers ----------
const chat = document.getElementById('chat');
function formatTime() {
  const d = new Date();
  return String(d.getHours()).padStart(2,'0')+":"+String(d.getMinutes()).padStart(2,'0');
}
function addMessage(sender,text){
  const msg=document.createElement('div');
  msg.className='msg '+(sender==='You'?'user':'bot');
  const time=formatTime();
  msg.innerHTML='<div><strong>'+sender+'</strong></div><div>'+text+'</div><span class="time">'+time+'</span>';
  chat.appendChild(msg);
  chat.scrollTop=chat.scrollHeight;
}
async function sendMessage(){
  const input=document.getElementById('userInput');
  const text=input.value.trim();
  if(!text) return;
  addMessage('You',text);
  input.value='';
  const email=localStorage.getItem('vha_user')||'';
  const res=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,email})});
  const data=await res.json();
  addMessage('Bot',data.reply);
  if(data.emergency){ try{ new Audio('/sounds/alert.wav').play(); }catch(e){} }
}
document.getElementById('userInput').addEventListener('keypress',function(e){if(e.key==='Enter') sendMessage();});

// ---------- Other frontend functions ----------
function study(){ addMessage('Bot','Opening medical study info...');window.open('https://www.webmd.com/','_blank'); }
function search(){ const t=document.getElementById('userInput').value||'health'; window.open('https://www.google.com/search?q='+encodeURIComponent(t),'_blank'); }
function uploadPhoto(){ const input=document.createElement('input'); input.type='file'; input.accept='image/*'; input.onchange=()=>addMessage('Bot','🩺 Analysing... (fake) mild infection detected.'); input.click(); }
function togglePanel(){ document.getElementById('panel').style.display=document.getElementById('panel').style.display==='block'?'none':'block'; }
function toggleDark(){ document.body.style.background=document.body.style.background==='black'?'#0b0b0b':'black'; }
function openPopup(id){ document.getElementById(id).style.display='block'; }
function closePopup(id){ document.getElementById(id).style.display='none'; }

// ---------- Signup/Login ----------
async function signup(){
  const name=document.getElementById('signupName').value.trim();
  const email=document.getElementById('signupEmail').value.trim();
  const pass=document.getElementById('signupPass').value;
  const contact1={name:document.getElementById('contact1Name').value.trim(),phone:document.getElementById('contact1Phone').value.trim(),relation:document.getElementById('contact1Relation').value.trim()};
  const contact2={name:document.getElementById('contact2Name').value.trim(),phone:document.getElementById('contact2Phone').value.trim(),relation:document.getElementById('contact2Relation').value.trim()};
  if(!name||!email||!pass||!contact1.phone||!contact2.phone){alert('Fill required fields and provide two emergency contacts'); return;}
  let users=JSON.parse(localStorage.getItem('vha_users')||'[]');
  if(!users.find(u=>u.email===email)){users.push({name,email,password:pass});localStorage.setItem('vha_users',JSON.stringify(users));}else{users=users.map(u=>u.email===email?{...u,password:pass,name}:u);localStorage.setItem('vha_users',JSON.stringify(users));}
 await fetch('/register', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ name, email, password: pass })  // ← now sending password
});
  const contacts=[contact1,contact2];
  await fetch('/set_contacts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,contacts})});
  localStorage.setItem('vha_user',email); alert('Signup successful!'); closePopup('signupPopup');
}
function login(){
  const email=document.getElementById('loginEmail').value.trim();
  const pass=document.getElementById('loginPass').value;
  const users=JSON.parse(localStorage.getItem('vha_users')||'[]');
  const user=users.find(u=>u.email===email);
  if(!user){alert('User not found'); return;}
  if(user.password!==pass){alert('Wrong password'); return;}
  localStorage.setItem('vha_user',email); alert('Login successful'); closePopup('loginPopup');
}
function openForgotPopup(){document.getElementById('forgotPopup').style.display='block'; closePopup('loginPopup');}
function closeForgotPopup(){document.getElementById('forgotPopup').style.display='none';}
function resetPassword(){const email=document.getElementById('resetEmail').value.trim(); const newPass=document.getElementById('newPass').value; const confirm=document.getElementById('confirmPass').value; const users=JSON.parse(localStorage.getItem('vha_users')||'[]'); const idx=users.findIndex(u=>u.email===email); if(idx===-1){alert('Email not found'); return;} if(newPass!==confirm){alert('Passwords do not match'); return;} users[idx].password=newPass; localStorage.setItem('vha_users',JSON.stringify(users)); alert('Password reset successful'); closeForgotPopup(); }
async function setContacts(contacts){const email=localStorage.getItem('vha_user'); if(!email){alert('Login first'); return;} await fetch('/set_contacts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,contacts})}); alert('Contacts saved'); }

// Bubbles
for(let i=0;i<20;i++){const b=document.createElement('div'); b.className='bubble'; b.style.width=b.style.height=Math.random()*20+10+'px'; b.style.left=Math.random()*100+'%'; b.style.animationDuration=Math.random()*5+5+'s'; document.getElementById('bubbles').appendChild(b);}
</script>
</body>
</html>
"""

# ------------------- Analyze -------------------
@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    message = data.get("message", "")
    email = data.get("email", "")
    reply, emergency = analyze_symptoms(message)

    if emergency and email:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM emergency_contacts WHERE user_id=(SELECT id FROM users WHERE email=%s)", (email,))
        contacts = cur.fetchall()
        for c in contacts:
            try:
                twilio_client.messages.create(
                    body=f"⚠️ Emergency alert from {email}: {message}",
                    from_=TWILIO_NUMBER,
                    to=c["phone"]
                )
            except Exception as e:
                print(f"Twilio error: {e}")
        cur.close()
        conn.close()

    return JSONResponse({"reply": reply, "emergency": emergency})

# ------------------- Register -------------------
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    if not name or not email or not password:
        raise HTTPException(400, "Missing fields")
    hashed = hash_password(password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users (name,email,password,created_at) VALUES (%s,%s,%s,%s)",
                    (name,email,hashed,datetime.datetime.now()))
        conn.commit()
    cur.close()
    conn.close()
    return JSONResponse({"status":"ok"})

# ------------------- Login -------------------
@app.post("/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(400, "Missing fields")
    hashed = hash_password(password)
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user or user["password"] != hashed:
        raise HTTPException(400, "Invalid credentials")
    return JSONResponse({"status":"ok","name":user["name"],"email":user["email"]})

# ------------------- Set Emergency Contacts -------------------
@app.post("/set_contacts")
async def set_contacts(request: Request):
    data = await request.json()
    email = data.get("email")
    contacts = data.get("contacts", [])
    if not email or not contacts:
        raise HTTPException(400,"Missing email or contacts")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s",(email,))
    res=cur.fetchone()
    if not res: cur.close(); conn.close(); raise HTTPException(400,"User not found")
    user_id=res[0]
    cur.execute("DELETE FROM emergency_contacts WHERE user_id=%s",(user_id,))
    for c in contacts:
        cur.execute("INSERT INTO emergency_contacts (user_id,name,phone,relation) VALUES (%s,%s,%s,%s)",
                    (user_id,c["name"],c["phone"],c["relation"]))
    conn.commit()
    cur.close()
    conn.close()
    return JSONResponse({"status":"contacts saved"})
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Use Railway's port or 8000 locally
    uvicorn.run(app, host="0.0.0.0", port=port)
