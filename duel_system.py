# duel_system.py
# Nexus Catch Bot
# Card Duel / EXP / Level System

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Optional
import random


# ============================================================
# CONFIG
# ============================================================

DUEL_COOLDOWN_SECONDS = 30

BASE_WIN_COINS = 100
BASE_LOSE_COINS = 25

BASE_WIN_EXP = 100
BASE_LOSE_EXP = 20

MAX_LEVEL = 100

# Level EXP formula:
# Required EXP = BASE_EXP * current_level
BASE_EXP_PER_LEVEL = 100

# Random damage safety limits
MIN_DAMAGE = 1

# Speed advantage
SPEED_ADVANTAGE = 1.15


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class CardStats:
    card_id: str

    level: int = 1
    exp: int = 0

    atk: int = 100
    defense: int = 100
    hp: int = 100
    speed: int = 100

    element: str = "Normal"


@dataclass
class DuelResult:
    success: bool
    winner_id: Optional[int] = None
    loser_id: Optional[int] = None

    winner_card_id: Optional[str] = None
    loser_card_id: Optional[str] = None

    winner_coins: int = 0
    loser_coins: int = 0

    winner_exp: int = 0
    loser_exp: int = 0

    rounds: int = 0

    battle_log: list[str] = field(
        default_factory=list
    )

    message: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ============================================================
# STORAGE
# ============================================================

_CARD_STATS: dict[tuple[int, str], CardStats] = {}

_LAST_DUEL: dict[int, datetime] = {}

_DUEL_HISTORY: list[DuelResult] = []

_LOCK = RLock()


# ============================================================
# TIME
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# ID HELPERS
# ============================================================

def normalize_user_id(user_id) -> int:
    try:
        return int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid user ID.")


def normalize_card_id(card_id) -> str:
    if card_id is None:
        raise ValueError("Card ID is required.")

    value = str(card_id).strip()

    if not value:
        raise ValueError("Card ID is required.")

    if value.isdigit():
        return value.zfill(4)

    return value


# ============================================================
# CARD STATS
# ============================================================

def get_card_stats(
    user_id: int,
    card_id: str,
) -> CardStats:

    user_id = normalize_user_id(user_id)
    card_id = normalize_card_id(card_id)

    key = (
        user_id,
        card_id,
    )

    with _LOCK:

        stats = _CARD_STATS.get(key)

        if stats is None:

            stats = CardStats(
                card_id=card_id
            )

            _CARD_STATS[key] = stats

        return stats


def set_card_stats(
    user_id: int,
    card_id: str,
    *,
    level: int = 1,
    exp: int = 0,
    atk: int = 100,
    defense: int = 100,
    hp: int = 100,
    speed: int = 100,
    element: str = "Normal",
) -> CardStats:

    stats = get_card_stats(
        user_id,
        card_id,
    )

    with _LOCK:

        stats.level = max(
            1,
            min(
                int(level),
                MAX_LEVEL,
            ),
        )

        stats.exp = max(
            0,
            int(exp),
        )

        stats.atk = max(
            1,
            int(atk),
        )

        stats.defense = max(
            1,
            int(defense),
        )

        stats.hp = max(
            1,
            int(hp),
        )

        stats.speed = max(
            1,
            int(speed),
        )

        stats.element = str(
            element or "Normal"
        )

    return stats


# ============================================================
# EXP SYSTEM
# ============================================================

def exp_required_for_level(
    level: int,
) -> int:

    level = max(
        1,
        int(level),
    )

    return (
        BASE_EXP_PER_LEVEL
        * level
    )


def get_level_progress(
    user_id: int,
    card_id: str,
) -> tuple[int, int, int]:

    stats = get_card_stats(
        user_id,
        card_id,
    )

    required = exp_required_for_level(
        stats.level
    )

    return (
        stats.level,
        stats.exp,
        required,
    )


def add_card_exp(
    user_id: int,
    card_id: str,
    amount: int,
) -> tuple[CardStats, int]:

    amount = int(amount)

    if amount <= 0:
        return (
            get_card_stats(
                user_id,
                card_id,
            ),
            0,
        )

    stats = get_card_stats(
        user_id,
        card_id,
    )

    levels_gained = 0

    with _LOCK:

        if stats.level >= MAX_LEVEL:

            stats.level = MAX_LEVEL
            stats.exp = 0

            return (
                stats,
                0,
            )

        stats.exp += amount

        while (
            stats.level < MAX_LEVEL
            and stats.exp
            >= exp_required_for_level(
                stats.level
            )
        ):

            required = exp_required_for_level(
                stats.level
            )

            stats.exp -= required
            stats.level += 1

            levels_gained += 1

        if stats.level >= MAX_LEVEL:

            stats.level = MAX_LEVEL
            stats.exp = 0

    return (
        stats,
        levels_gained,
    )


# ============================================================
# UPGRADE
# ============================================================

def upgrade_card(
    user_id: int,
    card_id: str,
) -> tuple[bool, CardStats, str]:

    stats = get_card_stats(
        user_id,
        card_id,
    )

    if stats.level >= MAX_LEVEL:

        return (
            False,
            stats,
            "⭐ Card is already at MAX LEVEL.",
        )

    required = exp_required_for_level(
        stats.level
    )

    if stats.exp < required:

        return (
            False,
            stats,
            (
                "❌ Not enough EXP.\n"
                f"Required: <b>{required}</b>\n"
                f"Current: <b>{stats.exp}</b>"
            ),
        )

    with _LOCK:

        stats.exp -= required
        stats.level += 1

        # Small stat increase on level-up.
        stats.atk += 5
        stats.defense += 5
        stats.hp += 10
        stats.speed += 3

    return (
        True,
        stats,
        (
            "✨ <b>CARD LEVEL UP!</b>\n\n"
            f"🎴 Card: <code>{stats.card_id}</code>\n"
            f"⭐ Level: <b>{stats.level}</b>\n"
            f"⚔️ ATK: <b>{stats.atk}</b>\n"
            f"🛡️ DEF: <b>{stats.defense}</b>\n"
            f"❤️ HP: <b>{stats.hp}</b>\n"
            f"💨 Speed: <b>{stats.speed}</b>"
        ),
    )


# ============================================================
# DUEL COOLDOWN
# ============================================================

def get_duel_cooldown(
    user_id: int,
) -> timedelta:

    user_id = normalize_user_id(
        user_id
    )

    last_duel = _LAST_DUEL.get(
        user_id
    )

    if last_duel is None:
        return timedelta(0)

    next_duel = (
        last_duel
        + timedelta(
            seconds=DUEL_COOLDOWN_SECONDS
        )
    )

    remaining = (
        next_duel
        - utc_now()
    )

    if remaining.total_seconds() <= 0:
        return timedelta(0)

    return remaining


def can_duel(
    user_id: int,
) -> tuple[bool, str]:

    remaining = get_duel_cooldown(
        user_id
    )

    if remaining.total_seconds() <= 0:

        return (
            True,
            "OK",
        )

    return (
        False,
        format_duration(
            remaining
        ),
    )


def mark_duel_used(
    user_id: int,
) -> None:

    user_id = normalize_user_id(
        user_id
    )

    with _LOCK:
        _LAST_DUEL[user_id] = utc_now()


# ============================================================
# CARD POWER
# ============================================================

def calculate_power(
    stats: CardStats,
) -> float:

    level_multiplier = (
        1
        + (
            max(
                0,
                stats.level - 1
            )
            * 0.03
        )
    )

    return (
        (
            stats.atk * 0.40
            + stats.defense * 0.20
            + stats.hp * 0.25
            + stats.speed * 0.15
        )
        * level_multiplier
    )


# ============================================================
# ATTACK CALCULATION
# ============================================================

def calculate_damage(
    attacker: CardStats,
    defender: CardStats,
) -> int:

    base_attack = max(
        1,
        attacker.atk
    )

    defense = max(
        1,
        defender.defense
    )

    raw_damage = (
        base_attack
        * random.uniform(
            0.85,
            1.15,
        )
    )

    reduction = (
        defense
        / (
            defense
            + 100
        )
    )

    damage = (
        raw_damage
        * (
            1
            - reduction
        )
    )

    return max(
        MIN_DAMAGE,
        int(damage),
    )


# ============================================================
# TURN ORDER
# ============================================================

def determine_first_player(
    stats_a: CardStats,
    stats_b: CardStats,
) -> str:

    speed_a = stats_a.speed
    speed_b = stats_b.speed

    if speed_a > (
        speed_b
        * SPEED_ADVANTAGE
    ):
        return "A"

    if speed_b > (
        speed_a
        * SPEED_ADVANTAGE
    ):
        return "B"

    # Close speed = random turn order.
    return random.choice(
        ["A", "B"]
    )


# ============================================================
# BATTLE ENGINE
# ============================================================

def simulate_battle(
    user_a: int,
    card_a: str,
    user_b: int,
    card_b: str,
    max_rounds: int = 50,
) -> DuelResult:

    user_a = normalize_user_id(
        user_a
    )

    user_b = normalize_user_id(
        user_b
    )

    card_a = normalize_card_id(
        card_a
    )

    card_b = normalize_card_id(
        card_b
    )

    stats_a = get_card_stats(
        user_a,
        card_a,
    )

    stats_b = get_card_stats(
        user_b,
        card_b,
    )

    current_hp_a = stats_a.hp
    current_hp_b = stats_b.hp

    logs = []

    first = determine_first_player(
        stats_a,
        stats_b,
    )

    logs.append(
        (
            f"⚔️ Battle Start!\n"
            f"🎴 A: <code>{card_a}</code> "
            f"(Lv.{stats_a.level})\n"
            f"🎴 B: <code>{card_b}</code> "
            f"(Lv.{stats_b.level})"
        )
    )

    rounds = 0

    for round_number in range(
        1,
        max_rounds + 1,
    ):

        rounds = round_number

        if first == "A":

            damage = calculate_damage(
                stats_a,
                stats_b,
            )

            current_hp_b -= damage

            logs.append(
                (
                    f"Round {round_number}: "
                    f"🎴 A dealt "
                    f"<b>{damage}</b> damage."
                )
            )

            if current_hp_b <= 0:
                winner = "A"
                break

            damage = calculate_damage(
                stats_b,
                stats_a,
            )

            current_hp_a -= damage

            logs.append(
                (
                    f"Round {round_number}: "
                    f"🎴 B dealt "
                    f"<b>{damage}</b> damage."
                )
            )

            if current_hp_a <= 0:
                winner = "B"
                break

        else:

            damage = calculate_damage(
                stats_b,
                stats_a,
            )

            current_hp_a -= damage

            logs.append(
                (
                    f"Round {round_number}: "
                    f"🎴 B dealt "
                    f"<b>{damage}</b> damage."
                )
            )

            if current_hp_a <= 0:
                winner = "B"
                break

            damage = calculate_damage(
                stats_a,
                stats_b,
            )

            current_hp_b -= damage

            logs.append(
                (
                    f"Round {round_number}: "
                    f"🎴 A dealt "
                    f"<b>{damage}</b> damage."
                )
            )

            if current_hp_b <= 0:
                winner = "A"
                break

    else:

        # Max rounds reached.
        # Highest remaining HP wins.
        if current_hp_a >= current_hp_b:
            winner = "A"
        else:
            winner = "B"

        logs.append(
            "⏱️ Maximum rounds reached."
        )

    if winner == "A":

        winner_id = user_a
        loser_id = user_b

        winner_card = card_a
        loser_card = card_b

    else:

        winner_id = user_b
        loser_id = user_a

        winner_card = card_b
        loser_card = card_a

    result = DuelResult(
        success=True,
        winner_id=winner_id,
        loser_id=loser_id,
        winner_card_id=winner_card,
        loser_card_id=loser_card,
        winner_coins=BASE_WIN_COINS,
        loser_coins=BASE_LOSE_COINS,
        winner_exp=BASE_WIN_EXP,
        loser_exp=BASE_LOSE_EXP,
        rounds=rounds,
        battle_log=logs,
    )

    return result


# ============================================================
# DUEL EXECUTION
# ============================================================

def duel(
    user_a: int,
    card_a: str,
    user_b: int,
    card_b: str,
) -> DuelResult:

    user_a = normalize_user_id(
        user_a
    )

    user_b = normalize_user_id(
        user_b
    )

    card_a = normalize_card_id(
        card_a
    )

    card_b = normalize_card_id(
        card_b
    )

    if user_a == user_b:

        return DuelResult(
            success=False,
            message=(
                "❌ You cannot duel yourself."
            ),
        )

    can_a, reason_a = can_duel(
        user_a
    )

    if not can_a:

        return DuelResult(
            success=False,
            message=(
                "⏳ You are on cooldown.\n"
                f"Try again in <b>{reason_a}</b>."
            ),
        )

    can_b, reason_b = can_duel(
        user_b
    )

    if not can_b:

        return DuelResult(
            success=False,
            message=(
                "⏳ Opponent is on cooldown.\n"
                f"Try again in <b>{reason_b}</b>."
            ),
        )

    with _LOCK:

        mark_duel_used(
            user_a
        )

        mark_duel_used(
            user_b
        )

        result = simulate_battle(
            user_a,
            card_a,
            user_b,
            card_b,
        )

        if not result.success:
            return result

        # Winner EXP
        winner_stats = get_card_stats(
            result.winner_id,
            result.winner_card_id,
        )

        loser_stats = get_card_stats(
            result.loser_id,
            result.loser_card_id,
        )

        add_card_exp(
            result.winner_id,
            result.winner_card_id,
            result.winner_exp,
        )

        add_card_exp(
            result.loser_id,
            result.loser_card_id,
            result.loser_exp,
        )

        result.message = format_duel_result(
            result,
            winner_stats,
            loser_stats,
        )

        _DUEL_HISTORY.append(
            result
        )

        return result


# ============================================================
# FORMAT DUEL RESULT
# ============================================================

def format_duel_result(
    result: DuelResult,
    winner_stats: CardStats,
    loser_stats: CardStats,
) -> str:

    logs = "\n".join(
        result.battle_log[-8:]
    )

    return (
        "⚔️ <b>NEXUS DUEL</b>\n\n"
        f"🏆 Winner: "
        f"<code>{result.winner_id}</code>\n"
        f"🎴 Card: "
        f"<code>{result.winner_card_id}</code>\n"
        f"⭐ Level: "
        f"<b>{winner_stats.level}</b>\n\n"
        f"💀 Loser: "
        f"<code>{result.loser_id}</code>\n"
        f"🎴 Card: "
        f"<code>{result.loser_card_id}</code>\n"
        f"⭐ Level: "
        f"<b>{loser_stats.level}</b>\n\n"
        f"💰 Winner Reward: "
        f"<b>+{result.winner_coins:,}</b> Coins\n"
        f"💰 Participation: "
        f"<b>+{result.loser_coins:,}</b> Coins\n"
        f"✨ Winner EXP: "
        f"<b>+{result.winner_exp}</b>\n"
        f"✨ Loser EXP: "
        f"<b>+{result.loser_exp}</b>\n\n"
        f"🔢 Rounds: "
        f"<b>{result.rounds}</b>\n\n"
        "📜 <b>Battle Log</b>\n"
        f"{logs}"
    )


# ============================================================
# COMMAND PARSER
# ============================================================

def parse_duel_command(
    user_id: int,
    args: list[str],
    replied_user_id: Optional[int] = None,
) -> tuple[bool, dict, str]:

    """
    Example:

        /duel 0021

    Reply to another user's message.

    Or bot.py may provide opponent ID separately.
    """

    if not args:

        return (
            False,
            {},
            (
                "❌ Usage:\n"
                "<code>/duel CARD_ID</code>\n\n"
                "Example:\n"
                "<code>/duel 0021</code>"
            ),
        )

    if replied_user_id is None:

        return (
            False,
            {},
            "❌ Reply to the user you want to duel.",
        )

    card_id = normalize_card_id(
        args[0]
    )

    data = {
        "user_a": int(user_id),
        "user_b": int(replied_user_id),
        "card_a": card_id,
    }

    return (
        True,
        data,
        "OK",
    )


# ============================================================
# HISTORY
# ============================================================

def get_duel_history(
    limit: int = 50,
) -> list[DuelResult]:

    limit = max(
        1,
        int(limit),
    )

    with _LOCK:

        return list(
            reversed(
                _DUEL_HISTORY[-limit:]
            )
        )


def get_user_duel_history(
    user_id: int,
    limit: int = 50,
) -> list[DuelResult]:

    user_id = normalize_user_id(
        user_id
    )

    history = [
        duel_result
        for duel_result in get_duel_history(
            limit=100000
        )
        if (
            duel_result.winner_id == user_id
            or duel_result.loser_id == user_id
        )
    ]

    return history[
        :max(1, int(limit))
    ]


# ============================================================
# CARD STATS DISPLAY
# ============================================================

def format_card_stats(
    user_id: int,
    card_id: str,
) -> str:

    stats = get_card_stats(
        user_id,
        card_id,
    )

    required = exp_required_for_level(
        stats.level
    )

    return (
        "🎴 <b>CARD BATTLE STATS</b>\n\n"
        f"🆔 ID: <code>{stats.card_id}</code>\n"
        f"⭐ Level: <b>{stats.level}</b>/{MAX_LEVEL}\n"
        f"✨ EXP: <b>{stats.exp}</b>"
        f"/{required}\n\n"
        f"⚔️ ATK: <b>{stats.atk}</b>\n"
        f"🛡️ DEF: <b>{stats.defense}</b>\n"
        f"❤️ HP: <b>{stats.hp}</b>\n"
        f"💨 Speed: <b>{stats.speed}</b>\n"
        f"🌟 Element: <b>{stats.element}</b>\n\n"
        f"🔥 Power: "
        f"<b>{calculate_power(stats):.1f}</b>"
    )


# ============================================================
# DURATION FORMAT
# ============================================================

def format_duration(
    remaining: timedelta,
) -> str:

    seconds = max(
        0,
        int(
            remaining.total_seconds()
        ),
    )

    minutes, seconds = divmod(
        seconds,
        60,
    )

    hours, minutes = divmod(
        minutes,
        60,
    )

    parts = []

    if hours:
        parts.append(
            f"{hours}h"
        )

    if minutes:
        parts.append(
            f"{minutes}m"
        )

    if seconds or not parts:
        parts.append(
            f"{seconds}s"
        )

    return " ".join(parts)


# ============================================================
# ADMIN CONTROLS
# ============================================================

def admin_set_card_stats(
    user_id: int,
    card_id: str,
    **kwargs,
) -> CardStats:

    return set_card_stats(
        user_id,
        card_id,
        **kwargs,
    )


def admin_add_card_exp(
    user_id: int,
    card_id: str,
    amount: int,
) -> tuple[CardStats, int]:

    return add_card_exp(
        user_id,
        card_id,
        amount,
    )


def admin_reset_card_stats(
    user_id: int,
    card_id: str,
) -> CardStats:

    return set_card_stats(
        user_id,
        card_id,
        level=1,
        exp=0,
        atk=100,
        defense=100,
        hp=100,
        speed=100,
        element="Normal",
    )


# ============================================================
# RESET
# ============================================================

def reset_duel_system() -> None:

    with _LOCK:

        _CARD_STATS.clear()
        _LAST_DUEL.clear()
        _DUEL_HISTORY.clear()


def reset_user_duel_data(
    user_id: int,
) -> None:

    user_id = normalize_user_id(
        user_id
    )

    with _LOCK:

        _LAST_DUEL.pop(
            user_id,
            None
        )

        keys = [
            key
            for key in _CARD_STATS
            if key[0] == user_id
        ]

        for key in keys:
            _CARD_STATS.pop(
                key,
                None
            )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Config
    "DUEL_COOLDOWN_SECONDS",
    "BASE_WIN_COINS",
    "BASE_LOSE_COINS",
    "BASE_WIN_EXP",
    "BASE_LOSE_EXP",
    "MAX_LEVEL",
    "BASE_EXP_PER_LEVEL",

    # Data
    "CardStats",
    "DuelResult",

    # Card stats
    "get_card_stats",
    "set_card_stats",

    # EXP
    "exp_required_for_level",
    "get_level_progress",
    "add_card_exp",
    "upgrade_card",

    # Cooldown
    "get_duel_cooldown",
    "can_duel",
    "mark_duel_used",

    # Battle
    "calculate_power",
    "calculate_damage",
    "determine_first_player",
    "simulate_battle",
    "duel",

    # Commands
    "parse_duel_command",

    # History
    "get_duel_history",
    "get_user_duel_history",

    # Display
    "format_card_stats",
    "format_duel_result",
    "format_duration",

    # Admin
    "admin_set_card_stats",
    "admin_add_card_exp",
    "admin_reset_card_stats",

    # Reset
    "reset_duel_system",
    "reset_user_duel_data",
]
