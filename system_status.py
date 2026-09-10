import os
import time
import sqlite3
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

START_TIME = time.time()


def format_bytes(value):
    value = float(value)

    if value < 1024:
        return f"{value:.0f} B"

    if value < 1024 ** 2:
        return f"{value / 1024:.1f} KB"

    if value < 1024 ** 3:
        return f"{value / (1024 ** 2):.1f} MB"

    return f"{value / (1024 ** 3):.2f} GB"


def format_uptime(seconds):
    seconds = int(seconds)

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []

    if days:
        parts.append(f"{days}d")

    if hours:
        parts.append(f"{hours}h")

    if minutes:
        parts.append(f"{minutes}m")

    parts.append(f"{seconds}s")

    return " ".join(parts)


def get_process_memory():

    try:
        import resource

        usage = resource.getrusage(
            resource.RUSAGE_SELF
        )

        # Linux reports KB
        memory_kb = usage.ru_maxrss

        return memory_kb * 1024

    except Exception:
        return 0


def get_cpu_usage():

    try:
        import psutil

        return psutil.cpu_percent(
            interval=0.15
        )

    except Exception:
        return None


def get_system_memory():

    try:
        import psutil

        memory = psutil.virtual_memory()

        return {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percent": memory.percent,
        }

    except Exception:

        return {
            "total": 0,
            "used": 0,
            "available": 0,
            "percent": 0,
        }


def get_disk_usage():

    try:

        import shutil

        total, used, free = (
            shutil.disk_usage("/")
        )

        percent = (
            (used / total) * 100
            if total
            else 0
        )

        return {
            "total": total,
            "used": used,
            "free": free,
            "percent": percent,
        }

    except Exception:

        return {
            "total": 0,
            "used": 0,
            "free": 0,
            "percent": 0,
        }


def get_database_stats():

    db_path = "data/database.db"

    possible_paths = [
        "data/database.db",
        "data/nexus.db",
        "database.db",
        "nexus.db",
    ]

    for path in possible_paths:

        if os.path.exists(path):

            db_path = path
            break

    stats = {
        "users": 0,
        "groups": 0,
        "cards": 0,
        "db_size": 0,
    }

    if not os.path.exists(db_path):
        return stats

    try:

        stats["db_size"] = os.path.getsize(
            db_path
        )

        connection = sqlite3.connect(
            db_path
        )

        cursor = connection.cursor()

        for key, table in (
            ("users", "users"),
            ("groups", "groups"),
            ("cards", "cards"),
        ):

            try:

                cursor.execute(
                    f"SELECT COUNT(*) FROM {table}"
                )

                result = cursor.fetchone()

                if result:
                    stats[key] = int(
                        result[0]
                    )

            except Exception:
                pass

        connection.close()

    except Exception as e:

        logger.warning(
            "Database stats error: %s",
            e,
        )

    return stats


def get_bot_latency(
    update,
):

    try:

        if not update.effective_message:
            return 0

        message_time = (
            update.effective_message.date
        )

        now = time.time()

        timestamp = (
            message_time.timestamp()
        )

        return max(
            0,
            int(
                (now - timestamp)
                * 1000
            ),
        )

    except Exception:

        return 0


def get_bot_status():

    uptime = (
        time.time()
        - START_TIME
    )

    cpu = get_cpu_usage()

    memory = get_system_memory()

    disk = get_disk_usage()

    database = get_database_stats()

    process_memory = (
        get_process_memory()
    )

    return {
        "uptime": format_uptime(
            uptime
        ),

        "cpu": cpu,

        "ram_total": memory[
            "total"
        ],

        "ram_used": memory[
            "used"
        ],

        "ram_available": memory[
            "available"
        ],

        "ram_percent": memory[
            "percent"
        ],

        "process_memory": process_memory,

        "disk_total": disk[
            "total"
        ],

        "disk_used": disk[
            "used"
        ],

        "disk_free": disk[
            "free"
        ],

        "disk_percent": disk[
            "percent"
        ],

        "users": database[
            "users"
        ],

        "groups": database[
            "groups"
        ],

        "cards": database[
            "cards"
        ],

        "db_size": database[
            "db_size"
        ],
    }


async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    # --------------------------------------------------------
    # OWNER ONLY
    # --------------------------------------------------------

    try:

        from config import OWNER_ID

        owner_id = int(
            OWNER_ID
        )

        if (
            update.effective_user
            and update.effective_user.id
            != owner_id
        ):

            await message.reply_text(
                "⛔ <b>OWNER ONLY</b>\n\n"
                "ဒီ Command ကို Bot Owner "
                "ပဲ အသုံးပြုနိုင်ပါတယ်။",
                parse_mode="HTML",
            )

            return

    except Exception:

        pass

    # --------------------------------------------------------
    # MEASURE RESPONSE
    # --------------------------------------------------------

    start = time.perf_counter()

    status = get_bot_status()

    latency = int(
        (
            time.perf_counter()
            - start
        )
        * 1000
    )

    cpu = status["cpu"]

    if cpu is None:
        cpu_text = "N/A"
    else:
        cpu_text = f"{cpu:.1f}%"

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    text = (
        "╔══════════════════════════╗\n"
        "       🖥️ <b>NEXUS SYSTEM</b>\n"
        "╚══════════════════════════╝\n\n"

        "🟢 <b>BOT STATUS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 Status       : <b>ONLINE</b>\n"
        f"⚡ Response     : <b>{latency} ms</b>\n"
        f"⏱️ Uptime       : <b>{status['uptime']}</b>\n\n"

        "🧠 <b>CPU</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⚙️ CPU Usage    : <b>{cpu_text}</b>\n\n"

        "💾 <b>RAM</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 RAM Usage    : "
        f"<b>{status['ram_percent']:.1f}%</b>\n"
        f"🔹 Used         : "
        f"<b>{format_bytes(status['ram_used'])}</b>\n"
        f"🔹 Available    : "
        f"<b>{format_bytes(status['ram_available'])}</b>\n"
        f"🔹 Total        : "
        f"<b>{format_bytes(status['ram_total'])}</b>\n"
        f"🤖 Bot Process   : "
        f"<b>{format_bytes(status['process_memory'])}</b>\n\n"

        "💿 <b>DISK</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Used         : "
        f"<b>{format_bytes(status['disk_used'])}</b>\n"
        f"🆓 Free         : "
        f"<b>{format_bytes(status['disk_free'])}</b>\n"
        f"💽 Total        : "
        f"<b>{format_bytes(status['disk_total'])}</b>\n"
        f"📊 Usage        : "
        f"<b>{status['disk_percent']:.1f}%</b>\n\n"

        "🗄️ <b>DATABASE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Users        : "
        f"<b>{status['users']:,}</b>\n"
        f"👥 Groups       : "
        f"<b>{status['groups']:,}</b>\n"
        f"🎴 Cards        : "
        f"<b>{status['cards']:,}</b>\n"
        f"📁 DB Size      : "
        f"<b>{format_bytes(status['db_size'])}</b>\n\n"

        "╔══════════════════════════╗\n"
        "      ⚡ <b>NEXUS V5 MONITOR</b>\n"
        "╚══════════════════════════╝"
    )

    await message.reply_text(
        text,
        parse_mode="HTML",
    )
