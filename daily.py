from datetime import datetime,timezone,timedelta
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from database import DailyReward,EconomyTransaction,SessionLocal,User
router=Router()
@router.message(Command('daily'))
async def daily(m:Message):
 now=datetime.now(timezone.utc)
 async with SessionLocal() as s:
  r=await s.execute(select(User).where(User.telegram_id==m.from_user.id));u=r.scalar_one_or_none()
  if not u:return await m.answer('Use /start first.')
  r=await s.execute(select(DailyReward).where(DailyReward.user_id==u.id));d=r.scalar_one_or_none()
  if not d:d=DailyReward(user_id=u.id);s.add(d);await s.flush()
  if d.last_claimed_at and now-d.last_claimed_at<timedelta(hours=24):return await m.answer('⏳ Daily already claimed.')
  if d.last_claimed_at and now-d.last_claimed_at>timedelta(hours=48):d.streak=0
  d.streak+=1;d.last_claimed_at=now;coins=min(500+d.streak*50,5000);u.coins+=coins;u.xp+=25;s.add(EconomyTransaction(user_id=u.id,transaction_type='DAILY_REWARD',currency='coins',amount=coins,description=f'Day {d.streak}'));await s.commit();await m.answer(f'🎁 DAILY\n🔥 Streak {d.streak}\n💰 +{coins:,}\n✨ +25 XP')
