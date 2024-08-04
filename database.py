import sqlite3
from config import DB_NAME
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bin_sicredi = {
    '476331': '❌ BIN BANIDA ❌',
    '476332': '❌ BIN BANIDA ❌',
    '476333': '❌ BIN BANIDA ❌',
    '512267': '❌ BIN BANIDA ❌',
    '522590': '❌ BIN BANIDA ❌',
    '527680': '❌ BIN BANIDA ❌',
    '534520': '❌ BIN BANIDA ❌'
}

# Dicionário de BINs suspeitas
bin_safra = {
    '401684': '💳 CREDIT|PLATINUM',
    '411838': '💳 CREDIT|CLASSIC',
    '416812': '💳 CREDIT|CLASSIC',
    '448446': '💳 CREDIT|PURCHASING',
    '473267': '💳 CREDIT|CLASSIC',
    '473269': '💳 CREDIT|GOLD',
    '473270': '💳 CREDIT|PLATINUM',
    '473271': '💳 CREDIT|BUSINESS',
    '476506': '💳 CREDIT|CLASSIC',
    '476507': '💳 CREDIT|BUSINESS',
    '476508': '💳 CREDIT|GOLD',
    '479018': '💳 DEBIT|ELECTRON',
    '510556': '💳 WORLD BLACK|BRAZIL',
    '549207': '💳 PLATINUM|BRAZIL',
    '553639': '💳 BLACK|BRAZIL',
    '406647': '💳 DEBIT|ELECTRON',
    '406897': '💳 CREDIT|CLASSIC',
    '411809': '💳 CREDIT|CLASSIC',
    '418746': '💳 CREDIT|CLASSIC',
    '420310': '💳 CREDIT|CLASSIC',
    '420311': '💳 CREDIT|None',
    '420312': '💳 CREDIT|CLASSIC',
    '420314': '💳 CREDIT|None',
    '422221': '💳 CREDIT|CLASSIC',
    '431923': '💳 CREDIT|CORPORATE T&E',
    '432403': '💳 CREDIT|CLASSIC',
    '432404': '💳 CREDIT|GOLD',
    '432405': '💳 CREDIT|PLATINUM',
    '434639': '💳 CREDIT|CLASSIC',
    '449745': '💳 CREDIT|None',
    '454046': '💳 CREDIT|CLASSIC',
    '454047': '💳 CREDIT|GOLD PREMIUM',
    '454479': '💳 CREDIT|BUSINESS',
    '456871': '💳 CREDIT|GOLD PREMIUM',
    '469872': '💳 CREDIT|PLATINUM',
    '474513': '💳 CREDIT|CLASSIC',
    '483066': '💳 CREDIT|CLASSIC',
    '483067': '💳 CREDIT|PLATINUM',
    '489429': '💳 CREDIT|CLASSIC',
    '491256': '💳 CREDIT|GOLD',
    '493493': '💳 CREDIT|CLASSIC',
    '493494': '💳 CREDIT|CLASSIC',
    '430535': '💳 CREDIT|CLASSIC',
    '468210': '💳 CREDIT|GOLD',
    '476502': '💳 CREDIT|None',
    '484132': '💳 CREDIT|PLATINUM',
    '486633': '💳 CREDIT|PURCHASING',
    '491411': '💳 CREDIT|GOLD',
    '491412': '💳 CREDIT|CLASSIC',
    '491413': '💳 CREDIT|None'
}

def create_bins_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bin TEXT,
                bandeira TEXT,
                banco TEXT,
                nivel TEXT,
                pais TEXT
            )
        ''')
        conn.commit()
        logger.info("Tabela 'bins' criada com sucesso.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar a tabela bins: {e}")
    finally:
        conn.close()

def copy_data_to_bins():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT cc FROM matrizggs')
        rows = cursor.fetchall()
        cursor.executemany('INSERT INTO bins (bin) VALUES (?)', [(row[0][:6],) for row in rows])
        conn.commit()
        logger.info("Dados copiados com sucesso para a tabela bins.")
    except sqlite3.Error as e:
        logger.error(f"Erro ao copiar dados: {e}")
    finally:
        conn.close()

def process_matriz(gg_provided):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT cc, mes, ano, cvv FROM matrizggs WHERE cc LIKE ?', (gg_provided + '%',))
    rows = cursor.fetchall()
    conn.close()

    processed_data = {}
    result = []

    for row in rows:
        gg, mes, ano, cvv = row
        gg_trimmed = gg[:-5]  # Remover os últimos 5 dígitos
        bin = gg[:6]
        unique_key = (gg_trimmed, mes, ano, cvv)

        if unique_key not in processed_data:
            processed_data[unique_key] = 1
        else:
            processed_data[unique_key] += 1

    for (gg_trimmed, mes, ano, cvv), count in processed_data.items():
        if count >= 3:  # Aparece 3 vezes ou mais
            if bin in bin_sicredi:
                parte_1 = gg_trimmed[:7]
                final_digit = gg_trimmed[-1]
                result.append(f"❌ {parte_1}xxxxxx{final_digit}xx|{mes}/{ano}|000 [apareceu {count}x]")
            elif bin in bin_safra:
                parte_1 = gg_trimmed[:7]
                final_digit = gg_trimmed[-1]
                result.append(f"🔍 {parte_1}xxxxxx{final_digit}xx|{mes}/{ano}|000 [apareceu {count}x]")
            else:
                result.append(f"🛡️ {gg_trimmed}xxxxx|{mes}/{ano}|000 [apareceu {count}x]")

    return result


def process_banco(bandeira, banco):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT bin, nivel, pais FROM bins WHERE bandeira LIKE ? AND banco LIKE ?', (f'%{bandeira.strip()}%', f'%{banco.strip()}%'))
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        rows = [f"Erro ao consultar o banco de dados: {e}"]
    finally:
        conn.close()

    if rows:
        result = ['|'.join(map(str, row)) for row in rows]
    else:
        result = ['**❌ Não encontrei resultados.**']
    
    return result


def process_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT creditos FROM user WHERE id = ?', (user_id,))
        row = cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"Erro ao consultar o banco de dados: {e}")
        return False
    finally:
        conn.close()
        
    if row and row[0] is not None:
        try:
            creditos = int(row[0])
            return creditos > 0
        except ValueError:
            logger.error(f"Erro ao converter créditos para inteiro: {row[0]}")
            return False
    else:
        return False
    
    
def remove_saldo(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Remover 10 do saldo do usuário
        cursor.execute('UPDATE user SET creditos = creditos - 10 WHERE id = ? AND creditos >= 10', (user_id,))
        
        # Verificar se alguma linha foi afetada (se o saldo foi atualizado)
        if cursor.rowcount == 0:
            logger.warning("Usuário não encontrado ou saldo insuficiente.")
            conn.rollback()  # Reverter a transação
            return False
        else:
            conn.commit()  # Confirmar a transação
            return True
    except sqlite3.Error as e:
        logger.error(f"Erro ao atualizar o saldo: {e}")
        conn.rollback()  # Reverter a transação em caso de erro
        return False
    finally:
        conn.close()
        
def adc_saldo(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Verificar se o usuário existe
        cursor.execute('SELECT creditos FROM user WHERE id = ?', (user_id,))
        row = cursor.fetchone()

        if row is None:
            # Usuário não encontrado, cadastrar novo usuário com o saldo fornecido
            cursor.execute('INSERT INTO user (id, creditos) VALUES (?, ?)', (user_id, amount))
            logger.info(f"Novo usuário cadastrado com ID: {user_id} e saldo: {amount}")
        else:
            # Usuário encontrado, atualizar saldo existente
            saldo_atual = int(row[0])  # Certificar que saldo_atual é um inteiro
            novo_saldo = saldo_atual + amount
            cursor.execute('UPDATE user SET creditos = ? WHERE id = ?', (novo_saldo, user_id))
            logger.info(f"Saldo atualizado para o usuário ID: {user_id}. Novo saldo: {novo_saldo}")

        conn.commit()  # Confirmar a transação
        return True

    except sqlite3.Error as e:
        logger.error(f"Erro ao adicionar saldo: {e}")
        conn.rollback()  # Reverter a transação em caso de erro
        return False

    finally:
        conn.close()

def obter_saldo(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT creditos FROM user WHERE id = ?', (user_id,))
        row = cursor.fetchone()

        if row is not None:
            return row[0]  # Retorna o saldo encontrado
        else:
            return None  # Retorna None se o usuário não for encontrado

    except sqlite3.Error as e:
        logger.error(f"Erro ao obter saldo: {e}")
        return None

    finally:
        conn.close()

    
def execute_sql_query(query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        affected_rows = cursor.rowcount  # Captura o número de linhas afetadas pela operação DELETE
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Erro ao executar a query: {e}", 0
    finally:
        conn.close()

    return True, None, affected_rows