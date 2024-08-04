from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TOKEN
from handlers import matriz, banco, menu, upload, delet, button, adc_balance, verificar_saldo
from database import create_bins_table, copy_data_to_bins
from colorama import Fore, Style

def main():
    print("Iniciando a construção do aplicativo...")
    app = ApplicationBuilder().token(TOKEN).build()

    # Exibir mensagem colorida ao iniciar o bot
    print(Fore.GREEN + Style.BRIGHT + "Bot iniciado com sucesso!")

    print("Adicionando manipuladores de comando...")
    app.add_handler(CommandHandler("matriz", matriz))
    app.add_handler(CommandHandler("binsearch", banco))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("start", menu))
    app.add_handler(CommandHandler("upload", upload))
    app.add_handler(CommandHandler("delet", delet))
    app.add_handler(CommandHandler("remove", delet))
    app.add_handler(CommandHandler("recarga", adc_balance))
    app.add_handler(CommandHandler("saldo", verificar_saldo))
    app.add_handler(CallbackQueryHandler(button))
    
    print("Adicionando manipuladores de mensagem...")
    app.add_handler(MessageHandler(filters.Document.FileExtension("txt"), upload))
    
    print("Iniciando polling...")
    app.run_polling()
    print("Polling iniciado.")

if __name__ == '__main__':
    main()
