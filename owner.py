from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from config import settings
from database import AuditLog,SessionLocal,User
router=Router()
def owner(m):return m.from_user.id==settings.owner_id
@router.message(Command('owner'))
async def panel(m):
 if not owner(m):return await m.answer('⛔ Owner only.')
 await m.answer('/owner_stats\n/owner_user <id>\n/owner_give <id> <coins>')
@router.message(Command('owner_stats'))
async def stats(m):
 if not owner(m):return await m.answer('⛔ Owner only.')
 async with SessionLocal() as s:r=await s.execute(select(User));await m.answer(f'👑 Users: {len(r.scalars().all())}')
@router.message(Command('owner_user'))
async def ou(m):
 if not owner(m):return await m.answer('⛔ Owner only.')
 try:tid=int(m.text.split()[1])
 except:return await m.answer('Usage: /owner_user <telegram_id>')
 async with SessionLocal() as s:
  r=await s.execute(select(User).where(User.telegram_id==tid));u=r.scalar_one_or_none()
  if not u:return await m.answer('Not found.')
  await m.answer(f'👤 {u.first_name}\n🆔 {u.telegram_id}\n💰 {u.coins:,}\n💎 {u.gems:,}')
@router.message(Command('owner_give'))
async def give(m):
 if not owner(m):return await m.answer('⛔ Owner only.')
 try:tid,amt=map(int,m.text.split()[1:3])
 except:return await m.answer('Usage: /owner_give <id> <coins>')
 if amt<=0:return await m.answer('Amount must be positive.')
 async with SessionLocal() as s:
  r=await s.execute(select(User).where(User.telegram_id==tid));u=r.scalar_one_or_none()
  if not u:return await m.answer('Not found.')
  u.coins+=amt;s.add(AuditLog(actor_id=m.from_user.id,action='OWNER_GIVE_COINS',target_id=tid,details=str(amt)));await s.commit();await m.answer(f'✅ +{amt:,} coins')
