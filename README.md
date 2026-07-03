# Sistema de Registro Fotográfico - Quadros Elétricos

Sistema web desenvolvido em Flask para organizar o registro fotográfico de quadros elétricos montados. Ele resolve o problema manual de recebimento e organização de fotos, automatizando a criação da estrutura de pastas.

## Tecnologias

- Python 3.12+
- Flask
- Flask-SQLAlchemy (SQLite)
- Bootstrap 5 (Vanilla CSS/JS)

## Estrutura de Diretórios
As imagens são organizadas automaticamente no servidor seguindo o padrão:
`storage/Nome_Cliente/Nome_Quadro/`

## Instalação e Execução

### 1. Criar e ativar o ambiente virtual (venv)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/MacOS
source venv/bin/activate
```

### 2. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 3. Executar a aplicação
O banco de dados (`instance/app.db`) e a pasta de armazenamento (`storage/`) serão criados automaticamente na primeira execução.
```bash
python run.py
```

Acesse no seu navegador: `http://localhost:5000`

## Arquitetura e Decisões de Design

* **Separação de Responsabilidades**: As rotas (`app/routes.py`) delegam as regras de negócio para os Services (`app/services.py`).
* **Estrutura Modular**: Uso de Flask Blueprints para permitir o crescimento do sistema.
* **Sanitização**: Nomes de clientes e quadros são sanitizados para evitar problemas em nomes de pastas no sistema operacional.
* **Segurança na Sobrescrita**: Verifica se um arquivo já existe no destino. Se sim, adiciona um contador no final do arquivo.

## Sugestões para Próximas Versões

1. **Autenticação e Autorização**: Adicionar sistema de login (Flask-Login) para que apenas usuários autorizados consigam ver/inserir dados.
2. **Compressão de Imagens**: Processar a imagem no upload (ex: usando a biblioteca Pillow) para reduzir resolução e consumo de disco, gerando thumbnails para exibição mais rápida.
3. **Armazenamento em Nuvem**: Mudar o serviço de `storage` para salvar no AWS S3 ou equivalente.
4. **Exportação / PDF**: Gerar relatório automático em PDF consolidando os dados do quadro e anexando as fotos (report técnico).
