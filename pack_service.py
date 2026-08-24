import random
from sqlalchemy import select
from database import Card,EconomyTransaction,Pack,PackOpening,PackRate,PityCounter,User,UserCard
from rarities import RARITY_ORDER

def choose_rarity(rates):
 total=sum(max(0,r.rate) for r in rates)
 roll=random.uniform(0,total); cur=0
 for r in rates:
  cur+=max(0,r.rate)
  if roll<=cur:return r.rarity
 return rates[-1].rarity
async def get_pity(s,uid,pid):
 r=await s.execute(select(PityCounter).where(PityCounter.user_id==uid,PityCounter.pack_id==pid)); p=r.scalar_one_or_none()
 if not p:p=PityCounter(user_id=uid,pack_id=pid);s.add(p);await s.flush()
 return p
async def open_pack(s,user,pack):
 if not pack.active:raise ValueError('Pack is unavailable.')
 if user.coins<pack.price_coins:raise ValueError('Not enough coins.')
 rr=await s.execute(select(PackRate).where(PackRate.pack_id==pack.id));rates=rr.scalars().all()
 if not rates:raise ValueError('Pack rates are not configured.')
 p=await get_pity(s,user.id,pack.id);user.coins-=pack.price_coins;s.add(EconomyTransaction(user_id=user.id,transaction_type='PACK_PURCHASE',currency='coins',amount=-pack.price_coins,description=pack.name));out=[]
 for _ in range(pack.cards_per_open):
  p.pulls+=1;r=choose_rarity(rates)
  if p.pulls>=p.mythic_pity:r=random.choice([x for x,o in RARITY_ORDER.items() if o>=7]);p.pulls=0
  elif p.pulls>=p.legendary_pity:r=random.choice([x for x,o in RARITY_ORDER.items() if o>=6]);p.pulls=0
  cr=await s.execute(select(Card).where(Card.rarity==r)); cards=cr.scalars().all()
  if not cards:
   cr=await s.execute(select(Card));cards=cr.scalars().all()
  if not cards:raise ValueError('No cards in database.')
  card=random.choice(cards);out.append(card)
  ur=await s.execute(select(UserCard).where(UserCard.user_id==user.id,UserCard.card_id==card.id));owned=ur.scalar_one_or_none()
  if owned:owned.quantity+=1
  else:s.add(UserCard(user_id=user.id,card_id=card.id))
  s.add(PackOpening(user_id=user.id,pack_id=pack.id,card_id=card.id,rarity=card.rarity))
 await s.commit();return out
