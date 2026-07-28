import io
import os
import zipfile
import pytest
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage

from app import create_app
from app.services import RegistroService
from app.models import Foto, RegistroFotografico, Obra, Cliente


# ============================================================================
# FIXTURES E MOCKS DO PYTEST
# ============================================================================

@pytest.fixture
def app(tmp_path):
    """
    Fixture que configura uma instância da aplicação Flask para os testes.
    Define a pasta de armazenamento ('STORAGE_FOLDER') para um diretório temporário
    fornecido pelo pytest (tmp_path), garantindo isolamento total do sistema de arquivos.
    """
    app = create_app()
    app.config['TESTING'] = True
    app.config['STORAGE_FOLDER'] = str(tmp_path / "storage")
    os.makedirs(app.config['STORAGE_FOLDER'], exist_ok=True)
    return app


@pytest.fixture
def app_ctx(app):
    """
    Fixture para fornecer o contexto da aplicação Flask durante a execução dos testes.
    """
    with app.app_context():
        yield app


@pytest.fixture
def mock_db(monkeypatch):
    """
    Fixture que faz o mock da sessão do SQLAlchemy (db.session).
    Substitui os métodos add, flush, commit e rollback por MagicMocks para
    permitir a inspeção de chamadas sem afetar o banco de dados real.
    """
    mock_session = MagicMock()
    # Simula a atribuição de um ID simulado ao registrar um RegistroFotografico
    def mock_add(obj):
        if isinstance(obj, RegistroFotografico) and not hasattr(obj, 'id'):
            obj.id = 1
        elif isinstance(obj, Foto) and not hasattr(obj, 'id'):
            obj.id = 100
    mock_session.add.side_effect = mock_add
    
    monkeypatch.setattr("app.services.db.session", mock_session)
    return mock_session


@pytest.fixture
def mock_obra():
    """
    Fixture que retorna um mock completo de uma Obra vinculada a um Cliente.
    """
    cliente = MagicMock(spec=Cliente)
    cliente.id = 1
    cliente.nome = "Cliente Teste"

    obra = MagicMock(spec=Obra)
    obra.id = 10
    obra.nome = "Obra Teste"
    obra.cliente = cliente
    return obra


def helper_criar_zip_in_memory(files_dict: dict, filename: str = "fotos.zip") -> FileStorage:
    """
    Função auxiliar que cria um arquivo ZIP em memória utilizando io.BytesIO.
    
    :param files_dict: Dicionário onde a chave é o caminho interno do arquivo no ZIP 
                       e o valor são os bytes do conteúdo do arquivo.
                       Exemplo: {"foto1.jpg": b"dados_imagem", "subpasta/foto2.png": b"dados"}
    :param filename: Nome do arquivo ZIP simulado.
    :return: Uma instância de FileStorage pronta para ser enviada aos serviços.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for inner_path, content in files_dict.items():
            zf.writestr(inner_path, content)
    buffer.seek(0)
    return FileStorage(stream=buffer, filename=filename, content_type='application/zip')


# ============================================================================
# CENÁRIOS DE TESTE
# ============================================================================

def test_upload_zip_caminho_feliz(app_ctx, mock_db, mock_obra, tmp_path):
    """
    Cenário 1: Caminho Feliz (Happy Path)
    - Envia um ZIP contendo 3 imagens válidas (.jpg, .png, .jpeg).
    - Valida se as 3 imagens foram descompactadas e salvas na pasta de destino.
    - Valida se `db.session.add` foi chamado para o Registro e para as 3 Fotos (total 4 chamadas).
    """
    # 1. Preparação dos dados
    arquivos_zip = {
        "foto1.jpg": b"conteudo_foto_1",
        "foto2.png": b"conteudo_foto_2",
        "foto3.jpeg": b"conteudo_foto_3"
    }
    zip_storage = helper_criar_zip_in_memory(arquivos_zip, "imagens.zip")
    
    with patch("app.services.ObraService.get_obra", return_value=mock_obra):
        # 2. Execução da função sob teste
        registro = RegistroService.criar_registro(
            obra_id=mock_obra.id,
            nome_quadro="Quadro Sala",
            arquivos=[zip_storage]
        )

    # 3. Verificações
    assert registro is not None
    assert registro.nome_quadro == "Quadro Sala"
    
    # Pasta esperada para os arquivos salvos
    target_dir = os.path.join(app_ctx.config['STORAGE_FOLDER'], "Cliente Teste - Obra Teste", "Quadro Sala")
    assert os.path.exists(target_dir)
    
    # Verificar se as 3 imagens físicas foram gravadas no disco
    salvos = os.listdir(target_dir)
    assert len(salvos) == 3
    assert set(salvos) == {"foto1.jpg", "foto2.png", "foto3.jpeg"}
    
    # Verificar chamadas ao banco de dados: 1 RegistroFotografico + 3 Fotos = 4 add calls
    assert mock_db.add.call_count == 4
    
    # Garantir que commit foi chamado no final
    mock_db.commit.assert_called_once()


def test_upload_zip_ignorar_arquivos_invalidos(app_ctx, mock_db, mock_obra):
    """
    Cenário 2: Ignorar Arquivos Inválidos
    - Envia um ZIP com imagens válidas, mas contendo também um arquivo oculto (.DS_Store) 
      e um arquivo zip aninhado (sub_archive.zip).
    - Valida se o sistema ignora os arquivos inválidos e salva apenas as imagens.
    """
    arquivos_zip = {
        "foto_valida1.jpg": b"imagem_1",
        "foto_valida2.png": b"imagem_2",
        ".DS_Store": b"dados_do_mac_os",
        "sub_archive.zip": b"zip_dentro_de_zip"
    }
    zip_storage = helper_criar_zip_in_memory(arquivos_zip, "pacote_misto.zip")
    
    with patch("app.services.ObraService.get_obra", return_value=mock_obra):
        RegistroService.criar_registro(
            obra_id=mock_obra.id,
            nome_quadro="Quadro Varanda",
            arquivos=[zip_storage]
        )

    target_dir = os.path.join(app_ctx.config['STORAGE_FOLDER'], "Cliente Teste - Obra Teste", "Quadro Varanda")
    salvos = os.listdir(target_dir)
    
    # Apenas as 2 fotos válidas devem ter sido salvas
    assert len(salvos) == 2
    assert set(salvos) == {"foto_valida1.jpg", "foto_valida2.png"}
    assert ".DS_Store" not in salvos
    assert "sub_archive.zip" not in salvos
    
    # Calls do db.session.add: 1 Registro + 2 Fotos = 3 chamadas
    assert mock_db.add.call_count == 3


def test_upload_zip_colisao_de_nomes(app_ctx, mock_db, mock_obra):
    """
    Cenário 3: Colisão de Nomes
    - O diretório de destino já contém uma imagem chamada 'foto.jpg'.
    - O ZIP enviado também contém uma imagem 'foto.jpg'.
    - Valida se o sistema salva o novo arquivo renomeado como 'foto_1.jpg'.
    """
    target_dir = os.path.join(app_ctx.config['STORAGE_FOLDER'], "Cliente Teste - Obra Teste", "Quadro Quarto")
    os.makedirs(target_dir, exist_ok=True)
    
    # Criar um arquivo pré-existente no destino com nome 'foto.jpg'
    arquivo_existente = os.path.join(target_dir, "foto.jpg")
    with open(arquivo_existente, "wb") as f:
        f.write(b"conteudo_existente")
        
    # Preparar ZIP contendo arquivo de mesmo nome
    arquivos_zip = {
        "foto.jpg": b"novo_conteudo_do_zip"
    }
    zip_storage = helper_criar_zip_in_memory(arquivos_zip, "upload_repetido.zip")
    
    with patch("app.services.ObraService.get_obra", return_value=mock_obra):
        RegistroService.criar_registro(
            obra_id=mock_obra.id,
            nome_quadro="Quadro Quarto",
            arquivos=[zip_storage]
        )

    # Verificar que o diretório agora tem 2 arquivos: 'foto.jpg' original e 'foto_1.jpg'
    salvos = os.listdir(target_dir)
    assert len(salvos) == 2
    assert set(salvos) == {"foto.jpg", "foto_1.jpg"}
    
    # Garantir que o conteúdo do foto_1.jpg é o novo conteúdo do ZIP
    with open(os.path.join(target_dir, "foto_1.jpg"), "rb") as f:
        assert f.read() == b"novo_conteudo_do_zip"


def test_upload_zip_extracao_subpastas_achatamento(app_ctx, mock_db, mock_obra):
    """
    Cenário 4: Extração de Subpastas (Achatamento / Flat Structure)
    - O ZIP contém imagens organizadas dentro de subpastas aninhadas.
    - Valida se o sistema varre recursivamente (via os.walk) e salva todas as fotos 
      na raiz do diretório de destino (estrutura achatada).
    """
    arquivos_zip = {
        "pasta1/foto_a.jpg": b"foto_a",
        "pasta1/subpasta2/foto_b.png": b"foto_b",
        "pasta2/foto_c.jpeg": b"foto_c"
    }
    zip_storage = helper_criar_zip_in_memory(arquivos_zip, "estruturado.zip")
    
    with patch("app.services.ObraService.get_obra", return_value=mock_obra):
        RegistroService.criar_registro(
            obra_id=mock_obra.id,
            nome_quadro="Quadro Cozinha",
            arquivos=[zip_storage]
        )

    target_dir = os.path.join(app_ctx.config['STORAGE_FOLDER'], "Cliente Teste - Obra Teste", "Quadro Cozinha")
    salvos = os.listdir(target_dir)
    
    # Todas as 3 fotos devem estar na raiz da pasta de destino do quadro
    assert len(salvos) == 3
    assert set(salvos) == {"foto_a.jpg", "foto_b.png", "foto_c.jpeg"}
    
    # 1 Registro + 3 Fotos = 4 chamadas no db.session.add
    assert mock_db.add.call_count == 4


def test_upload_zip_vazio_ou_corrompido(app_ctx, mock_db, mock_obra):
    """
    Cenário 5: ZIP Vazio ou Corrompido
    - 5A: Envia um arquivo com extensão .zip contendo bytes arbitrários e inválidos.
          Deve lançar zipfile.BadZipFile.
    - 5B: Envia um arquivo ZIP válido porém sem nenhum arquivo dentro.
          Não deve criar nenhuma imagem no disco nem registrar Fotos no banco.
    """
    # --- Teste 5A: ZIP Corrompido ---
    buffer_corrompido = io.BytesIO(b"conteudo_invalido_que_nao_e_zip")
    zip_corrompido = FileStorage(stream=buffer_corrompido, filename="invalido.zip", content_type="application/zip")
    
    with patch("app.services.ObraService.get_obra", return_value=mock_obra):
        with pytest.raises(zipfile.BadZipFile):
            RegistroService.criar_registro(
                obra_id=mock_obra.id,
                nome_quadro="Quadro Corrompido",
                arquivos=[zip_corrompido]
            )
            
    # --- Teste 5B: ZIP Vazio ---
    mock_db.reset_mock()
    zip_vazio = helper_criar_zip_in_memory({}, "vazio.zip")
    
    with patch("app.services.ObraService.get_obra", return_value=mock_obra):
        registro = RegistroService.criar_registro(
            obra_id=mock_obra.id,
            nome_quadro="Quadro Vazio",
            arquivos=[zip_vazio]
        )

    target_dir = os.path.join(app_ctx.config['STORAGE_FOLDER'], "Cliente Teste - Obra Teste", "Quadro Vazio")
    salvos = os.listdir(target_dir)
    
    # Nenhuma foto salva
    assert len(salvos) == 0
    # Apenas 1 chamada no db.session.add (para o objeto RegistroFotografico)
    assert mock_db.add.call_count == 1
    assert registro is not None
