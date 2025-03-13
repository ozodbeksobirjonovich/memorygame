# app/database.py
from peewee import *
import json
from pathlib import Path
import os
from datetime import datetime

# Database configuration
db_path = Path("memory_game.db")
db = SqliteDatabase(db_path)

# Viloyatlar va tumanlar ma'lumotlari
def load_regions():
    regions_file = Path("app/static/data/regions.json")
    if regions_file.exists():
        with open(regions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def create_tables():
    from app.models import User, GameResult, Session, GameProgress
    
    db.create_tables([User, GameResult, Session, GameProgress])
    
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