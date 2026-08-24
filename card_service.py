from sqlalchemy import select
from database import Card, User, UserCard


async def get_user(session, telegram_id: int):
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def add_card(session, user: User, card: Card):
    result = await session.execute(
        select(UserCard).where(
            UserCard.user_id == user.id,
            UserCard.card_id == card.id
        )
    )

    owned = result.scalar_one_or_none()

    if owned:
        owned.quantity += 1
    else:
        session.add(
            UserCard(
                user_id=user.id,
                card_id=card.id
            )
        )
