/* One question at a time; the server checks each answer and returns the explanation. */
(function () {
    "use strict";

    var box = document.getElementById("quiz");
    if (!box) return;
    var questions = JSON.parse(document.getElementById("quiz-data").textContent);
    var LETTERS = "ABCD";
    var current = 0;
    var resultUrl = null;

    var el = {
        count: document.getElementById("quiz-count"),
        question: document.getElementById("quiz-question"),
        options: document.getElementById("quiz-options"),
        feedback: document.getElementById("quiz-feedback"),
        verdict: document.getElementById("quiz-verdict"),
        explanation: document.getElementById("quiz-explanation"),
        sources: document.getElementById("quiz-sources"),
        error: document.getElementById("quiz-error"),
        next: document.getElementById("quiz-next"),
        bar: box.querySelectorAll(".qz-bar span")
    };

    function show(index) {
        var q = questions[index];
        el.count.textContent = "第 " + (index + 1) + " 题 / 共 " + questions.length + " 题";
        el.question.textContent = q.text;
        el.options.innerHTML = "";
        q.options.forEach(function (text, i) {
            var li = document.createElement("li");
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "qz-opt";
            btn.dataset.choice = i;
            var letter = document.createElement("span");
            letter.className = "qz-letter";
            letter.textContent = LETTERS[i];
            var label = document.createElement("span");
            label.textContent = text;
            btn.appendChild(letter);
            btn.appendChild(label);
            li.appendChild(btn);
            el.options.appendChild(li);
        });
        el.bar[index].classList.add("is-current");
        el.feedback.hidden = true;
        el.next.hidden = true;
        el.error.hidden = true;
    }

    function fail(message) {
        el.error.innerHTML = "";
        el.error.appendChild(document.createTextNode(message + " "));
        var again = document.createElement("a");
        again.href = window.location.pathname;
        again.textContent = "重新开始本关";
        el.error.appendChild(again);
        el.error.hidden = false;
    }

    el.options.addEventListener("click", function (event) {
        var btn = event.target.closest(".qz-opt");
        if (!btn || btn.disabled) return;
        var buttons = el.options.querySelectorAll(".qz-opt");
        buttons.forEach(function (b) { b.disabled = true; });
        var data = new FormData();
        data.append("attempt", box.dataset.attempt);
        data.append("question", current);
        data.append("choice", btn.dataset.choice);
        fetch(box.dataset.answerUrl, {
            method: "POST",
            headers: { "X-CSRFToken": box.dataset.csrf },
            body: data,
            credentials: "same-origin"
        })
            .then(function (response) {
                return response.json().then(function (payload) { return { ok: response.ok, payload: payload }; });
            })
            .then(function (res) {
                if (!res.ok) {
                    fail(res.payload.error || "提交失败。");
                    return;
                }
                var r = res.payload;
                buttons[r.answer].classList.add("is-right");
                if (!r.correct) btn.classList.add("is-wrong");
                el.bar[current].classList.remove("is-current");
                el.bar[current].classList.add(r.correct ? "is-right" : "is-wrong");
                el.verdict.textContent = r.correct ? "回答正确！" : "答错了，正确答案是 " + LETTERS[r.answer] + "。";
                el.verdict.className = "qz-verdict " + (r.correct ? "right" : "wrong");
                el.explanation.textContent = r.explanation;
                el.sources.innerHTML = "";
                if (r.sources.length) {
                    el.sources.appendChild(document.createTextNode("出处："));
                    r.sources.forEach(function (s, i) {
                        if (i) el.sources.appendChild(document.createTextNode("；"));
                        if (s.url) {
                            var a = document.createElement("a");
                            a.href = s.url;
                            a.target = "_blank";
                            a.rel = "noopener";
                            a.textContent = s.name;
                            el.sources.appendChild(a);
                        } else {
                            el.sources.appendChild(document.createTextNode(s.name));
                        }
                    });
                }
                el.sources.hidden = !r.sources.length;
                el.feedback.hidden = false;
                resultUrl = r.finished ? r.result_url : null;
                el.next.textContent = r.finished ? "查看成绩" : "下一题";
                el.next.hidden = false;
                el.next.focus();
            })
            .catch(function () {
                buttons.forEach(function (b) { b.disabled = false; });
                fail("网络有问题，答案没有提交成功。");
            });
    });

    el.next.addEventListener("click", function () {
        if (resultUrl) {
            window.location.href = resultUrl;
            return;
        }
        current += 1;
        show(current);
    });

    show(0);
})();
