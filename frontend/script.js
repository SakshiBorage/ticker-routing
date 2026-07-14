const API_BASE_URL = "http://127.0.0.1:8000";
const CLASSIFY_ENDPOINT = `${API_BASE_URL}/tickets/classify/validated`;

const form = document.getElementById("ticket-form");
const input = document.getElementById("ticket-input");
const submitBtn = document.getElementById("submit-btn");
const notification = document.getElementById("notification");
const notificationMessage = document.getElementById("notification-message");
const notificationClose = document.getElementById("notification-close");

let hideTimeout = null;

function showNotification(message, type) {
  clearTimeout(hideTimeout);
  notificationMessage.textContent = message;
  notification.className = `notification ${type}`;
  hideTimeout = setTimeout(hideNotification, 6000);
}

function hideNotification() {
  clearTimeout(hideTimeout);
  notification.className = "notification hidden";
}

notificationClose.addEventListener("click", hideNotification);

const submitBtnLabel = submitBtn.querySelector(".btn-label");

function setSubmitting(isSubmitting) {
  submitBtn.disabled = isSubmitting;
  submitBtnLabel.textContent = isSubmitting ? "Submitting..." : "Submit Ticket";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const ticket = input.value.trim();
  if (!ticket) {
    showNotification("Please enter a ticket description before submitting.", "error");
    return;
  }

  setSubmitting(true);

  try {
    const response = await fetch(CLASSIFY_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticket }),
    });

    if (!response.ok) {
      let detail = "Something went wrong while submitting your ticket. Please try again.";
      try {
        const errorBody = await response.json();
        if (errorBody && errorBody.detail) {
          detail = errorBody.detail;
        }
      } catch (_) {
        // response body wasn't JSON; keep the generic message
      }
      console.error("Ticket submission failed:", detail);
      showNotification(detail, "error");
      return;
    }

    const result = await response.json();
    console.log("Ticket classification result:", result);

    showNotification("Your request has been submitted and will be processed soon.", "success");
    form.reset();
  } catch (error) {
    console.error("Ticket submission error:", error);
    showNotification(
      "Could not reach the server. Please check your connection and try again.",
      "error"
    );
  } finally {
    setSubmitting(false);
  }
});
