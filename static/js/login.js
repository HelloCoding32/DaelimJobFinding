const messageDiv = document.getElementById("message");
const loginBtn = document.getElementById("loginBtn");

function showMessage(text, type) {
  messageDiv.textContent = text;
  messageDiv.className = `message ${type}`;
  messageDiv.style.display = "block";
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  loginBtn.disabled = true;
  loginBtn.textContent = "로그인 중...";

  const formData = new FormData(e.target);

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (data.success) {
      showMessage(data.message, "success");
      localStorage.setItem("user_id", data.user_id);
      localStorage.setItem("user_name", data.user_name);

      setTimeout(() => {
        window.location.href = "/chat";
      }, 1000);
    } else {
      showMessage(data.message, "error");
      loginBtn.disabled = false;
      loginBtn.textContent = "로그인";
    }
  } catch (error) {
    console.error("에러 발생:", error);
    showMessage("서버와의 통신에 실패했습니다.", "error");
    loginBtn.disabled = false;
    loginBtn.textContent = "로그인";
  }
});

// 아이디 찾기 / 비밀번호 찾기 링크 (기존 동작 유지)
const findIdLink = document.querySelector('a[href="find-id"]');
if (findIdLink) {
  findIdLink.addEventListener("click", () => {});
}

const findPwLink = document.querySelector('a[href="/find-pw"]');
if (findPwLink) {
  findPwLink.addEventListener("click", () => {});
}
