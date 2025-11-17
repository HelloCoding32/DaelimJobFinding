const findIdBtn = document.getElementById("findIdBtn");

document.getElementById("findIdForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    findIdBtn.disabled = true;
    findIdBtn.textContent = "찾는 중...";

    const formData = new FormData(e.target);
    const name = formData.get("name");

    try {
        const res = await fetch("/api/find-id", {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
        });

        const data = await res.json();

        if (res.ok && data.success) {
            alert(`${data.name}님의 아이디는 [ ${data.user_id} ] 입니다.`);
            window.location.href = "/"; 
        } else {
            alert(data.message || "해당 이름으로 등록된 아이디가 없습니다.");
            findIdBtn.disabled = false;
            findIdBtn.textContent = "아이디 찾기";
        }
    } catch (error) {
        console.error("에러 발생:", error);
        alert("서버와의 통신에 실패했습니다.");
        findIdBtn.disabled = false;
        findIdBtn.textContent = "아이디 찾기";
    }
});
