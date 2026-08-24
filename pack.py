from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from database import SessionLocal,Pack,User
from services.pack_service import open_pack
router=Router()
@router.message(Command('packs'))
async def packs(m:Message):
 async with SessionLocal() as s:
  r=await s.execute(select(Pack).where(Pack.active.is_(True)));ps=r.scalars().all()
  if not ps:return await m.answer('No active packs.')
  await m.answer('🎴 PACKS\n\n'+'\n\n'.join(f'📦 {p.name}\n💰 {p.price_coins:,}\n/open_{p.id}' for p in ps))
@router.message(lambda m:bool(m.text) and m.text.startswith('/open_'))
async def op(m:Message):
 try:pid=int(m.text.split('_',1)[1])
 except:return await m.answer('Invalid pack.')
 async with SessionLocal() as s:
  ur=await s.execute(select(User).where(User.telegram_id==m.from_user.id));u=ur.scalar_one_or_none()
  pr=await s.execute(select(Pack).where(Pack.id==pid,Pack.active.is_(True)));p=pr.scalar_one_or_none()
  if not u:return await m.answer('Use /start first.')
  if not p:return await m.answer('Pack not found.')
  try:cs=await open_pack(s,u,p)
  except ValueError as e:return await m.answer(f'❌ {e}')
  await m.answer(f'🎉 {p.name}\n\n'+'\n\n'.join(f'🃏 {c.name}\n✨ {c.rarity}\n⚔️ {c.attack} 🛡️ {c.defense} ❤️ {c.hp}' for c in cs)+f'\n\n💰 {u.coins:,}')
