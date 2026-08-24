from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from database import SessionLocal,User,UserCard,Card
router=Router()
@router.message(Command('start'))
async def start(m:Message):
 async with SessionLocal() as s:
  r=await s.execute(select(User).where(User.telegram_id==m.from_user.id));u=r.scalar_one_or_none()
  if not u:u=User(telegram_id=m.from_user.id,username=m.from_user.username,first_name=m.from_user.first_name or 'Player');s.add(u);await s.commit()
  await m.answer('🎴 Advanced Card Bot\n\n/start /profile /cards /daily /packs')
@router.message(Command('profile'))
async def profile(m:Message):
 async with SessionLocal() as s:
  r=await s.execute(select(User).where(User.telegram_id==m.from_user.id));u=r.scalar_one_or_none()
  if not u:return await m.answer('Use /start first.')
  await m.answer(f'👤 {u.first_name}\n⭐ Lv.{u.level}\n✨ XP {u.xp}\n💰 {u.coins:,}\n💎 {u.gems:,}')
@router.message(Command('cards'))
async def cards(m:Message):
 async with SessionLocal() as s:
  r=await s.execute(select(UserCard,Card).join(Card,UserCard.card_id==Card.id).join(User,UserCard.user_id==User.id).where(User.telegram_id==m.from_user.id));rows=r.all()
  if not rows:return await m.answer('🎴 Collection empty.')
  await m.answer('🎴 COLLECTION\n\n'+'\n'.join(f'• {c.name} [{c.rarity}] ×{u.quantity}' for u,c in rows[:50]))
