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
    const setChatOpen = (isOpen) => {
      panel.hidden = !isOpen;
      launcher.hidden = isOpen;
      if (isOpen) chatForm.elements.question.focus();
    };
    launcher.addEventListener("click", () => setChatOpen(true));
    closeButton.addEventListener("click", () => setChatOpen(false));
    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const input = chatForm.elements.question;
      const question = input.value.trim();
      if (!question) return;
      appendMessage(question, "user-message");
      appendMessage(getAnswer(question), "bot-message");
      input.value = "";
      chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    function appendMessage(text, className) {
      const message = document.createElement("div");
      message.className = `chat-message ${className}`;
      message.textContent = text;
      chatMessages.append(message);
    }

    function getAnswer(question) {
      const text = question.toLowerCase();
      if (/available|inventory|cars|collection|stock/.test(text)) return "Browse our current collection on the Browse Cars page. Our team can also source a specific make or model for you.";
      if (/price|cost|kes|how much/.test(text)) return "Each vehicle's price is listed on its details page. For a tailored quote or current availability, call +254 792 194 284.";
      if (/spec|engine|mileage|transmission|fuel/.test(text)) return "Open any car's details page to see its engine, mileage, transmission, fuel type and full description.";
      if (/test.?drive|drive|viewing/.test(text)) return "We would be delighted to arrange a private viewing or test drive. Send us an enquiry on the Contact page or WhatsApp +254 792 194 284.";
      if (/financ|loan|payment|installment/.test(text)) return "We offer car financing assistance and can connect you with suitable finance partners. Contact our team to discuss your options.";
      if (/import|source|order/.test(text)) return "Our team can assist with sourcing and importing a vehicle. Tell us what you are looking for on the Contact page.";
      if (/contact|phone|email|call|whatsapp/.test(text)) return "Call +254 792 194 284, email hello@guledmotors.co.ke, or message us on WhatsApp from the Contact page.";
      if (/where|location|address|visit|hours/.test(text)) return "Visit us on Ngong Road, Nairobi. We are open Monday to Saturday, 9:00 am–6:00 pm.";
      return "I can help with available cars, prices, specifications, test drives, financing, importation and our location. What would you like to know?";
    }
  }

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
});
