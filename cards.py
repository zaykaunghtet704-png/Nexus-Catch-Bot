from database import cards_col

def seed_initial_cards():
    if cards_col.count_documents({}) == 0:
        sample_cards = [
            {
                "card_id": "c001",
                "name": "Rem",
                "anime": "Re:Zero",
                "rarity": "SR",
                "image_url": "https://i.imgur.com/example1.jpg"
            },
            {
                "card_id": "c002",
                "name": "Zero Two",
                "anime": "Darling in the Franxx",
                "rarity": "SSR",
                "image_url": "https://i.imgur.com/example2.jpg"
            },
            {
                "card_id": "c003",
                "name": "Nezuko Kamado",
                "anime": "Demon Slayer",
                "rarity": "R",
                "image_url": "https://i.imgur.com/example3.jpg"
            }
        ]
        cards_col.insert_many(sample_cards)
        print("နမူနာ ကတ်များ ထည့်သွင်းပြီးပါပြီ။")

seed_initial_cards()
