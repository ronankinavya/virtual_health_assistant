// 🌌 Create Moving Bubbles
const bubbleContainer = document.getElementById("bubbles");
for (let i = 0; i < 30; i++) {
  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  const size = Math.random() * 60 + 10;
  bubble.style.width = `${size}px`;
  bubble.style.height = `${size}px`;
  bubble.style.left = `${Math.random() * 100}%`;
  bubble.style.animationDuration = `${10 + Math.random() * 10}s`;
  bubble.style.animationDelay = `${Math.random() * 5}s`;
  bubbleContainer.appendChild(bubble);
}

// 🧠 Chat placeholder
function sendMessage() {
  const input = document.getElementById("userInput");
  const chat = document.getElementById("chat");
  if (!input.value.trim()) return;

  const userMsg = document.createElement("div");
  userMsg.className = "msg user";
  userMsg.textContent = input.value;
  chat.appendChild(userMsg);

  const botMsg = document.createElement("div");
  botMsg.className = "msg assistant";
  botMsg.textContent = "🤖 Analyzing your symptoms...";
  chat.appendChild(botMsg);

  input.value = "";
  chat.scrollTop = chat.scrollHeight;
}

// ⚙️ Toggle settings panel
function togglePanel() {
  document.getElementById("panel").classList.toggle("show");
}

// 📅 Calendar toggle
function toggleCalendar() {
  document.getElementById("calendar").classList.toggle("show");
}
