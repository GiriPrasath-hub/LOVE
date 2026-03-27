const API_URL = "http://127.0.0.1:8000";

let currentSituation = "";
let selectedIndex = -1;

const suggestionsList = [
    "sorry for the inconvenience",
    "i sincerely apologize for the delay",
    "thank you for your patience",
    "we appreciate your support",
    "let me help you resolve this",
    "i will assist you right away",
    "we will fix this issue quickly"
];

// LOAD
async function loadSituation() {
    const res = await fetch(`${API_URL}/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
    });

    const data = await res.json();

    currentSituation = data.observation.echoed_message.replace("Situation: ", "");
    document.getElementById("situation").innerText = "Situation: " + currentSituation;

    document.getElementById("output").innerHTML = "";
}

const input = document.getElementById("inputBox");
const suggestionBox = document.getElementById("suggestions");

// INPUT SUGGESTIONS
input.addEventListener("input", () => {
    const value = input.value.toLowerCase();
    suggestionBox.innerHTML = "";

    if (!value) {
        suggestionBox.style.display = "none";
        return;
    }

    const filtered = suggestionsList.filter(item =>
        item.includes(value)
    );

    filtered.forEach((item, index) => {
        const div = document.createElement("div");
        div.innerText = item;

        div.onclick = () => {
            input.value = item;
            suggestionBox.style.display = "none";
            sendAction(item);
        };

        suggestionBox.appendChild(div);
    });

    selectedIndex = -1;
    suggestionBox.style.display = filtered.length ? "block" : "none";
});

// KEYBOARD NAV
input.addEventListener("keydown", (e) => {
    const items = suggestionBox.querySelectorAll("div");

    if (e.key === "ArrowDown") {
        selectedIndex++;
        if (selectedIndex >= items.length) selectedIndex = 0;
        updateSelection(items);
    }

    else if (e.key === "ArrowUp") {
        selectedIndex--;
        if (selectedIndex < 0) selectedIndex = items.length - 1;
        updateSelection(items);
    }

    else if (e.key === "Enter") {
        if (selectedIndex >= 0) {
            input.value = items[selectedIndex].innerText;
        }
        sendAction(input.value);
        suggestionBox.style.display = "none";
    }
});

function updateSelection(items) {
    items.forEach((item, index) => {
        item.classList.toggle("active", index === selectedIndex);
    });
}

// SEND ACTION
async function sendAction(text) {
    if (!text) return;

    const output = document.getElementById("output");

    // ⏳ Typing effect
    output.innerHTML = "⏳ Evaluating...";
    
    const res = await fetch(`${API_URL}/step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            action: {
                message: text,
                scenario: currentSituation
            }
        })
    });

    const data = await res.json();

    const score = data.reward;
    let barClass = "bad";
    if (score > 0.7) barClass = "good";
    else if (score > 0.3) barClass = "mid";

    output.innerHTML = `
        ${data.observation.echoed_message}
        <br><br>
        ⭐ Score: ${score}
        <div class="bar-container">
            <div class="bar ${barClass}" style="width:${score * 100}%"></div>
        </div>
    `;

    input.value = "";

    if (data.done) {
        setTimeout(loadSituation, 2500);
    }
}

loadSituation();