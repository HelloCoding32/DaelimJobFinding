        // ===================================================================
        // 💡 [수정 및 추가된] JavaScript 로직
        // ===================================================================

        // --- 1. DOM 요소 선택 ---
        const chatBody = document.getElementById("chat-body");
        const msgInput = document.getElementById("message");
        const sendBtn = document.getElementById("sendBtn");
        // const profileInput = document.getElementById("profileInput"); // 💡 [제거]
        const settingsBtn = document.getElementById("settingsBtn");
        const settingsPanel = document.getElementById("settingsPanel");
        const logoutBtn = document.getElementById("logoutBtn");
        const logoutSettingBtn = document.getElementById("logoutSettingBtn");
        const newChatBtn = document.getElementById("newChatBtn");
        const chatList = document.getElementById("chatList");
        const infoToggleBtn = document.getElementById("infoToggleBtn");
        const recommendationPanel = document.getElementById("recommendationPanel");
        const analysisPanel = document.getElementById("analysisPanel");

        const sidebarTitle = document.getElementById("sidebarTitle");
        const infoHeaderTitle = document.getElementById("infoHeaderTitle");
        const infoPanelTitle = document.getElementById("infoPanelTitle");
        const analysisKeywordContainer = document.getElementById("analysisKeywordContainer");

        const editProfileBtn = document.getElementById("editProfileBtn");
        const editProfileModal = document.getElementById("editProfileModal");
        const modalUserId = document.getElementById("modalUserId");
        const modalNewPassword = document.getElementById("modalNewPassword");
        const modalUserName = document.getElementById("modalUserName");
        // const modalProfileInput = document.getElementById("modalProfileInput"); // 💡 [삭제] 모달의 프로필 입력 필드
        const updateProfileBtn = document.getElementById("updateProfileBtn");
        const cancelUpdateBtn = document.getElementById("cancelUpdateBtn");
        const updateStatusMessage = document.getElementById("updateStatusMessage");

        // --- 색상 설정 관련 DOM 추가 ---
        const bgColorInput = document.getElementById('bgColorInput');
        const bgColorPicker = document.getElementById('bgColorPicker');
        const textColorInput = document.getElementById('textColorInput');
        const textColorPicker = document.getElementById('textColorPicker');
        const colorPresetBtns = document.querySelectorAll('.color-preset-btn');


        // --- 2. 전역 변수 관리 ---
        let userName = "학생";
        let userId = null;
        // 💡 [수정] 프로필 이미지 소스를 상수로 고정 (기능 삭제)
        const userProfileSrc = "/static/png/user-profile.png";
        let conversationHistory = [];
        let chats = [];
        let currentChatIndex = -1;
        let currentConversationId = null;
        let isRecommendationMode = true;

        let jobMatchChart = null;

        // --- 3. 헬퍼 함수 정의 및 수정 ---

        // 💡 [삭제] fileToBase64 함수 제거

        // 💡 [수정] 프로필 이미지 경로 업데이트 로직 제거
        function updateUserUI(name) {
            userName = name;
            // userProfileSrc = profileSrc; // 💡 [삭제] 프로필 이미지 경로 업데이트 로직 제거
            if (sidebarTitle) sidebarTitle.textContent = `💬 ${name} 님의 상담 기록`;
            if (infoHeaderTitle) infoHeaderTitle.textContent = `🔍 ${name} 님의 맞춤형 진로 정보`;
            if (infoPanelTitle) infoPanelTitle.innerHTML = `
                <span style="color: #666;">📊</span>
                <span style="display:inline-block; margin-right:5px; font-weight: bold;">${name} 님의</span> AI 추천 직업
            `;
            document.querySelectorAll('.name-label.user').forEach(el => el.textContent = name);

            // 💡 [수정] 프로필 이미지 소스 고정
            document.querySelectorAll('.profile.user-img').forEach(img => {
                img.src = userProfileSrc;
            });

            // 💡 [삭제] localStorage에 이미지 경로 저장 로직 제거
        }

        function addEventListeners() {
            infoToggleBtn?.addEventListener('click', toggleInfoPanel);
            settingsBtn?.addEventListener('click', () => settingsPanel.classList.toggle("show"));
            // profileInput?.addEventListener("change", handleProfileImageChange); // 💡 [제거]

            editProfileBtn?.addEventListener('click', openEditProfileModal);
            cancelUpdateBtn?.addEventListener('click', closeEditProfileModal);
            updateProfileBtn?.addEventListener('click', handleUpdateProfile);
            window.addEventListener('click', (event) => {
                // 설정 패널 외부 클릭 시 패널 닫기
                if (!settingsPanel.contains(event.target) && event.target !== settingsBtn) {
                     settingsPanel.classList.remove("show");
                }
                if (event.target === editProfileModal) closeEditProfileModal();
            });

            logoutBtn?.addEventListener('click', logout);
            logoutSettingBtn?.addEventListener('click', logout);

            newChatBtn?.addEventListener("click", newChat);

            msgInput?.addEventListener("keypress", (e) => {
                if (e.key === "Enter") sendMessage();
            });

            sendBtn?.addEventListener("click", sendMessage);

            // --- 색상 설정 이벤트 리스너 추가 ---
            bgColorInput?.addEventListener('input', () => applyCustomColors(bgColorInput.value, 'bg'));
            bgColorPicker?.addEventListener('input', () => applyCustomColors(bgColorPicker.value, 'bg'));

            textColorInput?.addEventListener('input', () => applyCustomColors(textColorInput.value, 'text'));
            textColorPicker?.addEventListener('input', () => applyCustomColors(textColorPicker.value, 'text'));

            colorPresetBtns.forEach(btn => {
                btn.addEventListener('click', handleColorPreset);
            });

        }

        // 💡 [수정] 커스텀 색상 적용 함수 (이전 수정 사항 유지)
        function applyCustomColors(color, type) {
            const root = document.documentElement;

            if (type === 'bg') {
                root.style.setProperty('--custom-bg-color', color);
                localStorage.setItem('custom_bg_color', color);
                if (bgColorInput.value !== color) bgColorInput.value = color;
                if (bgColorPicker.value !== color) bgColorPicker.value = color;

            } else if (type === 'text') {
                root.style.setProperty('--custom-text-color', color);
                localStorage.setItem('custom_text_color', color);
                if (textColorInput.value !== color) textColorInput.value = color;
                if (textColorPicker.value !== color) textColorPicker.value = color;

                // 💡 [추가] primary 텍스트 색상도 custom-text-color를 따르도록 설정
                root.style.setProperty('--text-color-primary', color);
            }

            if (currentChatIndex >= 0) {
                const loadedRecs = chats[currentChatIndex].recommendations || [];
                const loadedKeywords = chats[currentChatIndex].keywords || [];
                updateJobMatchGraph(loadedKeywords, loadedRecs);
            }
        }

        // ===================================================================
        // 💡 [JS 수정] 색상 프리셋 핸들러: 텍스트 색상 강제 초기화 방지 및 가시성 확보 로직 추가 (이전 수정분 유지)
        // ===================================================================
        function handleColorPreset(event) {
            const btn = event.currentTarget;
            const type = btn.getAttribute('data-type');
            const color = btn.getAttribute('data-color');

            const currentTextColor = localStorage.getItem('custom_text_color');

            // 텍스트 색상 코드를 소문자로 통일
            const isTextDark = (currentTextColor && (currentTextColor.toLowerCase() === '#333333' || currentTextColor.toLowerCase() === 'black'));
            const isTextLight = (currentTextColor && (currentTextColor.toLowerCase() === '#ffffff' || currentTextColor.toLowerCase() === 'white' || currentTextColor.toLowerCase() === '#e0e0e0'));

            if (type === 'bg') {
                const isDarkMode = (color === '#1a1a2e');

                if (isDarkMode) {
                    document.body.classList.add('dark-mode');
                    // 💡 다크 모드 진입 시, 텍스트 색상이 너무 어두우면 (가시성이 낮으면) 밝게 변경하여 가시성 확보
                    if (!currentTextColor || isTextDark) {
                         applyCustomColors('#e0e0e0', 'text'); // 흰색 계열로 변경
                    }
                } else {
                    document.body.classList.remove('dark-mode');
                    // 💡 라이트 모드 진입 시, 텍스트 색상이 너무 밝으면 (가시성이 낮으면) 어둡게 변경하여 가시성 확보
                    if (!currentTextColor || isTextLight) {
                         applyCustomColors('#333333', 'text'); // 검은색 계열로 변경
                    }
                }
                applyCustomColors(color, 'bg');
            } else if (type === 'text') {
                // 텍스트 색상 프리셋은 무조건 적용
                applyCustomColors(color, 'text');
            }
        }

        // 💡 [원본 유지] sendMessage 함수
        async function sendMessage() {
            const msg = msgInput.value.trim();
            if (msg === "") return;
            if (!currentConversationId || !userId) {
                alert("오류: 세션이 만료되었거나 사용자가 없습니다. '새 대화'를 눌러주세요.");
                return;
            }

            addUserMessage(msg);
            msgInput.value = "";
            sendBtn.disabled = true;
            sendBtn.textContent = "...";

            try {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        user_id: userId,
                        user_input: msg,
                        history: conversationHistory,
                        conversation_id: currentConversationId
                    })
                });

                if (!res.ok) throw new Error(`서버 오류: ${res.status}`);
                const data = await res.json();

                console.log("✅ AI 응답:", data);

                // ✅ 1️⃣ 답변 출력
                addAIMessage(data.answer || "답변을 불러오지 못했습니다.");

                // ✅ 2️⃣ 추천 직업 / 분석 패널 업데이트
                updateAnalysisPanel(data.keywords, data.recommendations);
                updateInfoPanel(data);

                // ✅ 3️⃣ 히스토리 저장
                conversationHistory = data.new_history || [];
                if (currentChatIndex >= 0) {
                    const currentChat = chats[currentChatIndex];
                    currentChat.history = conversationHistory;
                    // 💡 [수정] "새 대화"일 때만 제목 업데이트
                    if (currentChat.title === "새 대화") {
                        currentChat.title = msg.length > 15 ? msg.slice(0, 15) + "..." : msg;
                    }
                    currentChat.recommendations = data.recommendations;
                    currentChat.keywords = data.keywords;
                    saveChats();
                }
                loadChatList(); // 💡 목록을 새로고침하여 제목 변경 반영

            } catch (error) {
                console.error("❌ 챗봇 통신 오류:", error);
                addAIMessage("죄송합니다, 메시지를 처리하는 중에 오류가 발생했습니다.");
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = "전송";
                if (chatBody) chatBody.scrollTop = chatBody.scrollHeight;
            }
        }

        // 💡 [원본 유지] updateAnalysisPanel, updateJobMatchGraph 함수
        function updateAnalysisPanel(keywords, recommendations) {

            if (analysisKeywordContainer) {
                if (!keywords || keywords.length === 0) {
                    analysisKeywordContainer.innerHTML = `
                        <div class="keyword-card">
                            <div class="keyword-label">분석 데이터</div>
                            <div class="keyword-value">정보 없음</div>
                        </div>`;
                } else {
                    analysisKeywordContainer.innerHTML = keywords.map(item => `
                        <div class="keyword-card">
                            <div class="keyword-label">${item.label || '항목'}</div>
                            <div class="keyword-value">${item.value || 'N/A'}</div>
                        </div>
                    `).join('');
                }
            }

            if (typeof Chart === 'undefined') {
                console.warn("Chart.js가 로드되지 않았습니다. 그래프를 그릴 수 없습니다.");
                const canvas = document.getElementById('jobMatchChart');
                if (canvas) {
                    const ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    ctx.fillStyle = 'red';
                    ctx.font = '14px "Noto Sans KR"';
                    ctx.fillText('Chart.js 로딩 실패', 10, 50);
                }
                return;
            }

            updateJobMatchGraph(keywords, recommendations);
        }

        function updateJobMatchGraph(keywords, recommendations) {
            if (!window.Chart || typeof Chart !== "function") {
                console.warn("Chart.js가 아직 로드되지 않았습니다.");
                return;
            }
            const ctx = document.getElementById('jobMatchChart');
            if (!ctx) return;

            const validRecs = (recommendations || []).filter(rec =>
                rec.job && !rec.job.startsWith("추천 직업")
            );
            const validKeywords = (keywords || []).map(k => k.value).filter(Boolean);

            let labels = [];
            let scores = [];

            if (validRecs.length > 0 && validKeywords.length > 0) {
                labels = validRecs.map(rec => rec.job);
                scores = validRecs.map(rec => {
                    let score = 0;
                    const combinedText = (rec.job + rec.reason).toLowerCase();
                    validKeywords.forEach(kw => {
                        if (combinedText.includes(kw.toLowerCase())) {
                            score += 1;
                        }
                        if (kw.includes("연봉") && combinedText.includes("게임 기획자")) {
                             score += 2;
                        }
                    });
                    let finalScore = (1 + score) * (100 / (validKeywords.length + 2));
                    return Math.min(finalScore, 100);
                });

            } else {
                labels = ["일치율 데이터 없음"];
                scores = [0];
            }

            if (jobMatchChart) {
                jobMatchChart.destroy();
            }

            const root = document.documentElement;
            const tickColor = getComputedStyle(root).getPropertyValue('--custom-text-color') || '#333333';


            jobMatchChart = new Chart(ctx, {
                // 💡 [수정] 막대 그래프의 방향을 'y'에서 'x'로 변경 (수직 막대)
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '학생-직업 일치율',
                        data: scores,
                        backgroundColor: [
                            'rgba(74, 144, 226, 0.7)',
                            'rgba(92, 184, 92, 0.7)',
                            'rgba(243, 156, 18, 0.7)',
                            'rgba(226, 74, 144, 0.7)', /* 추가 색상 */
                            'rgba(144, 226, 74, 0.7)'  /* 추가 색상 */
                        ],
                        borderColor: [
                            'rgba(74, 144, 226, 1)',
                            'rgba(92, 184, 92, 1)',
                            'rgba(243, 156, 18, 1)',
                            'rgba(226, 74, 144, 1)', /* 추가 색상 */
                            'rgba(144, 226, 74, 1)'  /* 추가 색상 */
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    // 💡 [수정] 막대 그래프의 방향을 'y'에서 'x'로 변경 (수직 막대)
                    indexAxis: 'x',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: { color: tickColor }
                        },
                        y: {
                            beginAtZero: true,
                            max: 100, /* Image 1의 y축 최대값 10과 유사하게 100으로 설정 */
                            ticks: { color: tickColor }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
        function updateKeywordChart(keywords) {
            const chartContainer = document.getElementById("keyword-chart");
            if (!chartContainer) return;

            const values = keywords.map(k => k.value);
            chartContainer.innerHTML = `
                <h4>학생 키워드 분석</h4>
                <ul>${values.map(v => `<li>${v}</li>`).join("")}</ul>
            `;
        }

        function updateInfoPanel(data) {
    if (infoPanelTitle) {
        infoPanelTitle.innerHTML = `
            <span style="color: var(--text-color-secondary);">📊</span>
            <span style="display:inline-block; margin-right:5px; font-weight: bold;">${userName} 님의</span> AI 추천 직업
        `;
    }

    const recListContainer = recommendationPanel.querySelector('.recommendation-list');
    if (!recListContainer) return;

    const recs = (data && data.recommendations) ? data.recommendations : [];

    let recListHtml = "";
    let drawnCards = 0;

    if (recs.length > 0) {
        recs.forEach((rec, index) => {
            const companyName = rec.company || '관련 회사 정보가 없습니다.';
            const jobLink = (rec.link || '').split(',')[0];
            recListHtml += `
                <div class="recommendation-item" data-id="${index + 1}">
                    <div class="job-header">
                        <div class="job-title">${rec.job || `추천 직업 ${index + 1}`}</div>
                    </div>
                    <div class="button-container">
                        <button class="toggle-text-btn company-btn" data-target="company" data-state="reason">회사 보기</button>
                        <button class="toggle-text-btn competition-btn" data-target="competition" data-state="reason">경쟁률 보기</button>
                        <button class="toggle-text-btn outlook-btn" data-target="outlook" data-state="reason">전망 보기</button>
                    </div>
                    <div class="text-area">
                        <div class="reason-label">추천 사유</div>
                        <div class="text-content reason-text current">${rec.reason || '추천 사유가 없습니다.'}</div>
                        <div class="text-content company-text hidden">
                            <span class="company-name">${companyName}</span>
                            ${jobLink ? `<a class="company-map-link" href="${jobLink}" target="_blank" rel="noopener" title="JobKorea 공고로 이동">🔗 공고</a>` : ''}
                        </div>
                        <div class="text-content outlook-text hidden">${rec.outlook || '직업 전망 정보가 없습니다.'}</div>
                        <div class="text-content competition-text hidden">${rec.competition || '경쟁률 정보가 없습니다.'}</div>
                    </div>
                </div>
            `;
            drawnCards++;
        });
    }

    // 💡 수정된 부분
    if (drawnCards < 3) {
        for (let i = drawnCards; i < 3; i++) {
            recListHtml += `
                <div class="recommendation-item" data-id="${i + 1}">
                    <div class="job-header">
                        <div class="job-title">추천 직업 ${i + 1}</div>
                    </div>
                    <div class="text-area">
                        <div class="reason-label">추천 사유</div>
                        <div class="text-content reason-text current">대화를 통해 추천됩니다.</div>
                    </div>
                </div>
            `;
        }
    }

    recListContainer.innerHTML = recListHtml;

    recListContainer.querySelectorAll('.toggle-text-btn').forEach(button => {
        button.addEventListener('click', (e) => toggleTextContent(e.currentTarget));
    });
}

        function toggleTextContent(button) {
            const item = button.closest('.recommendation-item');
            if (!item) return;

            const target = button.getAttribute('data-target');
            const currentState = button.getAttribute('data-state');
            const textArea = item.querySelector('.text-area');
            const reasonLabel = textArea.querySelector('.reason-label');
            const textMap = {
                'reason': { element: textArea.querySelector('.reason-text'), label: '추천 사유' },
                'outlook': { element: textArea.querySelector('.outlook-text'), label: '직업 전망' },
                'competition': { element: textArea.querySelector('.competition-text'), label: '직업 경쟁률' },
                'company': { element: textArea.querySelector('.company-text'), label: '관련 회사 정보' }
            };

            Object.values(textMap).forEach(info => {
                if (info.element) {
                    info.element.classList.remove('current');
                    info.element.classList.add('hidden');
                }
            });

            const allButtons = item.querySelectorAll('.toggle-text-btn');
            allButtons.forEach(btn => {
                btn.setAttribute('data-state', 'reason');
                const btnTarget = btn.getAttribute('data-target');
                if (btnTarget === 'outlook') btn.textContent = '전망 보기';
                else if (btnTarget === 'competition') btn.textContent = '경쟁률 보기';
                else if (btnTarget === 'company') btn.textContent = '회사 보기';
            });

            let newState = (currentState === target) ? 'reason' : target;

            reasonLabel.textContent = textMap[newState].label;
            if(textMap[newState].element) {
                textMap[newState].element.classList.remove('hidden');
                textMap[newState].element.classList.add('current');
            }

            if (newState !== 'reason') {
                button.setAttribute('data-state', newState);
                button.textContent = '사유 보기';
            }
        }

        function toggleInfoPanel() {
            if (isRecommendationMode) {
                recommendationPanel.classList.remove('visible');
                recommendationPanel.classList.add('hidden');
                analysisPanel.classList.remove('hidden');
                analysisPanel.classList.add('visible');
                infoToggleBtn.textContent = "⬅️ 추천 직업 보기";
                infoToggleBtn.classList.add('analysis-mode-btn');
                // 💡 [수정] (가상) 텍스트 제거
                infoPanelTitle.innerHTML = `<span style="color: var(--bg-color-header-chat);">📊</span> ${userName} 님 분석 상세`;
            } else {
                analysisPanel.classList.remove('visible');
                analysisPanel.classList.add('hidden');
                recommendationPanel.classList.remove('hidden');
                recommendationPanel.classList.add('visible');
                infoToggleBtn.textContent = "📊 분석 정보 보기";
                infoToggleBtn.classList.remove('analysis-mode-btn');
                infoPanelTitle.innerHTML = `
                    <span style="color: var(--text-color-secondary);">📊</span>
                    <span style="display:inline-block; margin-right:5px; font-weight: bold;">${userName} 님의</span> AI 추천 직업
                `;
            }
            isRecommendationMode = !isRecommendationMode;
        }

        // --- 5. 회원정보/대화 세션 관리 함수 (원본 유지) ---
        function openEditProfileModal() {
            modalUserId.value = userId;
            modalUserName.value = userName;
            modalNewPassword.value = '';
            // modalProfileInput.value = ''; // 💡 [삭제] 파일 입력 초기화 로직 제거
            updateStatusMessage.textContent = '';
            updateStatusMessage.style.color = 'green';
            editProfileModal.style.display = 'block';
        }

        function closeEditProfileModal() {
            editProfileModal.style.display = 'none';
        }

        async function handleUpdateProfile() {
            const newPassword = modalNewPassword.value;
            const newName = modalUserName.value.trim();
            // const profileFile = modalProfileInput.files[0]; // 💡 [삭제] 파일 가져오기 로직 제거

            if (!newName) {
                updateStatusMessage.textContent = '이름은 필수로 입력해야 합니다.';
                updateStatusMessage.style.color = 'red';
                return;
            }

            updateStatusMessage.textContent = '정보 수정 중...';
            updateStatusMessage.style.color = 'blue';

            // 💡 [삭제] 파일 Base64 변환 로직 제거
            // let base64Image = null;
            // try { ... }

            try {
                const response = await fetch("/api/update_profile", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        new_password: newPassword || null,
                        new_name: newName,
                        // new_profile_image: base64Image // 💡 [삭제] Base64 이미지 데이터 전송 제거
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || '정보 수정 실패');
                }

                // const responseData = await response.json(); 💡 [삭제] 서버 응답 처리 (profile_src 제거)

                localStorage.setItem("user_name", newName);

                // 💡 [수정] 업데이트된 이름으로 UI 업데이트 (프로필 경로 인자 제거)
                updateUserUI(newName);

                updateStatusMessage.textContent = '회원 정보가 성공적으로 수정되었습니다!';
                updateStatusMessage.style.color = 'green';

                setTimeout(closeEditProfileModal, 1500);

            } catch (error) {
                console.error("회원 정보 수정 오류:", error);
                updateStatusMessage.textContent = error.message;
                updateStatusMessage.style.color = 'red';
            }
        }

        // ===================================================================
        // 💡 [JS 수정] loadChatList 함수 (이전 수정분 유지)
        // ===================================================================
        // 기존: div.textContent = chat.title
        // 수정: <span>(제목)</span><button>(삭제)</button> 구조로 변경
        //       제목과 삭제 버튼에 별도 이벤트 리스너 연결

        function loadChatList() {
            if (!chatList) return;
            chatList.innerHTML = "";

            // 💡 [수정] 최신 대화가 위로 오도록 역순으로 순회 (선택 사항)
            // chats.forEach((chat, index) => {
            [...chats].reverse().forEach((chat, reversedIndex) => {

                // 💡 [수정] 원래 배열의 인덱스를 계산
                const index = chats.length - 1 - reversedIndex;
                const chatData = chats[index];

                const div = document.createElement("div");
                div.classList.add("chat-item");
                if (index === currentChatIndex) div.classList.add("active");

                // 1. 제목 Span 생성
                const titleSpan = document.createElement("span");
                titleSpan.classList.add("chat-item-title");
                titleSpan.textContent = chatData.title;

                // 2. 삭제 Button 생성
                const deleteBtn = document.createElement("button");
                deleteBtn.classList.add("chat-delete-btn");
                deleteBtn.innerHTML = "🗑️"; // 휴지통 아이콘
                deleteBtn.setAttribute("title", "대화 삭제");

                // 3. 제목(titleSpan) 클릭 이벤트 (기존 div.addEventListener)
                titleSpan.addEventListener("click", () => {
                    currentChatIndex = index;
                    conversationHistory = chatData.history;
                    currentConversationId = chatData.conversationId;

                    const loadedRecs = chatData.recommendations || [];
                    const loadedKeywords = chatData.keywords || [];

                    loadChatList(); // 목록 새로고침 (활성 아이템 변경)
                    renderChat(conversationHistory); // 채팅창 내용 로드

                    updateInfoPanel({ recommendations: loadedRecs });

                    try {
                        updateAnalysisPanel(loadedKeywords, loadedRecs);
                    } catch (e) {
                        console.error("그래프 로딩 중 오류 발생:", e);
                    }
                });

                // 4. 제목(titleSpan) 더블 클릭 이벤트 (이름 바꾸기)
                titleSpan.addEventListener("dblclick", () => {
                    const newTitle = prompt("새로운 대화 제목을 입력하세요:", chatData.title);
                    if (newTitle && newTitle.trim() !== "") {
                        chats[index].title = newTitle.trim();
                        saveChats();
                        loadChatList();
                    }
                });

                // 5. 삭제(deleteBtn) 클릭 이벤트
                deleteBtn.addEventListener("click", (e) => {
                    e.stopPropagation(); // 💡 중요: titleSpan의 클릭 이벤트가 실행되지 않도록 함

                    // 사용자에게 확인 받기
                    if (confirm("'" + chatData.title + "' 대화를 정말 삭제하시겠습니까?")) {
                        deleteChat(index);
                    }
                });

                // 6. div에 자식 요소들 추가
                div.appendChild(titleSpan);
                div.appendChild(deleteBtn);
                chatList.appendChild(div);
            });
        }

        // ===================================================================
        // 💡 [JS 신규] deleteChat 함수 (이전 수정분 유지)
        // ===================================================================
        function deleteChat(index) {
            try {
                // 1. 배열에서 해당 인덱스 제거
                chats.splice(index, 1);

                // 2. LocalStorage에 저장
                saveChats();

                // 3. UI 갱신
                if (index === currentChatIndex) {
                    // 💡 현재 활성화된 채팅을 삭제한 경우
                    if (chats.length > 0) {
                        // 💡 다른 채팅이 남아있다면, 이전 채팅 또는 0번 채팅을 활성화
                        currentChatIndex = Math.max(0, index - 1);

                        const newActiveChat = chats[currentChatIndex];
                        conversationHistory = newActiveChat.history;
                        currentConversationId = newActiveChat.conversationId;

                        renderChat(conversationHistory);
                        updateInfoPanel({ recommendations: newActiveChat.recommendations || [] });
                        updateAnalysisPanel(newActiveChat.keywords || [], newActiveChat.recommendations || []);

                    } else {
                        // 💡 모든 채팅이 삭제된 경우, 새 채팅 시작
                        newChat();
                        return; // newChat()가 loadChatList()를 호출하므로 여기서 종료
                    }

                } else if (index < currentChatIndex) {
                    // 💡 현재 활성화된 채팅보다 '이전' 채팅을 삭제한 경우
                    // 활성 인덱스를 하나 줄여야 함
                    currentChatIndex--;
                }

                // 4. 채팅 목록 새로고침
                loadChatList();

            } catch (error) {
                console.error("대화 삭제 중 오류:", error);
                alert("대화를 삭제하는 중 오류가 발생했습니다.");
            }
        }


        function renderChat(history) {
            if (!chatBody) return;
            chatBody.innerHTML = "";
            if (!history || history.length === 0) {
                addAIMessage("안녕하세요! 저는 진로 상담사 AI예요. 궁금한 걸 편하게 물어봐요!", false);
                return;
            }
            history.forEach(msg => {
                if (msg.role === "student") {
                    addUserMessage(msg.content, false);
                } else if (msg.role === "counselor" || msg.role === "assistant") {
                    addAIMessage(msg.content, false);
                }
            });
        }

        function newChat() {
            if (!userId) {
                alert("로그인이 필요합니다.");
                return;
            }
            currentConversationId = 'conv_' + Date.now().toString() + '_' + userId;
            conversationHistory = [];

            const newChatEntry = {
                title: "새 대화",
                history: [],
                conversationId: currentConversationId,
                recommendations: [],
                keywords: []
            };

            // 💡 [수정] 새 대화를 배열의 맨 앞에 추가 (최신순)
            chats.push(newChatEntry);
            currentChatIndex = chats.length - 1; // 💡 새 대화가 마지막 인덱스가 됨

            saveChats();
            loadChatList(); // 💡 목록 새로고침 (새 대화가 맨 위에 표시됨)
            renderChat([]); // 💡 채팅창 비우기

            updateInfoPanel({ recommendations: [] });
            try {
                updateAnalysisPanel([], []);
            } catch(e) {
                console.error("새 대화 그래프 초기화 오류:", e);
            }
            updateUserUI(userName);
        }

        function logout() {
            localStorage.removeItem("user_id");
            localStorage.removeItem("user_name");
            localStorage.removeItem(`chats_${userId}`);
            // 💡 [삭제] 프로필 이미지 소스도 초기화 로직 제거
            // localStorage.removeItem("user_profile_src");
            // 💡 [수정] 커스텀 색상 설정도 로그아웃 시 초기화 (텍스트 키 이름 수정)
            localStorage.removeItem("custom_bg_color");
            localStorage.removeItem("custom_text_color");
            window.location.href = "/login.html";
        }

        function saveChats() {
            if (userId) {
                localStorage.setItem(`chats_${userId}`, JSON.stringify(chats));
            }
        }

        // --- 6. 채팅 메시지 UI 추가 함수 (원본 유지) ---
        function addUserMessage(text, scroll = true) {
            const messageRow = document.createElement("div");
            messageRow.classList.add("message-row", "user");
            messageRow.innerHTML = `
                <div class="name-label user-name">${userName}</div>
                <div class="message-content">
                    <div class="message">${text}</div>
                    <img class="profile user-img" src="${userProfileSrc}" alt="${userName} 프로필" />
                </div>
            `;
            chatBody.appendChild(messageRow);
            if (scroll) chatBody.scrollTop = chatBody.scrollHeight;
        }

        function addAIMessage(text, scroll = true) {
            const messageRow = document.createElement("div");
            messageRow.classList.add("message-row", "ai");
            messageRow.innerHTML = `
                <div class="name-label">AI 상담사</div>
                <div class="message-content">
                    <img class="profile" src="/static/png/bot-profile.png" alt="AI 프로필" />
                    <div class="message">${text}</div>
                </div>
            `;
            chatBody.appendChild(messageRow);
            if (scroll) chatBody.scrollTop = chatBody.scrollHeight;
        }


        // --- 7. window.onload 로직 수정: 커스텀 색상 로드 및 적용 추가 ---
        window.onload = function() {
            try {

                const savedBgColor = localStorage.getItem('custom_bg_color');
                const savedTextColor = localStorage.getItem('custom_text_color');
                // const savedProfileSrc = localStorage.getItem('user_profile_src'); // 💡 [삭제] 저장된 프로필 이미지 경로 로드 제거
                const root = document.documentElement;

                document.body.classList.remove('dark-mode');

                if (savedBgColor) {
                    root.style.setProperty('--custom-bg-color', savedBgColor);
                    if (bgColorInput) {
                        bgColorInput.value = savedBgColor;
                        bgColorPicker.value = savedBgColor;
                    }
                    if (savedBgColor === '#1a1a2e') {
                         document.body.classList.add('dark-mode');
                    }
                }

                if (savedTextColor) {
                    root.style.setProperty('--custom-text-color', savedTextColor);
                    if (textColorInput) {
                        textColorInput.value = savedTextColor;
                        textColorPicker.value = savedTextColor;
                    }
                }

                if (!savedBgColor && localStorage.getItem('theme') === 'dark') {
                     // ...
                }

                userId = localStorage.getItem('user_id');
                userName = localStorage.getItem('user_name') || '학생';
                // 💡 [수정] 로드된 프로필 경로 로직 제거. userProfileSrc는 전역 상수로 고정됨.

                if (!userId) {
                    alert("로그인이 필요합니다.");
                    window.location.href = "/login.html";
                    return;
                }

                updateUserUI(userName); // 💡 [수정] 프로필 경로 인자 제거

                chats = JSON.parse(localStorage.getItem(`chats_${userId}`) || "[]");

                // 💡 [수정] 앱 로드 시 가장 최신 대화(마지막 인덱스)를 선택
                currentChatIndex = chats.length ? chats.length - 1 : -1;

                if (currentChatIndex >= 0) {
                    currentConversationId = chats[currentChatIndex].conversationId;
                    conversationHistory = chats[currentChatIndex].history;
                    renderChat(conversationHistory);

                    const loadedRecs = chats[currentChatIndex].recommendations || [];
                    const loadedKeywords = chats[currentChatIndex].keywords || [];

                    updateInfoPanel({ recommendations: loadedRecs });

                    try {
                        updateAnalysisPanel(loadedKeywords, loadedRecs);
                    } catch (e) {
                        console.error("그래프 로딩 중 오류 발생:", e);
                    }

                } else {
                    newChat(); // 💡 채팅이 하나도 없으면 새 채팅 시작
                }

                recommendationPanel.classList.add('visible');
                analysisPanel.classList.add('hidden');
                infoToggleBtn.classList.remove('analysis-mode-btn');

                loadChatList(); // 💡 목록 로드

            } catch (error) {
                console.error("초기화 중 치명적 오류:", error);
                alert("페이지 로딩 중 오류가 발생했습니다. (window.onload) \n\n" + error.message);
            }

            addEventListeners();
        }

