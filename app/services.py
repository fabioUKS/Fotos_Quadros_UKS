import os
from typing import List
from werkzeug.datastructures import FileStorage
from flask import current_app
from app import db
from app.models import Cliente, Obra, RegistroFotografico, Foto
from app.utils import sanitize_directory_name, sanitize_filename

class ClienteService:
    @staticmethod
    def criar_cliente(nome: str) -> Cliente:
        if not nome or not nome.strip():
            raise ValueError("O nome do cliente não pode estar vazio.")
        
        # Check if already exists
        existente = Cliente.query.filter_by(nome=nome.strip()).first()
        if existente:
            raise ValueError("Já existe um cliente com este nome.")
            
        cliente = Cliente(nome=nome.strip())
        db.session.add(cliente)
        db.session.commit()
        return cliente
        
    @staticmethod
    def listar_clientes() -> List[Cliente]:
        return Cliente.query.order_by(Cliente.nome).all()
        
    @staticmethod
    def get_cliente(cliente_id: int) -> Cliente:
        return Cliente.query.get(cliente_id)

class ObraService:
    @staticmethod
    def criar_obra(cliente_id: int, nome: str) -> Obra:
        if not nome or not nome.strip():
            raise ValueError("O nome da obra não pode estar vazio.")
            
        cliente = ClienteService.get_cliente(cliente_id)
        if not cliente:
            raise ValueError("Cliente não encontrado.")
            
        existente = Obra.query.filter_by(cliente_id=cliente.id, nome=nome.strip()).first()
        if existente:
            raise ValueError("Este cliente já possui uma obra com este nome.")
            
        obra = Obra(cliente_id=cliente.id, nome=nome.strip())
        db.session.add(obra)
        db.session.commit()
        return obra

    @staticmethod
    def listar_obras_por_cliente(cliente_id: int) -> List[Obra]:
        return Obra.query.filter_by(cliente_id=cliente_id).order_by(Obra.nome).all()

    @staticmethod
    def get_obra(obra_id: int) -> Obra:
        return Obra.query.get(obra_id)


class RegistroService:
    @staticmethod
    def criar_registro(obra_id: int, nome_quadro: str, arquivos: List[FileStorage]) -> RegistroFotografico:
        obra = ObraService.get_obra(obra_id)
        if not obra:
            raise ValueError("Obra não encontrada.")
            
        cliente = obra.cliente
            
        if not nome_quadro or not nome_quadro.strip():
            raise ValueError("O nome do quadro não pode estar vazio.")
            
        # Filtrar arquivos válidos
        arquivos_validos = [f for f in arquivos if f and f.filename]
        if not arquivos_validos:
            raise ValueError("Nenhuma imagem selecionada para upload.")
            
        # Cria o registro no banco
        registro = RegistroFotografico(obra_id=obra.id, nome_quadro=nome_quadro.strip())
        db.session.add(registro)
        db.session.flush() # Para pegar o ID do registro
        
        # Estruturar o diretório
        storage_folder = current_app.config['STORAGE_FOLDER']
        nome_pasta = sanitize_directory_name(f"{cliente.nome} - {obra.nome}")
        quadro_dir = sanitize_directory_name(registro.nome_quadro)
        
        # Se os nomes sanitizados ficarem vazios, use um fallback
        if not nome_pasta: nome_pasta = f"cliente_{cliente.id}_obra_{obra.id}"
        if not quadro_dir: quadro_dir = f"quadro_{registro.id}"
        
        target_dir = os.path.join(storage_folder, nome_pasta, quadro_dir)
        os.makedirs(target_dir, exist_ok=True)
        
        # Salvar os arquivos e criar registros na tabela Foto
        for arquivo in arquivos_validos:
            original_filename = sanitize_filename(arquivo.filename)
            nome, ext = os.path.splitext(original_filename)
            
            # Garantir que não sobrescreva
            final_filename = original_filename
            caminho_completo = os.path.join(target_dir, final_filename)
            counter = 1
            
            while os.path.exists(caminho_completo):
                final_filename = f"{nome}_{counter}{ext}"
                caminho_completo = os.path.join(target_dir, final_filename)
                counter += 1
                
            # Salvar no disco
            arquivo.save(caminho_completo)
            
            # Caminho relativo para facilitar a exibição/armazenamento
            caminho_relativo = os.path.join(nome_pasta, quadro_dir, final_filename).replace('\\', '/')
            
            foto = Foto(registro_id=registro.id, nome_arquivo=final_filename, caminho=caminho_relativo)
            db.session.add(foto)
            
        db.session.commit()
        return registro
        
    @staticmethod
    def listar_registros() -> List[RegistroFotografico]:
        return RegistroFotografico.query.order_by(RegistroFotografico.data_upload.desc()).all()
        
    @staticmethod
    def get_registro(registro_id: int) -> RegistroFotografico:
        return RegistroFotografico.query.get(registro_id)
