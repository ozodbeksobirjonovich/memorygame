import aiosqlite
import os
import json
from pathlib import Path

DB_PATH = "memory_game.db"

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

# Viloyatlar va tumanlar ma'lumotlari
async def load_regions():
    regions_file = Path("app/static/data/regions.json")
    if regions_file.exists():
        with open(regions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

async def create_tables():
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            region TEXT NOT NULL,
            district TEXT NOT NULL,
            avatar TEXT DEFAULT 'default_avatar.png',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Game results table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            level INTEGER NOT NULL,
            stage INTEGER NOT NULL,
            grid_size INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            completed BOOLEAN NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create regions data
        regions_data = Path("app/static/data")
        if not regions_data.exists():
            regions_data.mkdir(parents=True)
            
        regions_file = regions_data / "regions.json"
        if not regions_file.exists():
            # O'zbekiston viloyatlari va tumanlari
            regions = {
                "Toshkent shahri": ["Bektemir", "Chilonzor", "Mirzo Ulug'bek", "Mirobod", "Sergeli", "Shayxontohur", "Olmazor", "Uchtepa", "Yakkasaroy", "Yunusobod", "Yashnobod"],
                "Toshkent viloyati": ["Angren", "Bekobod", "Bo'stonliq", "Bo'ka", "Chinoz", "Qibray", "Ohangaron", "Oqqo'rg'on", "Parkent", "Piskent", "O'rtachirchiq", "Yangiyo'l", "Yuqorichirchiq", "Zangiota"],
                "Andijon viloyati": ["Andijon", "Asaka", "Baliqchi", "Bo'z", "Buloqboshi", "Jalaquduq", "Izboskan", "Qo'rg'ontepa", "Marhamat", "Oltinko'l", "Paxtaobod", "Shahrixon", "Ulug'nor", "Xo'jaobod"],
                "Buxoro viloyati": ["Buxoro", "G'ijduvon", "Jondor", "Kogon", "Olot", "Peshku", "Qorako'l", "Qorovulbozor", "Romitan", "Shofirkon", "Vobkent"],
                "Farg'ona viloyati": ["Oltiariq", "Bag'dod", "Beshariq", "Buvayda", "Dang'ara", "Farg'ona", "Furqat", "Qo'qon", "Qo'shtepa", "Quva", "Rishton", "So'x", "Toshloq", "Uchko'prik", "O'zbekiston", "Yozyovon"],
                "Jizzax viloyati": ["Arnasoy", "Baxmal", "Do'stlik", "Forish", "G'allaorol", "Jizzax", "Mirzacho'l", "Paxtakor", "Yangiobod", "Zomin", "Zafarobod", "Zarbdor"],
                "Xorazm viloyati": ["Bog'ot", "Gurlan", "Xonqa", "Hazorasp", "Xiva", "Qo'shko'pir", "Shovot", "Urganch", "Yangiariq", "Yangibozor"],
                "Namangan viloyati": ["Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Namangan", "Norin", "Pop", "To'raqo'rg'on", "Uchqo'rg'on", "Uychi", "Yangiqo'rg'on"],
                "Navoiy viloyati": ["Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa", "Tomdi", "Uchquduq", "Xatirchi"],
                "Qashqadaryo viloyati": ["Chiroqchi", "Dehqonobod", "G'uzor", "Qamashi", "Qarshi", "Koson", "Kitob", "Mirishkor", "Muborak", "Nishon", "Shahrisabz", "Yakkabog'"],
                "Samarqand viloyati": ["Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on", "Narpay", "Nurobod", "Oqdaryo", "Payariq", "Pastdarg'om", "Paxtachi", "Samarqand", "Toyloq", "Urgut"],
                "Sirdaryo viloyati": ["Boyovut", "Guliston", "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo", "Xovos"],
                "Surxondaryo viloyati": ["Angor", "Bandixon", "Boysun", "Denov", "Jarqo'rg'on", "Qiziriq", "Qumqo'rg'on", "Muzrabot", "Oltinsoy", "Sariosiyo", "Sherobod", "Sho'rchi", "Termiz", "Uzun"],
                "Qoraqalpog'iston": ["Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a", "Kegeyli", "Mo'ynoq", "Nukus", "Qanliko'l", "Qo'ng'irot", "Qorao'zak", "Shumanay", "Taxtako'pir", "To'rtko'l", "Xo'jayli"]
            }
            with open(regions_file, "w", encoding="utf-8") as f:
                json.dump(regions, f, ensure_ascii=False, indent=4)
        
        await db.commit()