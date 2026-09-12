from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from os import getenv

def main_keyboard(): return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="▶ Открыть Wathis",web_app=WebAppInfo(url=getenv("WEBAPP_URL","https://example.com")))]])
