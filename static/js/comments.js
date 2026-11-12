/* Comment form: posts to the server and shows the new comment at the top. */
(function () {
    "use strict";

    var form = document.getElementById("comment-form");
    var trigger = document.getElementById("comment-button");
    if (trigger) {
        trigger.addEventListener("click", function () {
            var target = document.getElementById("comment-body") || document.getElementById("comments");
            target.scrollIntoView({ behavior: "smooth", block: "center" });
            if (target.focus) target.focus({ preventScroll: true });
        });
    }
    if (!form) return;

    var input = document.getElementById("comment-body");
    var chars = document.getElementById("comment-chars");
    var error = document.getElementById("comment-error");
    var list = document.getElementById("comment-list");
    var submit = form.querySelector("button[type=submit]");

    function showError(message) {
        error.textContent = message;
        error.hidden = !message;
    }

    input.addEventListener("input", function () {
        chars.textContent = input.value.length + " / 300";
        showError("");
    });

    function renderComment(comment) {
        var item = document.createElement("li");
        item.className = "cmt-item";
        var meta = document.createElement("div");
        meta.className = "cmt-meta";
        var name = document.createElement("b");
        name.textContent = comment.user;
        var time = document.createElement("time");
        time.textContent = comment.created;
        meta.appendChild(name);
        meta.appendChild(time);
        var body = document.createElement("p");
        comment.body.split("\n").forEach(function (line, i) {
            if (i) body.appendChild(document.createElement("br"));
            body.appendChild(document.createTextNode(line));
        });
        item.appendChild(meta);
        item.appendChild(body);
        return item;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        var text = input.value.trim();
        if (!text) {
            showError("评论内容不能为空。");
            return;
        }
        submit.disabled = true;
        var data = new FormData();
        data.append("body", text);
        fetch(form.dataset.url, {
            method: "POST",
            headers: { "X-CSRFToken": form.dataset.csrf },
            body: data,
            credentials: "same-origin"
        })
            .then(function (response) {
                return response.json().then(function (payload) {
                    return { ok: response.ok, payload: payload };
                });
            })
            .then(function (result) {
                if (!result.ok) {
                    showError(result.payload.error || "评论没有发出去，请稍后再试。");
                    return;
                }
                var empty = document.getElementById("comment-empty");
                if (empty) empty.remove();
                list.insertBefore(renderComment(result.payload.comment), list.firstChild);
                var count = document.getElementById("comment-count");
                if (count) count.textContent = result.payload.comment_count;
                input.value = "";
                chars.textContent = "0 / 300";
                showError("");
            })
            .catch(function () {
                showError("网络有问题，评论没有发出去，请稍后再试。");
            })
            .finally(function () {
                submit.disabled = false;
            });
    });
})();
