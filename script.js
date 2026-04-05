// =============================================
//  CHATROOM — script.js
// =============================================

var ws = null;
var myName = "";

// ── Connect ──────────────────────────────────
function connect() {
    myName = document.getElementById("username").value.trim();
    if (!myName) return;

    var proto = window.location.protocol === "https:" ? "wss://" : "ws://";
    ws = new WebSocket(proto + window.location.host + "/ws/" + myName);

    // Switch views
    document.getElementById("login-section").classList.add("d-none");
    var chatSection = document.getElementById("chat-section");
    chatSection.classList.remove("d-none");
    chatSection.classList.add("d-flex");

    // WebSocket events
    ws.onopen    = onOpen;
    ws.onmessage = onMessage;
    ws.onclose   = onClose;
    ws.onerror   = onError;
}

// ── WebSocket Handlers ───────────────────────
function onOpen() {
    appendSystemMsg("Connected as " + myName);
}

function onMessage(event) {
    var chatBox = document.getElementById("chat-box");
    var messageDiv = document.createElement("div");

    if (event.data.startsWith("System:")) {
        messageDiv.className = "msg system-msg";
        messageDiv.innerText = event.data.replace("System: ", "");

        // Update online count if message contains that info
        updateOnlineCount(event.data);
    } else {
        var colonIndex = event.data.indexOf(": ");
        var sender = event.data.substring(0, colonIndex);
        var text   = event.data.substring(colonIndex + 2);

        if (sender === "Bot") {
            messageDiv.className = "msg bot-msg";
        } else if (sender === myName) {
            messageDiv.className = "msg my-msg";
        } else {
            messageDiv.className = "msg other-msg";
        }

        messageDiv.innerHTML =
            '<div class="msg-name">' + escapeHTML(sender) + '</div>' +
            '<div>' + escapeHTML(text) + '</div>';
    }

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function onClose() {
    appendSystemMsg("Disconnected from chatroom");
    document.getElementById("user-count").textContent = "0";
}

function onError() {
    appendSystemMsg("Connection error — please refresh");
}

// ── Send Message ─────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("message-form");
    if (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            sendMessage();
        });
    }
});

function sendMessage() {
    var input = document.getElementById("messageText");
    var text  = input.value.trim();
    if (text !== "" && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(text);
        input.value = "";
    }
}

// ── Helpers ──────────────────────────────────

// Append a local system message (not from server)
function appendSystemMsg(text) {
    var chatBox = document.getElementById("chat-box");
    var div = document.createElement("div");
    div.className = "msg system-msg";
    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Parse online count from system messages like "System: 3 users online"
function updateOnlineCount(data) {
    var match = data.match(/(\d+)\s+user/i);
    if (match) {
        document.getElementById("user-count").textContent = match[1];
    }
}

// Prevent XSS — escape user-generated text before injecting into DOM
function escapeHTML(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}