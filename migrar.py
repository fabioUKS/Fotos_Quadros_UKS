import sqlite3
import os
import argparse
from datetime import datetime
from pathlib import Path

# ============================================
# CONFIGURAÇÕES
# ============================================
DB_PATH = 'C:/Users/UKS EST/git/Fotos_Quadros_UKS/instance/app.db'
PASTA_RAIZ = 'E:/Fotos Quadros'
PASTA_ANO = '2026'

# ============================================
# CONEXÃO COM O BANCO
# ============================================
def conectar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    return conn, cursor

# ============================================
# FUNÇÕES DE BUSCA (evitam duplicatas)
# ============================================
def get_cliente_id(cursor, nome_cliente):
    """Busca ID do cliente ou cria se não existir"""
    cursor.execute("SELECT id FROM clientes WHERE nome = ?", (nome_cliente,))
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0], False  # Já existia
    
    # Não existe, criar
    cursor.execute("""
        INSERT INTO clientes (nome, data_criacao)
        VALUES (?, ?)
    """, (nome_cliente, datetime.now()))
    
    return cursor.lastrowid, True  # Foi criado agora

def get_obra_id(cursor, cliente_id, nome_obra):
    """Busca ID da obra ou cria se não existir"""
    cursor.execute("""
        SELECT id FROM obras 
        WHERE cliente_id = ? AND nome = ?
    """, (cliente_id, nome_obra))
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0], False
    
    cursor.execute("""
        INSERT INTO obras (cliente_id, nome, data_criacao)
        VALUES (?, ?, ?)
    """, (cliente_id, nome_obra, datetime.now()))
    
    return cursor.lastrowid, True

def get_registro_id(cursor, obra_id, nome_registro):
    """Busca ID do registro ou cria se não existir"""
    cursor.execute("""
        SELECT id FROM registros 
        WHERE obra_id = ? AND nome_quadro = ?
    """, (obra_id, nome_registro))
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0], False
    
    cursor.execute("""
        INSERT INTO registros (obra_id, nome_quadro, data_upload)
        VALUES (?, ?, ?)
    """, (obra_id, nome_registro, datetime.now()))
    
    return cursor.lastrowid, True

def foto_existe(cursor, registro_id, nome_arquivo, caminho):
    """Verifica se a foto já existe (evita duplicatas)"""
    cursor.execute("""
        SELECT id FROM fotos 
        WHERE registro_id = ? AND nome_arquivo = ? AND caminho = ?
    """, (registro_id, nome_arquivo, caminho))
    return cursor.fetchone() is not None

# ============================================
# FUNÇÃO PARA MIGRAR
# ============================================
def migrar_dados(n_clientes):
    conn, cursor = conectar_banco()
    
    try:
        # Estatísticas
        stats = {
            'clientes_novos': 0,
            'clientes_existentes': 0,
            'obras_novas': 0,
            'obras_existentes': 0,
            'registros_novos': 0,
            'registros_existentes': 0,
            'fotos_novas': 0,
            'fotos_duplicadas': 0,
            'erros': 0
        }
        
        # Define a pasta base
        if PASTA_ANO:
            pasta_base = Path(PASTA_RAIZ) / PASTA_ANO
        else:
            pasta_base = Path(PASTA_RAIZ)
        
        if not pasta_base.exists():
            print(f"❌ Pasta não encontrada: {pasta_base}")
            return
        
        print(f"📁 Pasta base: {pasta_base}")
        print(f"📊 Limite de clientes: {n_clientes if n_clientes != 'all' else 'TODOS'}")
        print("=" * 70)
        
        # Lista pastas
        pastas_clientes = sorted([p for p in pasta_base.iterdir() if p.is_dir()])
        
        if n_clientes == 'all':
            pastas_selecionadas = pastas_clientes
        else:
            try:
                limite = int(n_clientes)
                pastas_selecionadas = pastas_clientes[:limite]
            except ValueError:
                print(f"❌ Valor inválido para n_clientes: {n_clientes}")
                return
        
        print(f"📂 Encontradas {len(pastas_clientes)} pastas no total")
        print(f"🎯 Processando {len(pastas_selecionadas)} pastas\n")
        
        # Processa cada pasta
        for idx, cliente_obra_dir in enumerate(pastas_selecionadas, 1):
            if not cliente_obra_dir.is_dir():
                continue
            
            nome_pasta = cliente_obra_dir.name
            
            # Verifica separador
            if ' - ' not in nome_pasta:
                print(f"⚠️ [{idx}/{len(pastas_selecionadas)}] Pasta ignorada: {nome_pasta}")
                continue
            
            # Extrai cliente e obra
            partes = nome_pasta.split(' - ', 1)
            nome_cliente = partes[0].strip()
            nome_obra = partes[1].strip() if len(partes) > 1 else ''
            
            print(f"\n📁 [{idx}/{len(pastas_selecionadas)}] Processando: {nome_cliente} - {nome_obra}")
            
            # ========================================
            # 1. CLIENTE (sempre seguro)
            # ========================================
            cliente_id, cliente_novo = get_cliente_id(cursor, nome_cliente)
            if cliente_novo:
                stats['clientes_novos'] += 1
                print(f"   ✅ Cliente NOVO: '{nome_cliente}' (ID: {cliente_id})")
            else:
                stats['clientes_existentes'] += 1
                print(f"   ♻️  Cliente EXISTENTE: '{nome_cliente}' (ID: {cliente_id})")
            
            # ========================================
            # 2. OBRA (sempre seguro)
            # ========================================
            obra_id, obra_nova = get_obra_id(cursor, cliente_id, nome_obra)
            if obra_nova:
                stats['obras_novas'] += 1
                print(f"   📂 Obra NOVA: '{nome_obra}' (ID: {obra_id})")
            else:
                stats['obras_existentes'] += 1
                print(f"   ♻️  Obra EXISTENTE: '{nome_obra}' (ID: {obra_id})")
            
            # ========================================
            # 3. REGISTROS
            # ========================================
            registros = [p for p in cliente_obra_dir.iterdir() if p.is_dir()]
            
            for registro_dir in registros:
                nome_registro = registro_dir.name
                
                # Busca ou cria registro
                registro_id, registro_novo = get_registro_id(cursor, obra_id, nome_registro)
                if registro_novo:
                    stats['registros_novos'] += 1
                    print(f"      📸 Registro NOVO: '{nome_registro}' (ID: {registro_id})")
                else:
                    stats['registros_existentes'] += 1
                    print(f"      ♻️  Registro EXISTENTE: '{nome_registro}' (ID: {registro_id})")
                
                # ========================================
                # 4. FOTOS (com verificação de duplicata)
                # ========================================
                arquivos = [p for p in registro_dir.iterdir() if p.is_file()]
                extensoes_validas = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                
                fotos_no_registro = 0
                for arquivo in arquivos:
                    if arquivo.suffix.lower() not in extensoes_validas:
                        continue
                    
                    nome_arquivo = arquivo.name
                    caminho_relativo = str(cliente_obra_dir.name) + '/' + str(registro_dir.name) + '/' + nome_arquivo
                    
                    # VERIFICA SE A FOTO JÁ EXISTE
                    if foto_existe(cursor, registro_id, nome_arquivo, caminho_relativo):
                        stats['fotos_duplicadas'] += 1
                        print(f"         ⏭️  Foto duplicada (ignorada): '{nome_arquivo}'")
                        continue
                    
                    # Insere a foto (só se não existir)
                    cursor.execute("""
                        INSERT INTO fotos (registro_id, nome_arquivo, caminho, data_upload)
                        VALUES (?, ?, ?, ?)
                    """, (registro_id, nome_arquivo, caminho_relativo, datetime.now()))
                    
                    conn.commit()
                    stats['fotos_novas'] += 1
                    fotos_no_registro += 1
                
                if fotos_no_registro > 0:
                    print(f"         🖼️  {fotos_no_registro} foto(s) NOVA(S) registrada(s)")
        
        # ========================================
        # COMMIT FINAL
        # ========================================
        conn.commit()
        
        # ========================================
        # RESUMO FINAL
        # ========================================
        print("\n" + "=" * 70)
        print("✅ MIGRAÇÃO CONCLUÍDA!")
        
        print(f"\n📊 Resumo da execução:")
        print(f"   🆕 Clientes novos: {stats['clientes_novos']}")
        print(f"   ♻️  Clientes existentes: {stats['clientes_existentes']}")
        print(f"   🆕 Obras novas: {stats['obras_novas']}")
        print(f"   ♻️  Obras existentes: {stats['obras_existentes']}")
        print(f"   🆕 Registros novos: {stats['registros_novos']}")
        print(f"   ♻️  Registros existentes: {stats['registros_existentes']}")
        print(f"   🆕 Fotos novas: {stats['fotos_novas']}")
        print(f"   ⏭️  Fotos duplicadas (ignoradas): {stats['fotos_duplicadas']}")
        
        # Estatísticas totais do banco
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes_db = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM obras")
        total_obras_db = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM registros")
        total_registros_db = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM fotos")
        total_fotos_db = cursor.fetchone()[0]
        
        print(f"\n📈 Totais no banco de dados:")
        print(f"   Total de clientes: {total_clientes_db}")
        print(f"   Total de obras: {total_obras_db}")
        print(f"   Total de registros: {total_registros_db}")
        print(f"   Total de fotos: {total_fotos_db}")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

# ============================================
# MAIN - PROCESSAR ARGUMENTOS
# ============================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Migrar fotos para o banco de dados SQLite (SEM DUPLICATAS)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python migrar.py -n_clientes 1      # Processa 1 cliente (TESTE)
  python migrar.py -n_clientes 5      # Processa 5 clientes
  python migrar.py -n_clientes all    # Processa TODOS os clientes

🛡️  Proteção contra duplicatas:
   - Clientes: verifica por nome (UNIQUE)
   - Obras: verifica por cliente_id + nome
   - Registros: verifica por obra_id + nome_quadro
   - Fotos: verifica por registro_id + nome_arquivo + caminho
        '''
    )
    
    parser.add_argument(
        '-n_clientes',
        type=str,
        required=True,
        help='Número de clientes a processar (inteiro ou "all")'
    )
    
    args = parser.parse_args()
    
    print("🚀 INICIANDO MIGRAÇÃO (MODO SEGURO SEM DUPLICATAS)")
    print("=" * 70)
    
    # Valida o argumento
    if args.n_clientes != 'all':
        try:
            n = int(args.n_clientes)
            if n <= 0:
                print("❌ O número de clientes deve ser maior que 0")
                exit(1)
        except ValueError:
            print(f"❌ Valor inválido: {args.n_clientes}. Use um número inteiro ou 'all'")
            exit(1)
    
    # Executa a migração
    migrar_dados(args.n_clientes)
    
    print("\n" + "=" * 70)
    print("🏁 FIM")