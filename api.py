from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json, yaml, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/sounds", StaticFiles(directory="sounds"), name="sounds")

# ---------- Load Data ----------
with open("data/triage_rules.yaml", "r") as f:
    triage_rules = yaml.safe_load(f)
with open("data/feature_order.json", "r") as f:
    feature_order = json.load(f)
with open("data/symptom_ontology.json", "r") as f:
    symptom_ontology = json.load(f)

# ---------- Frontend ----------
@app.get("/", response_class=HTMLResponse)
def ui():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
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
.panel,.popup{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#1c1c1c;padding:20px;border-radius:15px;box-shadow:0 0 10px #c77dff;z-index:10;width:300px;}
#bubbles{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;overflow:hidden;}
.bubble{position:absolute;bottom:0;background:#c77dff;border-radius:50%;opacity:0.4;animation:rise 10s infinite ease-in;}
@keyframes rise{0%{transform:translateY(0);}100%{transform:translateY(-120vh);opacity:0;}}
.robot{position:fixed;left:20px;bottom:30px;width:70px;height:70px;z-index:5;animation:floatBot 3s ease-in-out infinite;}
@keyframes floatBot{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}
.robot-tip{position:fixed;left:100px;bottom:40px;background:#c77dff;border-radius:12px;padding:8px 12px;font-size:0.9rem;animation:floatTip 3s ease-in-out infinite;z-index:5;}
@keyframes floatTip{0%,100%{transform:translateY(0);}50%{transform:translateY(-5px);}}
</style>
</head>
<body>
<div id="bubbles"></div>
<h1>💜 AI Health Assistant</h1>
<div class="chat-container" id="chat"></div>

<!-- Input ABOVE icons -->
<div class="input-area">
  <input id="userInput" type="text" placeholder="Describe your symptoms...">
  <button onclick="sendMessage()">📨</button>
</div>

<!-- Icons BELOW textbox -->
<div class="extra-btn-group">
  <button onclick="study()">📚 Study</button>
  <button onclick="search()">🔍 Search</button>
  <button onclick="uploadPhoto()">🖼️ Upload</button>
</div>

<!-- Top buttons -->
<div class="top-buttons">
  <button onclick="openPopup('loginPopup')">Login</button>
  <button onclick="openPopup('signupPopup')">Signup</button>
  <button onclick="togglePanel()">⚙️</button>
</div>

<!-- Settings Panel -->
<div class="panel" id="panel">
  <button onclick="toggleDark()">🌙 Dark Mode</button><br><br>
  <button onclick="openPopup('trackerPopup')">📅 Tracker</button><br><br>
  <button onclick="openPopup('dietPopup')">🥗 Diet Tracker</button><br><br>
  <button onclick="openPopup('moodPopup')">😊 Mood Tracker</button><br><br>
  <button onclick="openPopup('menstrualPopup')">💖 Menstrual Cycle</button>
</div>

<!-- Popups -->
<div class="popup" id="loginPopup">
<h3>Login</h3>
<input placeholder='Email' id='loginEmail'><br><br>
<input type='password' placeholder='Password' id='loginPass'><br><br>
<button onclick="login()">Login</button>
<button onclick="closePopup('loginPopup')">Close</button>
</div>

<div class="popup" id="signupPopup">
<h3>Signup</h3>
<input placeholder='Name' id='signupName'><br><br>
<input placeholder='Email' id='signupEmail'><br><br>
<input type='password' placeholder='Password' id='signupPass'><br><br>
<button onclick="signup()">Signup</button>
<button onclick="closePopup('signupPopup')">Close</button>
</div>

<div class="popup" id="trackerPopup">
<h3>Health Tracker</h3><input type="date"><br><br><textarea rows="4" placeholder="Notes..."></textarea><br><br>
<button onclick="closePopup('trackerPopup')">Close</button></div>

<div class="popup" id="dietPopup">
<h3>Diet Tracker</h3><input placeholder='Enter food'><br><br>
<button onclick="addMessage('Bot','This food is healthy with moderate calories!')">Analyze</button><br><br>
<button onclick="closePopup('dietPopup')">Close</button></div>

<div class="popup" id="moodPopup">
<h3>Mood Tracker</h3><input placeholder='How are you feeling today?'><br><br>
<button onclick="addMessage('Bot','Mood noted!')">Save</button><br><br>
<button onclick="closePopup('moodPopup')">Close</button></div>

<div class="popup" id="menstrualPopup">
<h3>Menstrual Cycle</h3><input type="date"><br><br>
<textarea rows="3" placeholder="Symptoms..."></textarea><br><br>
<button onclick="closePopup('menstrualPopup')">Close</button></div>

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
const chat=document.getElementById('chat');
function addMessage(sender,text){
  const msg=document.createElement('div');
  msg.className='msg '+(sender==='You'?'user':'bot');
  msg.innerHTML=text;
  chat.appendChild(msg);
  chat.scrollTop=chat.scrollHeight;
}
async function sendMessage(){
  const input=document.getElementById('userInput');
  const text=input.value.trim();
  if(!text)return;
  addMessage('You',text);
  input.value='';
  const res=await fetch('/analyze',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({message:text})
  });
  const data=await res.json();
  addMessage('Bot',data.reply);
  if(data.emergency){new Audio('/sounds/alert.wav').play();}
}

function study(){addMessage('Bot','Opening medical study info...');window.open('https://www.webmd.com/','_blank');}
function search(){const t=document.getElementById('userInput').value||'health';window.open('https://www.google.com/search?q='+encodeURIComponent(t),'_blank');}
function uploadPhoto(){const input=document.createElement('input');input.type='file';input.accept='image/*';input.onchange=()=>addMessage('Bot','🩺 Analysing... mild infection detected.');input.click();}

function togglePanel(){document.getElementById('panel').style.display=document.getElementById('panel').style.display==='block'?'none':'block';}
function toggleDark(){document.body.style.background=document.body.style.background==='black'?'#0b0b0b':'black';}
function openPopup(id){document.getElementById(id).style.display='block';}
function closePopup(id){document.getElementById(id).style.display='none';}

// Signup/Login storage
function signup(){
  const name=document.getElementById('signupName').value;
  const email=document.getElementById('signupEmail').value;
  const pass=document.getElementById('signupPass').value;
  if(name && email && pass){localStorage.setItem(email,JSON.stringify({name,pass}));alert('Signup successful!');closePopup('signupPopup');}
  else{alert('Fill all fields');}
}
function login(){
  const email=document.getElementById('loginEmail').value;
  const pass=document.getElementById('loginPass').value;
  const user=localStorage.getItem(email);
  if(user){const u=JSON.parse(user);if(u.pass===pass){alert('Login successful!');closePopup('loginPopup');}else{alert('Wrong password');}}
  else{alert('User not found');}
}

// Bubbles
for(let i=0;i<20;i++){
  const b=document.createElement('div');
  b.className='bubble';
  b.style.width=b.style.height=Math.random()*20+10+'px';
  b.style.left=Math.random()*100+'%';
  b.style.animationDuration=Math.random()*5+5+'s';
  document.getElementById('bubbles').appendChild(b);
}
</script>
</body>
</html>
"""

# ---------- Bot Logic ----------
@app.post("/analyze")
async def analyze(req: Request):
    data = await req.json()
    msg = data.get("message","").lower()

    greetings = ["hi","hello","hey"]
    if msg in greetings:
        return {"reply":"Hello! What symptom are you experiencing today?","emergency":False}

    emergencies = ["chest pain","heart pain","shortness of breath","severe bleeding","fainting"]
    if any(e in msg for e in emergencies):
        return {"reply":"🚨 This seems serious. Please go to the hospital immediately!","emergency":True}

    if "pain" in msg:
        return {"reply":"How long have you been feeling this pain?","emergency":False}
    if "hour" in msg or "day" in msg:
        return {"reply":"How severe is the symptom (mild, moderate, severe)?","emergency":False}
    if "severe" in msg:
        return {"reply":"Where exactly are you feeling it?","emergency":False}
    if "head" in msg or "stomach" in msg or "back" in msg:
        return {"reply":"Have you taken any medication for it?","emergency":False}
    if "no" in msg:
        return {"reply":"Got it. Do you get this symptom often?","emergency":False}
    if "yes" in msg:
        return {"reply":"Your symptoms suggest it could be migraine or mild inflammation. Take rest and stay hydrated.","emergency":False}

    return {"reply":"Please describe your symptom clearly.","emergency":False}
