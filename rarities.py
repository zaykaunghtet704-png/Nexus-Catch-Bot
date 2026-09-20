from dataclasses import dataclass
@dataclass(frozen=True)
class Rarity:
    name:str; order:int; default_rate:float
RARITIES=[Rarity('Common',1,55),Rarity('Uncommon',2,20),Rarity('Rare',3,10),Rarity('Epic',4,5),Rarity('Ultra',5,3),Rarity('Legendary',6,2),Rarity('Mythic',7,1.2),Rarity('Divine',8,.8),Rarity('Eternal',9,.5),Rarity('Celestial',10,.3),Rarity('Immortal',11,.15),Rarity('Supreme',12,.04),Rarity('Premium Edition',13,.01)]
RARITY_ORDER={r.name:r.order for r in RARITIES}
