const themeToggle = document.querySelector(".theme-toggle");
const menuToggle = document.querySelector(".menu-toggle");
const nav = document.querySelector(".main-nav");
const notificationToggle = document.querySelector(".notification-toggle");
const notificationPopover = document.querySelector(".notification-popover");
const accountButton = document.querySelector(".account-button");
const accountPopover = document.querySelector(".account-popover");

if (localStorage.getItem("c4g-theme") === "dark") {
  document.documentElement.dataset.theme = "dark";
  themeToggle?.setAttribute("aria-label", "Switch to light theme");
  if (themeToggle) themeToggle.innerHTML = '<span aria-hidden="true">☀</span>';
}

themeToggle?.addEventListener("click", () => {
  const isDark = document.documentElement.dataset.theme !== "dark";
  document.documentElement.dataset.theme = isDark ? "dark" : "light";
  localStorage.setItem("c4g-theme", isDark ? "dark" : "light");
  themeToggle.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
  themeToggle.innerHTML = isDark ? '<span aria-hidden="true">☀</span>' : '<span aria-hidden="true">☾</span>';
});

menuToggle?.addEventListener("click", () => {
  const isOpen = nav.classList.toggle("nav-open");
  menuToggle.setAttribute("aria-expanded", String(isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
});

notificationToggle?.addEventListener("click", () => {
  const isOpen = notificationPopover.hidden;
  notificationPopover.hidden = !isOpen;
  notificationToggle.setAttribute("aria-expanded", String(isOpen));
  accountPopover && (accountPopover.hidden = true);
});

accountButton?.addEventListener("click", () => {
  const isOpen = accountPopover.hidden;
  accountPopover.hidden = !isOpen;
  accountButton.setAttribute("aria-expanded", String(isOpen));
  if (notificationPopover) notificationPopover.hidden = true;
});

document.addEventListener("click", (event) => {
  if (notificationPopover && !notificationPopover.hidden &&
      !notificationPopover.contains(event.target) && !notificationToggle.contains(event.target)) {
    notificationPopover.hidden = true;
    notificationToggle.setAttribute("aria-expanded", "false");
  }
  if (accountPopover && !accountPopover.hidden &&
      !accountPopover.contains(event.target) && !accountButton.contains(event.target)) {
    accountPopover.hidden = true;
    accountButton.setAttribute("aria-expanded", "false");
  }
});

document.querySelectorAll(".flash-close").forEach((button) => {
  button.addEventListener("click", () => button.closest(".flash").remove());
});

window.setTimeout(() => {
  document.querySelectorAll(".flash").forEach((flash) => flash.classList.add("flash-hide"));
}, 5000);

const chatForm = document.querySelector("[data-chat-form]");
const chatMessages = document.querySelector("[data-chat-messages]");

function appendChatMessage(message, type, speaker) {
  const item = document.createElement("div");
  item.className = `chat-message ${type}`;
  const label = document.createElement("span");
  label.className = "chat-speaker";
  label.textContent = speaker;
  const text = document.createElement("p");
  text.textContent = message;
  item.append(label, text);
  chatMessages.append(item);
  item.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

if (chatForm && chatMessages) {
  const questionInput = chatForm.querySelector('input[name="question"]');
  const sendButton = chatForm.querySelector('button[type="submit"]');

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    appendChatMessage(question, "learner-message", "You");
    questionInput.value = "";
    questionInput.disabled = true;
    sendButton.disabled = true;
    sendButton.textContent = "…";

    try {
      const response = await fetch(chatForm.dataset.chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "The course assistant couldn’t answer just now.");
      }
      appendChatMessage(result.answer, "assistant-message", "Course assistant");
    } catch (error) {
      appendChatMessage(error.message, "assistant-message chat-error", "Assistant unavailable");
    } finally {
      questionInput.disabled = false;
      sendButton.disabled = false;
      sendButton.textContent = "↑";
      questionInput.focus();
    }
  });

  document.querySelectorAll("[data-chat-suggestion]").forEach((button) => {
    button.addEventListener("click", () => {
      questionInput.value = button.dataset.chatSuggestion;
      chatForm.requestSubmit();
    });
  });
}

document.querySelectorAll("[data-certificate-code]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.querySelector("#certificate-code");
    input.value = button.dataset.certificateCode;
    input.form.requestSubmit();
  });
});

document.querySelector("[data-print-certificate]")?.addEventListener("click", () => {
  window.print();
});
