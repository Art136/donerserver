from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from pathlib import Path
import datetime
import random
import re
import tempfile

import markdown
from lzstring import LZString
from excalidraw_render.render import load_scene, render_svg

import fun
import store

app = Flask(__name__)

CONTENT_DIR = Path(__file__).parent / "content"
BASE_DIR = Path(__file__).parent


def find_content_file(filename):
    matches = list(CONTENT_DIR.rglob(filename))

    if matches:
        return matches[0]

    matches = list(CONTENT_DIR.rglob(filename + ".md"))
    return matches[0] if matches else None


def find_photos_dir():
    matches = [
        path for path in CONTENT_DIR.rglob("photos")
        if path.is_dir()
    ]

    return matches[0] if matches else None


def render_excalidraw(file_path):
    text = file_path.read_text(encoding="utf-8")

    match = re.search(
        r"```compressed-json\s*(.*?)\s*```",
        text,
        re.DOTALL
    )

    if not match:
        raise ValueError("No compressed-json block found")

    compressed_data = match.group(1).replace("\n", "").replace("\r", "")

    json_text = LZString().decompressFromBase64(compressed_data)

    if not json_text:
        raise ValueError("LZString decompression returned nothing")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".excalidraw",
        encoding="utf-8",
        delete=False
    ) as temp:
        temp.write(json_text)
        temp_path = temp.name

    try:
        scene = load_scene(temp_path)
        return render_svg(scene)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def process_excalidraw(text):
    pattern = r'!\[\[([^\]]+\.excalidraw)\]\]'

    def replace(match):
        filename = match.group(1)
        file_path = find_content_file(filename)

        if file_path is None:
            return match.group(0)

        try:
            svg = render_excalidraw(file_path)
            return f'<div class="excalidraw-container">{svg}</div>'

        except Exception as e:
            print(f"Excalidraw error for {file_path}: {e}")
            return f'<p>Excalidraw error: {e}</p>'

    return re.sub(pattern, replace, text)


# ---------- всякие мелкие помощники ----------


def all_notes():
    """Все markdown-заметки в content/, отсортированные по пути."""
    return sorted(p for p in CONTENT_DIR.rglob("*.md") if p.is_file())


def project_lines():
    """Сколько строк кода мы уже наворотили (для спагетти-метра)."""
    files = [Path(__file__), BASE_DIR / "fun.py", BASE_DIR / "store.py"]
    files += list((BASE_DIR / "templates").glob("*.html"))
    files += list((BASE_DIR / "static").rglob("*.css"))
    files += list((BASE_DIR / "static").rglob("*.js"))

    total = 0

    for path in files:
        try:
            total += len(path.read_text(encoding="utf-8").splitlines())
        except OSError:
            pass

    return total


def excuse_of_the_day():
    seed = datetime.date.today().toordinal()
    return random.Random(seed).choice(fun.EXCUSES)


def basename(path):
    return path.replace("\\", "/")


# ---------- основные страницы ----------


@app.route("/")
def index():
    lines = project_lines()

    return render_template(
        "index.html",
        notes_count=len(all_notes()),
        lines=lines,
        vibe=min(99, lines // 30),
        excuse=excuse_of_the_day(),
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/random")
def random_note():
    notes = all_notes()

    if not notes:
        return redirect(url_for("Browse"))

    note = random.choice(notes)
    return redirect(url_for(
        "Browse",
        filepath=basename(str(note.relative_to(CONTENT_DIR)))
    ))


@app.route("/Browse/", methods=["GET", "POST"])
@app.route("/Browse/<path:filepath>", methods=["GET", "POST"])
def Browse(filepath=""):
    current_path = (CONTENT_DIR / filepath).resolve()

    if CONTENT_DIR not in current_path.parents and current_path != CONTENT_DIR:
        abort(404)

    if any(
        part.startswith(".")
        for part in current_path.relative_to(CONTENT_DIR).parts
    ):
        abort(404)

    # Прилепить стикер к заметке
    if request.method == "POST":
        if not current_path.is_file() or current_path.suffix.lower() != ".md":
            abort(404)

        if not current_path.name.endswith(".excalidraw.md"):
            text = (request.form.get("text") or "").strip()[:300]
            name = (request.form.get("name") or "").strip()[:40] or "аноним"

            if text:
                store.add(
                    "stickers",
                    {
                        "path": filepath.replace("\\", "/"),
                        "name": name,
                        "text": text,
                        "color": random.choice(fun.STICKER_COLORS),
                        "angle": random.choice(fun.STICKER_ANGLES),
                        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    },
                    limit=500,
                )

        return redirect(url_for("Browse", filepath=filepath))

    # Normal Markdown note
    if current_path.is_file():

        # Excalidraw files should be rendered by the Excalidraw renderer
        if current_path.name.endswith(".excalidraw.md"):
            svg = render_excalidraw(current_path)
            title = current_path.name.removesuffix(".excalidraw.md")

            return render_template(
                "directview.html",
                content=svg,
                title=title
            )

        # Regular Markdown
        if current_path.suffix.lower() != ".md":
            abort(404)

        markdown_text = current_path.read_text(encoding="utf-8")
        markdown_text = process_excalidraw(markdown_text)

        html = markdown.markdown(
            markdown_text,
            extensions=[
                "fenced_code",
                "tables",
                "toc"
            ]
        )

        key = basename(filepath)

        return render_template(
            "note.html",
            content=html,
            filepath=filepath,
            title=current_path.stem,
            stickers=[
                sticker
                for sticker in store.load("stickers")
                if sticker.get("path") == key
            ],
        )

    # Directory
    if current_path.is_dir():
        items = []

        for item in sorted(current_path.iterdir()):
            if item.name.startswith("."):
                continue

            if item.is_dir():
                items.append({
                    "name": item.name,
                    "type": "folder"
                })

            elif item.is_file():
                if item.name.endswith(".excalidraw.md"):
                    items.append({
                        "name": item.name.removesuffix(".md"),
                        "type": "file"
                    })

                elif item.suffix.lower() == ".md":
                    items.append({
                        "name": item.stem,
                        "type": "file"
                    })

        return render_template(
            "browse.html",
            items=items,
            current_path=filepath,
            has_notes=bool(all_notes()),
        )

    abort(404)


# ---------- гостевая книга ----------


@app.route("/guestbook", methods=["GET", "POST"])
def guestbook():
    if request.method == "POST":
        text = (request.form.get("text") or "").strip()[:300]
        name = (request.form.get("name") or "").strip()[:40] or "аноним"
        mood = request.form.get("mood") or "😎"

        if mood not in fun.GUESTBOOK_MOODS:
            mood = "😎"

        if text:
            store.add(
                "guestbook",
                {
                    "name": name,
                    "text": text,
                    "mood": mood,
                    "color": random.choice(fun.STICKER_COLORS),
                    "angle": random.choice(fun.STICKER_ANGLES),
                    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                },
                limit=300,
            )

        return redirect(url_for("guestbook"))

    entries = list(reversed(store.load("guestbook")))

    return render_template(
        "guestbook.html",
        entries=entries,
        moods=fun.GUESTBOOK_MOODS,
    )


# ---------- донерка ----------


@app.route("/doner")
def doner():
    orders = store.load("doners")

    return render_template(
        "doner.html",
        menu=fun.DONER_MENU,
        orders=list(reversed(orders[-8:])),
        total_orders=len(orders),
    )


@app.route("/api/doner", methods=["POST"])
def api_doner():
    payload = request.get_json(silent=True) or {}
    selected = payload.get("items") or {}

    if not isinstance(selected, dict):
        return jsonify(ok=False, error="Непонятный заказ"), 400

    menu = {item["id"]: item for item in fun.DONER_MENU}
    lines = []

    for item_id, quantity in selected.items():
        item = menu.get(item_id)

        if item is None:
            continue

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        quantity = max(0, min(quantity, 20))

        if quantity:
            lines.append({
                "id": item_id,
                "name": item["name"],
                "price": item["price"],
                "qty": quantity,
            })

    if not lines:
        return jsonify(ok=False, error="Ты ничего не выбрал, а кушать хочется"), 400

    total = sum(line["price"] * line["qty"] for line in lines)
    orders = store.load("doners")
    number = max((order.get("number", 0) for order in orders), default=0) + 1
    status = random.choice(fun.DONER_STATUSES)
    wait = random.randint(5, 25)

    order = {
        "number": number,
        "lines": lines,
        "summary": ", ".join(
            f'{line["name"]} ×{line["qty"]}' for line in lines
        ),
        "total": total,
        "status": status,
        "wait": wait,
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    }

    store.add("doners", order, limit=300)

    return jsonify(
        ok=True,
        number=number,
        total=total,
        status=status,
        wait=wait,
        summary=order["summary"],
    )


# ---------- паника ----------


@app.route("/panic")
def panic():
    return render_template(
        "panic.html",
        session_date=fun.SESSION_DATE,
        phrases=fun.PANIC_PHRASES,
    )


# ---------- мелочи ----------


@app.route("/health")
def health():
    return jsonify(ok=True, notes=len(all_notes()))


# ---------- 404 ----------


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "404.html",
        phrase=random.choice(fun.NOT_FOUND_PHRASES),
    ), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
