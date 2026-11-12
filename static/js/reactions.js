/* Like and favorite buttons on news and law articles, saved to the server. */
(function () {
    "use strict";

    var box = document.querySelector(".reactions");
    if (!box) return;

    var LABELS = {
        like: { on: "已赞", off: "点赞" },
        favorite: { on: "已收藏", off: "收藏" }
    };
    var hint = document.getElementById("reaction-hint");

    function showHint(html) {
        hint.innerHTML = html;
        hint.hidden = false;
    }

    function setState(kind, on) {
        var btn = box.querySelector('[data-kind="' + kind + '"]');
        btn.classList.toggle("is-on", on);
        btn.setAttribute("aria-pressed", String(on));
        btn.querySelector(".reaction-label").textContent = LABELS[kind][on ? "on" : "off"];
    }

    box.addEventListener("click", function (event) {
        var btn = event.target.closest(".reaction-btn");
        if (!btn || btn.disabled) return;
        var kind = btn.dataset.kind;
        btn.disabled = true;
        fetch(box.dataset[kind + "Url"], {
            method: "POST",
            headers: { "X-CSRFToken": box.dataset.csrf },
            credentials: "same-origin"
        })
            .then(function (response) {
                if (response.status === 401) {
                    showHint('登录后才能' + LABELS[kind].off + '，<a href="' + box.dataset.loginUrl + '">去登录</a>');
                    return null;
                }
                if (!response.ok) throw new Error(response.status);
                return response.json();
            })
            .then(function (state) {
                if (!state) return;
                hint.hidden = true;
                setState("like", state.liked);
                setState("favorite", state.favorited);
                document.getElementById("like-count").textContent = state.like_count;
                if (kind === "favorite" && state.favorited) {
                    showHint('已加入<a href="/favorite_news/">我的收藏</a>');
                }
            })
            .catch(function () {
                showHint("操作没有成功，请检查网络后再试一次。");
            })
            .finally(function () {
                btn.disabled = false;
            });
    });
})();
