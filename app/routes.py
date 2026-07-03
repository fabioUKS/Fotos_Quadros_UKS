from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, jsonify
from app.services import ClienteService, RegistroService, ObraService
from app.models import Cliente, RegistroFotografico, Foto
import os

main_bp = Blueprint('main', __name__)
clientes_bp = Blueprint('clientes', __name__)
registros_bp = Blueprint('registros', __name__)

@main_bp.route('/')
def index():
    qtd_clientes = Cliente.query.count()
    qtd_registros = RegistroFotografico.query.count()
    qtd_fotos = Foto.query.count()
    return render_template('index.html', qtd_clientes=qtd_clientes, qtd_registros=qtd_registros, qtd_fotos=qtd_fotos)

@main_bp.route('/storage/<path:filename>')
def serve_storage(filename):
    """Serve images from the storage directory."""
    storage_folder = current_app.config['STORAGE_FOLDER']
    return send_from_directory(storage_folder, filename)

@clientes_bp.route('/')
def listar():
    clientes = ClienteService.listar_clientes()
    return render_template('clientes.html', clientes=clientes)

@clientes_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        nome = request.form.get('nome')
        try:
            ClienteService.criar_cliente(nome)
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('clientes.listar'))
        except ValueError as e:
            flash(str(e), 'danger')
            
    return render_template('novo_cliente.html')

@clientes_bp.route('/<int:id>')
def visualizar(id):
    cliente = ClienteService.get_cliente(id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes.listar'))
    
    obras = ObraService.listar_obras_por_cliente(id)
    return render_template('visualizar_cliente.html', cliente=cliente, obras=obras)

@clientes_bp.route('/<int:id>/obras/nova', methods=['GET', 'POST'])
def nova_obra(id):
    cliente = ClienteService.get_cliente(id)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes.listar'))
        
    if request.method == 'POST':
        nome = request.form.get('nome')
        try:
            ObraService.criar_obra(id, nome)
            flash('Obra cadastrada com sucesso!', 'success')
            return redirect(url_for('clientes.visualizar', id=id))
        except ValueError as e:
            flash(str(e), 'danger')
            
    return render_template('nova_obra.html', cliente=cliente)

@clientes_bp.route('/<int:id>/obras/api')
def api_listar_obras(id):
    obras = ObraService.listar_obras_por_cliente(id)
    return jsonify([{'id': o.id, 'nome': o.nome} for o in obras])

@registros_bp.route('/')
def listar():
    registros = RegistroService.listar_registros()
    return render_template('registros.html', registros=registros)

@registros_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        obra_id = request.form.get('obra_id')
        nome_quadro = request.form.get('nome_quadro')
        arquivos = request.files.getlist('fotos')
        
        try:
            if not obra_id:
                raise ValueError("Selecione uma obra.")
            RegistroService.criar_registro(int(obra_id), nome_quadro, arquivos)
            flash('Registro criado com sucesso!', 'success')
            return redirect(url_for('registros.listar'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f"Erro ao processar upload: {str(e)}", 'danger')
            
    clientes = ClienteService.listar_clientes()
    return render_template('novo_registro.html', clientes=clientes)

@registros_bp.route('/<int:id>')
def visualizar(id):
    registro = RegistroService.get_registro(id)
    if not registro:
        flash('Registro não encontrado.', 'danger')
        return redirect(url_for('registros.listar'))
    return render_template('visualizar_registro.html', registro=registro)
