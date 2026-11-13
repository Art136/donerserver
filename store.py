"""Простое хранилище на JSON-файлах, без БД.

Данных мало, поэтому вместо sqlite — обычные списки в data/*.json.
Запись атомарная (временный файл + замена), плюс блокировка на случай,
если Flask запущен в несколько потоков.
"""

import json
import os
import tempfile
from pathlib import Path
from threading import RLock

DATA_DIR = Path(__file__).parent / "data"
_LOCK = RLock()


def _path(name):
    return DATA_DIR / f"{name}.json"


def load(name, default=None):
    try:
        return json.loads(_path(name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [] if default is None else default


def save(name, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, _path(name))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def add(name, item, limit=None):
    """Дописать элемент в список и вернуть получившийся список."""
    with _LOCK:
        data = load(name)
        data.append(item)

        if limit is not None:
            data = data[-limit:]

        save(name, data)
        return data
