from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from database import process_matriz, process_banco, execute_sql_query, process_user, remove_saldo, adc_saldo, obter_saldo
from utils import send_large_message, send_message_to_user, send_message_to_group, extract_card_data, check_and_insert_card
import os
from colorama import Fore, Style
import logging
import telegram

# Configurar o logger

logger = logging.getLogger(__name__)

async def matriz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1 or len(context.args[0]) < 6:
        await update.message.reply_text('**Por favor, forneça um valor de matriz válido. Uso: /matriz <valor>**', parse_mode='Markdown')
        return

    gg_provided = context.args[0]
    result = process_matriz(gg_provided)

    chat_id = update.effective_chat.id
    logger.info(f"Chat ID: {chat_id}")

    if process_user(chat_id):
        if result:
            if remove_saldo(chat_id):
                response_user = "✅ **Segue abaixo a matriz solicitada:**\n\n" + '\n'.join(result)
                response_group = f"Mensagem enviada para {update.effective_user.first_name} ({update.effective_user.id}):\n" + response_user
            else:
                response_user = '**❌ Falha ao remover saldo.**'
                response_group = f"Tentativa de consulta de matriz falhou para {update.effective_user.first_name} ({update.effective_user.id})."
        else:
            response_user = '**❌ Matriz não encontrada para o valor fornecido.**'
            response_group = f"Tentativa de consulta de matriz falhou para {update.effective_user.first_name} ({update.effective_user.id})."

        try:
            await send_large_message(update, response_user)
            await send_message_to_group(context.bot, response_group)
        except telegram.error.BadRequest as e:
            await update.message.reply_text(f"Ocorreu um erro ao tentar enviar uma mensagem para o grupo: {e}")
        except Exception as e:
            await update.message.reply_text(f"Ocorreu um erro inesperado: {e}")
    else:
        response_user = '**❌ Sem Acesso**'
        await send_large_message(update, response_user)


async def banco(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1 or '|' not in ' '.join(context.args):
        await send_message_to_user(update, '**Por favor, forneça valores válidos. Uso: /banco {bandeira}|{banco}**')
        return

    full_arg = ' '.join(context.args)
    bandeira, banco = full_arg.split('|', 1)
    
    if len(bandeira.strip()) < 3 or len(banco.strip()) < 3:
        await send_message_to_user(update, '**Cada parâmetro deve ter pelo menos 3 caracteres. Uso: /banco {bandeira}|{banco}**')
        return

    result = process_banco(bandeira.strip(), banco.strip())

    response = '\n'.join(result)
    keyboard = [[InlineKeyboardButton("🗑️ APAGAR RESULTADO ", callback_data="close")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_large_message(update, response)

    response_group = f"Mensagem enviada para {update.effective_user.first_name} ({update.effective_user.id}):\n" + response
    await send_message_to_group(context.bot, response_group)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "🛠️ *Menu de Comandos*\n\n" \
               "🔹 */matriz 498407 - Consulta matriz*\n" \
               "🔹 */banco MASTERCARD|COOPERATIVO SICREDI - Consulta banco*\n" \
               "🔹 */menu - Mostra este menu*\n" \
               "🔹 */delet - Limpa o banco de dados*\n"

    keyboard = [[InlineKeyboardButton("🗑️ APAGAR RESULTADO ", callback_data="close")]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.document:
        await update.message.reply_text('**Por favor, envie um arquivo .txt válido.**', parse_mode='Markdown')
        return
    
    file = await context.bot.get_file(update.message.document.file_id)
    file_path = await file.download_as_bytearray()
    file_content = file_path.decode('utf-8')

    card_data = extract_card_data(file_content)
    new_cards = check_and_insert_card(card_data)

    if new_cards:
        response = "📋 *Relatório de Cartões Adicionados*\n\n" + '\n'.join([f"`{cc}|{mes}|{ano}|{cvv}`" for cc, mes, ano, cvv in new_cards])
        print("Cartões foram adicionados com sucesso.")
    else:
        response = "✅ Nenhum cartão novo encontrado para adicionar."

    await send_large_message(update, response)


async def delet(update: Update, context: CallbackContext) -> None:
    # Query para deletar cartões cuja validade já passou
    query1 = """
    DELETE FROM matrizggs
    WHERE (ANO < strftime('%Y', 'now')) OR (ANO = strftime('%Y', 'now') AND MES < strftime('%m', 'now'));
    """

    # Query para deletar duplicatas mantendo apenas a primeira entrada
    query2 = """
    DELETE FROM matrizggs
    WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM matrizggs
        GROUP BY CC
    );
    """

    # Executar as queries
    success1, error1, count1 = execute_sql_query(query1)
    success2, error2, count2 = execute_sql_query(query2)

    log_messages = []

    # Gerar log das operações
    log_messages.append("ℹ️ *Operações de Deleção Executadas*")

    if success1:
        log_messages.append(f"✅ Cartões com validade expirada foram removidos: {count1} registros.")
        print(f"Cartões com validade expirada foram removidos: {count1} registros.")
    else:
        log_messages.append(f"❌ Erro ao remover cartões com validade expirada: {error1}")

    if success2:
        log_messages.append(f"✅ Duplicatas foram removidas, mantendo apenas a primeira entrada: {count2} registros.")
        print(f"Duplicatas foram removidas, mantendo apenas a primeira entrada: {count2} registros.")
    else:
        log_messages.append(f"❌ Erro ao remover duplicatas: {error2}")

    # Enviar log como resposta
    response = "\n".join(log_messages)
    await send_message_to_user(update, response)
    await send_message_to_group(context.bot, response)


async def adc_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    # Verifica se o chat_id é igual ao fornecido e converte para inteiro, se necessário
    if chat_id == 6214704825:
        if len(context.args) < 1 or '|' not in ' '.join(context.args):
            await send_message_to_user(update, '**Por favor, forneça valores válidos. Uso: /recarga {id}|{saldo}**')
            return

        full_arg = ' '.join(context.args)
        user_id_str, saldo_str = full_arg.split('|', 1)

        try:
            user_id = int(user_id_str.strip())
            saldo = int(saldo_str.strip())
        except ValueError:
            await send_message_to_user(update, '**ID ou saldo fornecido inválido. Certifique-se de que ambos sejam números.**')
            return

        if adc_saldo(user_id, saldo):
            await send_message_to_user(update, '💰 **Saldo adicionado com sucesso!**')
        else:
            await send_message_to_user(update, '**Erro ao adicionar saldo. Verifique se o ID do usuário é válido.**')
    else:
        await send_message_to_user(update, '**Acesso não autorizado.**')
        
async def verificar_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    # Chamada assíncrona para obter o saldo
    saldo = obter_saldo(str(user_id))
    
    if saldo is not None:
        mensagem = f"💳 Seu saldo atual é: {saldo} créditos."
    else:
        mensagem = "❌ Erro ao verificar o saldo. Tente novamente mais tarde."

    # Envia a mensagem de resposta para o usuário
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensagem)



async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "close":
        await query.message.delete()