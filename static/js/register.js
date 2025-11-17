const messageDiv = document.getElementById("message");
const registerBtn = document.getElementById("registerBtn");

function showMessage(text, type) {
  messageDiv.textContent = text;
  messageDiv.className = `message ${type}`;
  messageDiv.style.display = "block";
}

document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  registerBtn.disabled = true;
  registerBtn.textContent = "처리 중...";

  const formData = new FormData(e.target);

  try {
    const res = await fetch("/api/register", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (data.success) {
      showMessage(data.message, "success");
      setTimeout(() => {
        window.location.href = "/login";
      }, 2000);
    } else {
      showMessage(data.message, "error");
      registerBtn.disabled = false;
      registerBtn.textContent = "가입하기";
    }
  } catch (error) {
    console.error("에러 발생:", error);
    showMessage("서버와의 통신에 실패했습니다.", "error");
    registerBtn.disabled = false;
    registerBtn.textContent = "가입하기";
  }
});
