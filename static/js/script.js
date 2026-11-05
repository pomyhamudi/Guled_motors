document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.querySelector(".menu-toggle");
  const navigation = document.querySelector(".main-nav");
  if (menuButton && navigation) {
    const menuIcon = menuButton.querySelector("span");
    menuButton.addEventListener("click", () => {
      const isOpen = navigation.classList.toggle("is-open");
      menuButton.setAttribute("aria-expanded", String(isOpen));
      menuButton.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
      if (menuIcon) menuIcon.textContent = isOpen ? "×" : "☰";
    });
    navigation.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        navigation.classList.remove("is-open");
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.setAttribute("aria-label", "Open navigation");
        if (menuIcon) menuIcon.textContent = "☰";
      }
    });
  }

  const launcher = document.querySelector(".chat-launcher");
  const panel = document.querySelector(".chat-panel");
  const closeButton = document.querySelector(".chat-close");
  const chatForm = document.querySelector(".chat-form");
  const chatMessages = document.querySelector(".chat-messages");
  if (launcher && panel && closeButton && chatForm && chatMessages) {
    const input = chatForm.elements.question;
    const sendButton = chatForm.querySelector("button");
    const leadData = {};
    let leadField = null;
    const setChatOpen = (isOpen) => {
      panel.hidden = !isOpen;
      launcher.hidden = isOpen;
      if (isOpen) input.focus();
    };
    launcher.addEventListener("click", () => setChatOpen(true));
    closeButton.addEventListener("click", () => setChatOpen(false));
    chatForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = input.value.trim();
      if (!question) return;
      appendMessage(question, "user-message");
      input.value = "";
      input.disabled = true;
      sendButton.disabled = true;

      if (leadField) leadData[leadField] = question;
      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": chatForm.dataset.csrfToken,
          },
          body: JSON.stringify({ message: question, lead_data: { ...leadData } }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "The message could not be sent.");
        appendMessage(result.reply, "bot-message");
        leadField = result.lead_field || null;
        if (result.complete) {
          Object.keys(leadData).forEach((key) => delete leadData[key]);
        }
      } catch {
        appendMessage("Sorry, I couldn’t send that just now. Please try again or call +254 792 194 284.", "bot-message");
      } finally {
        input.disabled = false;
        sendButton.disabled = false;
        input.focus();
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    });

    function appendMessage(text, className) {
      const message = document.createElement("div");
      message.className = `chat-message ${className}`;
      message.textContent = text;
      chatMessages.append(message);
    }
  }

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
});
