import asyncio
from database import init_db,SessionLocal,Card,Pack,PackRate
from rarities import RARITIES
async def main():
 await init_db()
 async with SessionLocal() as s:
  s.add_all([Card(name='Flame Knight',rarity='Common',attack=100,defense=80,hp=500),Card(name='Shadow Dragon',rarity='Rare',attack=300,defense=250,hp=1200),Card(name='Premium Phoenix',rarity='Premium Edition',attack=2500,defense=2000,hp=10000,is_limited=True,is_animated=True)])
  p=Pack(name='Starter Pack',price_coins=500,cards_per_open=1,opens_per_day=10);s.add(p);await s.flush();s.add_all([PackRate(pack_id=p.id,rarity=r.name,rate=r.default_rate) for r in RARITIES]);await s.commit()
if __name__=='__main__':asyncio.run(main())
