/* Вся мелкая движуха: бургеры с неба, маскот и пасхалки. */

(function () {
    "use strict";

    var reduceMotion = window.matchMedia
        && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var mascot = document.getElementById("mascot");
    var bubble = document.getElementById("mascotBubble");
    var pupils = mascot ? mascot.querySelectorAll(".pupil") : [];
    var mascotCenter = null;
    var sad = false;

    /* ---------- бургерный дождь ---------- */

    var RAIN_ITEMS = ["🍔", "🍔", "🥙", "🍟"];

    function burgerRain(count) {
        if (reduceMotion) {
            return;
        }

        var amount = count || 32;

        for (var i = 0; i < amount; i += 1) {
            var drop = document.createElement("span");
            drop.className = "burger-drop";
            drop.textContent = RAIN_ITEMS[Math.floor(Math.random() * RAIN_ITEMS.length)];
            drop.style.left = (Math.random() * 100) + "vw";
            drop.style.fontSize = (18 + Math.random() * 26) + "px";
            drop.style.animationDuration = (1.8 + Math.random() * 2.4) + "s";
            drop.style.animationDelay = (Math.random() * 0.9) + "s";
            drop.style.setProperty("--spin", (Math.random() * 720 - 360) + "deg");
            drop.addEventListener("animationend", function () {
                this.remove();
            });
            document.body.appendChild(drop);
        }
    }

    /* ---------- код Konami ---------- */

    var KONAMI = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65];
    var progress = 0;

    document.addEventListener("keydown", function (event) {
        if (event.keyCode === KONAMI[progress]) {
            progress += 1;

            if (progress === KONAMI.length) {
                progress = 0;
                burgerRain(60);
                if (bubble) {
                    bubble.textContent = "пасхалка, брат";
                }
            }
        } else {
            progress = 0;
        }
    });

    /* ---------- маскот ---------- */

    function mascotBox() {
        if (!mascot) {
            return null;
        }

        var rect = mascot.getBoundingClientRect();
        mascotCenter = {
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
        };
        return mascotCenter;
    }

    function lookAt(x, y) {
        if (!mascotCenter || sad) {
            return;
        }

        var dx = x - mascotCenter.x;
        var dy = y - mascotCenter.y;
        var distance = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        var shift = Math.min(distance / 60, 2.6);

        for (var i = 0; i < pupils.length; i += 1) {
            pupils[i].setAttribute("transform",
                "translate(" + (dx / distance * shift) + "," + (dy / distance * shift) + ")");
        }
    }

    if (mascot) {
        mascotBox();

        window.addEventListener("resize", mascotBox);
        window.addEventListener("scroll", mascotBox, { passive: true });

        document.addEventListener("mousemove", function (event) {
            lookAt(event.clientX, event.clientY);
        });

        var clicked = 0;
        var phrases = [
            "не трогай, я работаю",
            "донер заказывал?",
            "открой конспект, брат",
            "ещё раз и я расстегнусь",
            "м-м-м, соус",
            "я тут вместо дедлайна"
        ];

        mascot.addEventListener("click", function () {
            clicked += 1;
            bubble.textContent = phrases[Math.floor(Math.random() * phrases.length)];

            if (clicked === 5) {
                clicked = 0;
                burgerRain(14);
                bubble.textContent = "ладно, держи бургеры";
            }
        });
    }

    /* ---------- грусть на пустой папке ---------- */

    if (mascot && document.querySelector(".empty")) {
        sad = true;
        mascot.classList.add("sad");

        for (var i = 0; i < pupils.length; i += 1) {
            pupils[i].setAttribute("transform", "translate(0,2)");
        }

        bubble.textContent = "тут пусто, брат";
    }

    /* Экспортируем наружу, чтобы страницы могли вызвать дождь сами */
    window.burgerRain = burgerRain;
}());
