function speakWord(word) {
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = "en-US";
    window.speechSynthesis.speak(utterance);
}

document.addEventListener("DOMContentLoaded", function () {
    const app = document.getElementById("practice-app");
    if (!app) return;

    const sessionId = app.dataset.sessionId;
    const items = document.querySelectorAll(".practice-item");

    items.forEach(function (item) {
        const word = item.dataset.word;
        const wordId = item.dataset.wordId;
        const speakBtn = item.querySelector(".speak-btn");
        const submitBtn = item.querySelector(".submit-btn");
        const answerInput = item.querySelector(".answer-input");
        const resultBox = item.querySelector(".result-box");

        speakBtn.addEventListener("click", function () {
            speakWord(word);
        });

        submitBtn.addEventListener("click", function () {
            const formData = new FormData();
            formData.append("session_id", sessionId);
            formData.append("word_id", wordId);
            formData.append("user_input", answerInput.value);
            formData.append("csrfmiddlewaretoken", getCsrfToken());

            fetch("/practice/submit/", {
                method: "POST",
                body: formData,
            })
                .then(response => response.json())
                .then(data => {
                    if (!data.ok) {
                        resultBox.innerHTML = "<div class='text-danger'>提交失败</div>";
                        return;
                    }

                    if (data.is_correct) {
                        resultBox.innerHTML = "<div class='text-success'>回答正确</div>";
                    } else {
                        resultBox.innerHTML = `
                            <div class='text-danger'>回答错误</div>
                            <div>正确答案：${data.correct_word}</div>
                            <div>中文：${data.meaning_cn || ""}</div>
                            <div>例句：${data.example_sentence || ""}</div>
                        `;
                    }
                });
        });
    });
});

function getCsrfToken() {
    const cookieValue = document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="));
    return cookieValue ? cookieValue.split("=")[1] : "";
}
