/* Донерка: корзина и заказ. */

(function () {
    "use strict";

    var cards = Array.prototype.slice.call(document.querySelectorAll(".doner-card"));
    var list = document.getElementById("cartList");
    var totalField = document.getElementById("cartTotal");
    var orderButton = document.getElementById("orderButton");
    var resultField = document.getElementById("orderResult");

    if (!cards.length || !list || !orderButton) {
        return;
    }

    var cart = {};

    function cardData(card) {
        return {
            id: card.dataset.id,
            name: card.dataset.name,
            price: Number(card.dataset.price)
        };
    }

    function render() {
        list.innerHTML = "";
        var total = 0;
        var hasItems = false;

        cards.forEach(function (card) {
            var data = cardData(card);
            var quantity = cart[data.id] || 0;

            card.querySelector(".doner-qty").textContent = quantity;
            card.classList.toggle("in-cart", quantity > 0);

            if (!quantity) {
                return;
            }

            hasItems = true;
            total += quantity * data.price;

            var row = document.createElement("li");
            row.textContent = data.name + " ×" + quantity + " — " + quantity * data.price + " ₽";
            list.appendChild(row);
        });

        if (!hasItems) {
            var empty = document.createElement("li");
            empty.className = "empty-cart";
            empty.textContent = "Пока пусто. Как в жизни.";
            list.appendChild(empty);
        }

        totalField.textContent = total;
    }

    cards.forEach(function (card) {
        card.querySelector(".doner-plus").addEventListener("click", function () {
            var id = card.dataset.id;
            cart[id] = Math.min((cart[id] || 0) + 1, 20);
            render();
        });

        card.querySelector(".doner-minus").addEventListener("click", function () {
            var id = card.dataset.id;
            cart[id] = Math.max((cart[id] || 0) - 1, 0);

            if (!cart[id]) {
                delete cart[id];
            }

            render();
        });
    });

    function addToFeed(data) {
        var feed = document.querySelector(".order-feed");

        if (!feed) {
            return;
        }

        var empty = feed.querySelector(".empty");

        if (empty) {
            empty.remove();
        }

        var row = document.createElement("li");
        var title = document.createElement("b");
        title.textContent = "#" + data.number;
        row.appendChild(title);
        row.appendChild(document.createTextNode(
            " — " + data.summary + " — " + data.total + " ₽"
        ));

        var status = document.createElement("span");
        status.className = "order-status";
        status.textContent = data.status + " (~" + data.wait + " мин)";
        row.appendChild(status);

        feed.insertBefore(row, feed.firstChild);
    }

    orderButton.addEventListener("click", function () {
        if (!Object.keys(cart).length) {
            resultField.textContent = "Сначала выбери хоть что-нибудь, голодный.";
            return;
        }

        orderButton.disabled = true;
        resultField.textContent = "Отправляем заказ...";

        fetch("/api/doner", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ items: cart })
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function (response) {
                if (!response.ok || !response.data.ok) {
                    resultField.textContent =
                        response.data.error || "Что-то сломалось. Как обычно.";
                    return;
                }

                var data = response.data;

                resultField.textContent = "Заказ #" + data.number + " принят. " +
                    data.status + ". Ждать ~" + data.wait + " мин. Итого " +
                    data.total + " ₽.";

                cart = {};
                render();
                addToFeed(data);

                if (window.burgerRain) {
                    window.burgerRain(24);
                }
            })
            .catch(function () {
                resultField.textContent = "Кухня не отвечает. Попробуй ещё раз.";
            })
            .then(function () {
                orderButton.disabled = false;
            });
    });

    render();
}());
