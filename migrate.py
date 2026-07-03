import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'app.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create 'obras' table
    print("Creating 'obras' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER NOT NULL, 
            cliente_id INTEGER NOT NULL, 
            nome VARCHAR(100) NOT NULL, 
            data_criacao DATETIME, 
            PRIMARY KEY (id), 
            FOREIGN KEY(cliente_id) REFERENCES clientes (id)
        )
    """)

    # 2. Check if 'registros' has 'cliente_id' (meaning we need to migrate)
    cursor.execute("PRAGMA table_info(registros)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'cliente_id' not in columns:
        print("Table 'registros' does not have 'cliente_id'. Already migrated?")
        conn.close()
        return

    # 3. Create "Obra Padrão" for all clients that have records
    print("Migrating data...")
    cursor.execute("SELECT DISTINCT cliente_id FROM registros")
    cliente_ids = cursor.fetchall()
    
    cliente_obra_map = {}
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    
    for (cid,) in cliente_ids:
        # Check if "Obra Padrão" already exists for this client
        cursor.execute("SELECT id FROM obras WHERE cliente_id = ? AND nome = ?", (cid, "Obra Padrão"))
        row = cursor.fetchone()
        if row:
            obra_id = row[0]
        else:
            cursor.execute("INSERT INTO obras (cliente_id, nome, data_criacao) VALUES (?, ?, ?)", 
                           (cid, "Obra Padrão", current_time))
            obra_id = cursor.lastrowid
        cliente_obra_map[cid] = obra_id

    # 4. Recreate 'registros' table
    print("Recreating 'registros' table...")
    cursor.execute("ALTER TABLE registros RENAME TO registros_old")
    
    cursor.execute("""
        CREATE TABLE registros (
            id INTEGER NOT NULL, 
            obra_id INTEGER NOT NULL, 
            nome_quadro VARCHAR(100) NOT NULL, 
            data_upload DATETIME, 
            PRIMARY KEY (id), 
            FOREIGN KEY(obra_id) REFERENCES obras (id)
        )
    """)

    # 5. Insert data into new table
    cursor.execute("SELECT id, cliente_id, nome_quadro, data_upload FROM registros_old")
    old_registros = cursor.fetchall()
    
    for row in old_registros:
        reg_id, cli_id, nome_quadro, data_up = row
        obra_id = cliente_obra_map.get(cli_id)
        if obra_id is None:
            # Fallback if somehow there's a record with a non-existent client?
            continue
        cursor.execute("""
            INSERT INTO registros (id, obra_id, nome_quadro, data_upload) 
            VALUES (?, ?, ?, ?)
        """, (reg_id, obra_id, nome_quadro, data_up))

    # 6. Drop old table
    print("Dropping old table...")
    cursor.execute("DROP TABLE registros_old")

    conn.commit()
    conn.close()
    print("Migration successful.")

if __name__ == '__main__':
    migrate()
