import os
import re
import sqlite3
from telegram import InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes
from config import MESSAGE_LIMIT, GROUP_ID, DB_NAME
from database import process_banco

def extract_card_data(text):
    pattern = r'(\d{16})\|(\d{2})\|(\d{2,4})\|(\d{3})'
    return re.findall(pattern, text)

def check_and_insert_card(card_data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    new_cards = []
    try:
        for cc, mes, ano, cvv in card_data:
            # Corrigir ano se tiver dois dígitos
            if len(ano) == 2:
                ano = '20' + ano
            # Excluir cartões com ano menor que 2024
            if int(ano) < 2024:
                continue
            cursor.execute('SELECT cc FROM matrizggs WHERE cc = ?', (cc[:12],))
            existing_card = cursor.fetchone()
            if existing_card is None:
                cursor.execute('INSERT INTO matrizggs (cc, mes, ano, cvv) VALUES (?, ?, ?, ?)', (cc, mes, ano, cvv))
                new_cards.append((cc, mes, ano, cvv))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao inserir dados: {e}")
    finally:
        conn.close()
    return new_cards

async def send_large_message(update: Update, response: str) -> None:
    if len(response) > MESSAGE_LIMIT:
        with open("response.txt", "w", encoding="utf-8") as file:
            file.write(response)
        
        with open("response.txt", "rb") as file:
            await update.message.reply_document(InputFile(file, filename="response.txt"))
        
        os.remove("response.txt")
    else:
        await update.message.reply_text(response, parse_mode='Markdown')

async def send_message_to_user(update: Update, response: str) -> None:
    await update.message.reply_text(response, parse_mode='Markdown')

async def send_message_to_group(bot, response: str) -> None:
    await bot.send_message(GROUP_ID, response, parse_mode='Markdown')
