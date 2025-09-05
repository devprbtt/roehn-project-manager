from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# Adicione estas importações no início do arquivo
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from roehn_converter import RoehnProjectConverter
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine
import uuid
import io
import csv
import io
import json
import re
import os
from datetime import datetime
from database import db, User, Projeto, Area, Ambiente, Circuito, Modulo, Vinculacao

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projetos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-muito-longa-aqui-altere-para-uma-chave-segura'

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

db.init_app(app)

# Informações sobre os módulos
MODULO_INFO = {
    'RL12': {'nome_completo': 'ADP-RL12', 'canais': 12, 'tipos_permitidos': ['luz']},
    'RL4': {'nome_completo': 'AQL-GV-RL4', 'canais': 4, 'tipos_permitidos': ['luz']},
    'LX4': {'nome_completo': 'ADP-LX4', 'canais': 4, 'tipos_permitidos': ['persiana']},
    'SA1': {'nome_completo': 'AQL-GV-SA1', 'canais': 1, 'tipos_permitidos': ['hvac']},
    'DIM8': {'nome_completo': 'ADP-DIM8', 'canais': 8, 'tipos_permitidos': ['luz']}
}

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass

# Carregador de usuário para o Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Criar tabelas e usuário admin padrão
with app.app_context():
    db.create_all()
    # Criar usuário admin padrão se não existir
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@empresa.com', role='admin')
        admin_user.set_password('admin123')  # Senha padrão - deve ser alterada após o primeiro login
        db.session.add(admin_user)
        db.session.commit()

@app.route('/roehn/import', methods=['POST'])
@login_required
def roehn_import():
    # Verificar se há um projeto selecionado
    projeto_atual_id = session.get('projeto_atual_id')
    if not projeto_atual_id:
        flash('Nenhum projeto selecionado. Selecione ou crie um projeto primeiro.', 'warning')
        return redirect(url_for('index'))
    
    projeto = Projeto.query.get(projeto_atual_id)
    if not projeto:
        flash('Projeto não encontrado.', 'danger')
        return redirect(url_for('index'))
    
    # Processar formulário de importação
    project_info = {
        'project_name': request.form.get('project_name', projeto.nome),
        'client_name': request.form.get('client_name', ''),
        'client_email': request.form.get('client_email', ''),
        'client_phone': request.form.get('client_phone_clean', ''),
        'timezone_id': request.form.get('timezone_id', 'America/Bahia'),
        'lat': request.form.get('lat', '0.0'),
        'lon': request.form.get('lon', '0.0'),
        'tech_area': request.form.get('tech_area', 'Área Técnica'),
        'tech_room': request.form.get('tech_room', 'Sala Técnica'),
        'board_name': request.form.get('board_name', 'Quadro Elétrico'),
        'm4_ip': request.form.get('m4_ip', '192.168.0.245'),
        'm4_hsnet': request.form.get('m4_hsnet', '245'),
        'm4_devid': request.form.get('m4_devid', '1'),
        'software_version': request.form.get('software_version', '1.0.8.67'),
        'programmer_name': request.form.get('programmer_name', current_user.username),
        'programmer_email': request.form.get('programmer_email', current_user.email),
        'programmer_guid': str(uuid.uuid4()),
    }
    
    try:
        # Converter dados do projeto para Roehn
        converter = RoehnProjectConverter()
        converter.create_project(project_info)
        
        # Processar os dados do projeto atual - CORREÇÃO AQUI
        # Garantir que estamos passando o projeto completo
        converter.process_db_project(projeto)
        
        # Gerar arquivo para download
        project_json = converter.export_project()
        
        # Criar resposta para download
        output = io.BytesIO()
        output.write(project_json.encode('utf-8'))
        output.seek(0)
        
        nome_arquivo = f"{project_info['project_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.rwp"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/json'
        )
        
    except Exception as e:
        # Capturar informações detalhadas do erro
        import traceback
        error_traceback = traceback.format_exc()
        app.logger.error(f"Erro durante a geração do projeto: {str(e)}")
        app.logger.error(f"Traceback: {error_traceback}")
        
        flash(f'Erro durante a geração do projeto: {str(e)}. Verifique os logs para mais detalhes.', 'danger')
        return redirect(url_for('roehn_import'))

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Apenas administradores podem criar novos usuários
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem criar usuários.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email já está em uso', 'danger')
        else:
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Usuário criado com sucesso', 'success')
            return redirect(url_for('manage_users'))
    
    return render_template('register.html')

@app.route('/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem gerenciar usuários.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    if current_user.id == user_id:
        return jsonify({'success': False, 'message': 'Você não pode excluir sua própria conta'})
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Usuário excluído com sucesso'})

# Middleware para verificar projeto selecionado
@app.before_request
def check_projeto_selecionado():
    # Rotas que não requerem projeto selecionado
    if request.endpoint in ['login', 'logout', 'register', 'manage_users', 'delete_user', 'static']:
        return
    
    # Verificar se o usuário está autenticado
    if not current_user.is_authenticated:
        return
    
    # Verificar se há projeto selecionado para rotas que precisam
    if request.endpoint in ['areas', 'ambientes', 'circuitos', 'modulos', 'vinculacao', 'projeto', 'exportar_csv']:
        if 'projeto_atual_id' not in session:
            flash('Selecione ou crie um projeto para continuar', 'warning')
            return redirect(url_for('index'))

# Rotas principais da aplicação
@app.route('/')
@login_required
def index():
    # Buscar apenas projetos do usuário atual (ou todos se for admin)
    if current_user.role == 'admin':
        projetos = Projeto.query.all()
    else:
        projetos = Projeto.query.filter_by(user_id=current_user.id).all()
        
    projeto_atual_id = session.get('projeto_atual_id')
    projeto_atual_nome = session.get('projeto_atual_nome', '')
    return render_template('index.html', projetos=projetos, projeto_atual_id=projeto_atual_id, projeto_atual_nome=projeto_atual_nome)

@app.route('/projeto/<int:projeto_id>')
@login_required
def selecionar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem acesso ao projeto
    if projeto.user_id != current_user.id and current_user.role != 'admin':
        flash('Acesso negado a este projeto', 'danger')
        return redirect(url_for('index'))
    
    session['projeto_atual_id'] = projeto.id
    session['projeto_atual_nome'] = projeto.nome
    return redirect(url_for('index'))

@app.route('/projeto/novo', methods=['POST'])
@login_required
def novo_projeto():
    nome = request.form.get('nome')
    
    if not nome:
        return jsonify({'success': False, 'message': 'Nome do projeto é obrigatório'})
    
    projeto_existente = Projeto.query.filter_by(nome=nome).first()
    if projeto_existente:
        return jsonify({'success': False, 'message': 'Já existe um projeto com esse nome'})
    
    novo_projeto = Projeto(nome=nome, user_id=current_user.id)
    db.session.add(novo_projeto)
    db.session.commit()
    
    session['projeto_atual_id'] = novo_projeto.id
    session['projeto_atual_nome'] = novo_projeto.nome
    
    return jsonify({'success': True, 'id': novo_projeto.id})

@app.route('/projeto/<int:projeto_id>', methods=['DELETE'])
@login_required
def excluir_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem permissão para excluir o projeto
    if projeto.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    db.session.delete(projeto)
    db.session.commit()
    
    if session.get('projeto_atual_id') == projeto_id:
        session.pop('projeto_atual_id', None)
        session.pop('projeto_atual_nome', None)
    
    return jsonify({'success': True})

@app.route('/areas', methods=['GET', 'POST'])
@login_required
def areas():
    projeto_atual_id = session.get('projeto_atual_id')
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        
        # Verificar se já existe área com esse nome no projeto atual
        area_existente = Area.query.filter_by(nome=nome, projeto_id=projeto_atual_id).first()
        if area_existente:
            return jsonify({'success': False, 'message': 'Já existe uma área com esse nome neste projeto'})
        
        nova_area = Area(nome=nome, projeto_id=projeto_atual_id)
        db.session.add(nova_area)
        db.session.commit()
        return jsonify({'success': True, 'id': nova_area.id})
    
    areas = Area.query.filter_by(projeto_id=projeto_atual_id).all()
    return render_template('areas.html', areas=areas)

@app.route('/areas/<int:id>', methods=['DELETE'])
@login_required
def excluir_area(id):
    area = Area.query.get_or_404(id)
    
    # Verificar se a área pertence ao projeto atual
    if area.projeto_id != session.get('projeto_atual_id'):
        return jsonify({'success': False, 'message': 'Área não pertence ao projeto atual'})
    
    # Verificar se a área tem ambientes
    if area.ambientes:
        return jsonify({'success': False, 'message': 'Não é possível excluir área com ambientes vinculados'})
    
    db.session.delete(area)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/ambientes', methods=['GET', 'POST'])
@login_required
def ambientes():
    projeto_atual_id = session.get('projeto_atual_id')
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        area_id = request.form.get('area_id')
        
        # Verificar se a área pertence ao projeto atual
        area = Area.query.get(area_id)
        if not area or area.projeto_id != projeto_atual_id:
            return jsonify({'success': False, 'message': 'Área inválida'})
        
        # Verificar se já existe ambiente com esse nome na mesma área
        ambiente_existente = Ambiente.query.filter_by(nome=nome, area_id=area_id).first()
        if ambiente_existente:
            return jsonify({'success': False, 'message': 'Já existe um ambiente com esse nome nesta área'})
        
        novo_ambiente = Ambiente(nome=nome, area_id=area_id)
        db.session.add(novo_ambiente)
        db.session.commit()
        return jsonify({'success': True, 'id': novo_ambiente.id})
    
    # Buscar apenas áreas do projeto atual
    areas = Area.query.filter_by(projeto_id=projeto_atual_id).all()
    ambientes = Ambiente.query.join(Area).filter(Area.projeto_id == projeto_atual_id).all()
    return render_template('ambientes.html', areas=areas, ambientes=ambientes)

@app.route('/ambientes/<int:id>', methods=['DELETE'])
@login_required
def excluir_ambiente(id):
    ambiente = Ambiente.query.get_or_404(id)
    
    # Verificar se o ambiente pertence ao projeto atual
    if ambiente.area.projeto_id != session.get('projeto_atual_id'):
        return jsonify({'success': False, 'message': 'Ambiente não pertence ao projeto atual'})
    
    # Verificar se o ambiente tem circuitos
    if ambiente.circuitos:
        return jsonify({'success': False, 'message': 'Não é possível excluir ambiente com circuitos vinculados'})
    
    db.session.delete(ambiente)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/circuitos', methods=['GET', 'POST'])
@login_required
def circuitos():
    projeto_atual_id = session.get('projeto_atual_id')
    
    if request.method == 'POST':
        identificador = request.form.get('identificador')
        nome = request.form.get('nome')
        tipo = request.form.get('tipo')
        ambiente_id = request.form.get('ambiente_id')
        
        # Verificar se o ambiente pertence ao projeto atual
        ambiente = Ambiente.query.get(ambiente_id)
        if not ambiente or ambiente.area.projeto_id != projeto_atual_id:
            return jsonify({'success': False, 'message': 'Ambiente inválido'})
        
        # Verificar se já existe circuito com esse identificador no mesmo ambiente
        circuito_existente = Circuito.query.filter_by(identificador=identificador, ambiente_id=ambiente_id).first()
        if circuito_existente:
            return jsonify({'success': False, 'message': 'Já existe um circuito com esse identificador neste ambiente'})
        
        # Para circuitos HVAC, não gerar SAK
        if tipo == 'hvac':
            sak = None
            quantidade_saks = 0
        else:
            # Determinar quantidade de SAKs baseada no tipo
            if tipo == 'persiana':
                quantidade_saks = 2
            else:
                quantidade_saks = 1
            
            # Encontrar o último SAK usado
            ultimo_circuito = Circuito.query.join(Ambiente).join(Area).filter(
                Area.projeto_id == projeto_atual_id,
                Circuito.tipo != 'hvac'
            ).order_by(Circuito.sak.desc()).first()
            
            # Calcular o próximo SAK disponível
            if ultimo_circuito:
                # Para persianas, precisamos de 2 SAKs consecutivos
                if tipo == 'persiana':
                    # Verificar se o próximo SAK está livre
                    sak_disponivel = ultimo_circuito.sak + ultimo_circuito.quantidade_saks
                    # Garantir que temos 2 SAKs consecutivos livres
                    circuito_com_sak_seguinte = Circuito.query.filter_by(sak=sak_disponivel + 1).first()
                    if circuito_com_sak_seguinte:
                        sak_disponivel += 2  # Pular para o próximo par livre
                    sak = sak_disponivel
                else:
                    sak = ultimo_circuito.sak + ultimo_circuito.quantidade_saks
            else:
                sak = 1
        
        novo_circuito = Circuito(
            identificador=identificador,
            nome=nome,
            tipo=tipo,
            ambiente_id=ambiente_id,
            sak=sak,
            quantidade_saks=quantidade_saks
        )
        db.session.add(novo_circuito)
        db.session.commit()
        return jsonify({'success': True, 'id': novo_circuito.id})
    
    # Buscar apenas ambientes do projeto atual
    ambientes = Ambiente.query.join(Area).filter(Area.projeto_id == projeto_atual_id).all()
    circuitos = Circuito.query.join(Ambiente).join(Area).filter(Area.projeto_id == projeto_atual_id).all()
    return render_template('circuitos.html', ambientes=ambientes, circuitos=circuitos)

@app.route('/circuitos/<int:id>', methods=['DELETE'])
@login_required
def excluir_circuito(id):
    circuito = Circuito.query.get_or_404(id)
    
    # Verificar se o circuito pertence ao projeto atual
    if circuito.ambiente.area.projeto_id != session.get('projeto_atual_id'):
        return jsonify({'success': False, 'message': 'Circuito não pertence ao projeto atual'})
    
    # Verificar se o circuito tem vinculação
    if circuito.vinculacao:
        return jsonify({'success': False, 'message': 'Não é possível excluir circuito com vinculação ativa'})
    
    db.session.delete(circuito)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/modulos', methods=['GET', 'POST'])
@login_required
def modulos():
    projeto_atual_id = session.get('projeto_atual_id')
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        tipo = request.form.get('tipo')
        
        # Verificar se já existe módulo com esse nome no projeto atual
        modulo_existente = Modulo.query.filter_by(nome=nome, projeto_id=projeto_atual_id).first()
        if modulo_existente:
            return jsonify({'success': False, 'message': 'Já existe um módulo com esse nome neste projeto'})
        
        # Obter quantidade de canais do tipo selecionado
        quantidade_canais = MODULO_INFO[tipo]['canais']
        
        novo_modulo = Modulo(
            nome=nome,
            tipo=tipo,
            quantidade_canais=quantidade_canais,
            projeto_id=projeto_atual_id
        )
        db.session.add(novo_modulo)
        db.session.commit()
        return jsonify({'success': True, 'id': novo_modulo.id})
    
    # Garantir que estamos filtrando apenas módulos do projeto atual
    modulos = Modulo.query.filter_by(projeto_id=projeto_atual_id).all()
    return render_template('modulos.html', modulos=modulos, modulo_info=MODULO_INFO)

@app.route('/modulos/<int:id>', methods=['DELETE'])
@login_required
def excluir_modulo(id):
    modulo = Modulo.query.get_or_404(id)
    
    # Verificar se o módulo pertence ao projeto atual
    if modulo.projeto_id != session.get('projeto_atual_id'):
        return jsonify({'success': False, 'message': 'Módulo não pertence ao projeto atual'})
    
    # Verificar se o módulo tem vinculações
    if modulo.vinculacoes:
        return jsonify({'success': False, 'message': 'Não é possível excluir módulo com vinculações ativas'})
    
    db.session.delete(modulo)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/vinculacao', methods=['GET', 'POST'])
@login_required
def vinculacao():
    projeto_atual_id = session.get('projeto_atual_id')
    
    if request.method == 'POST':
        circuito_id = request.form.get('circuito_id')
        modulo_id = request.form.get('modulo_id')
        canal = request.form.get('canal')
        
        # Verificar se o circuito pertence ao projeto atual
        circuito = Circuito.query.get(circuito_id)
        if not circuito or circuito.ambiente.area.projeto_id != projeto_atual_id:
            return jsonify({'success': False, 'message': 'Circuito inválido'})
        
        # Obter informações do módulo
        modulo = Modulo.query.get(modulo_id)
        if not modulo or modulo.projeto_id != projeto_atual_id:
            return jsonify({'success': False, 'message': 'Módulo inválido'})
        
        # Validar compatibilidade de tipos
        tipos_permitidos = MODULO_INFO[modulo.tipo]['tipos_permitidos']
        if circuito.tipo not in tipos_permitidos:
            return jsonify({'success': False, 'message': f'Circuitos do tipo {circuito.tipo} não podem ser vinculados a módulos {modulo.tipo}'})
        
        # Verificar se o canal já está em uso neste módulo
        vinculacao_existente = Vinculacao.query.filter_by(modulo_id=modulo_id, canal=canal).first()
        if vinculacao_existente:
            return jsonify({'success': False, 'message': 'Este canal já está em uso no módulo selecionado'})
        
        # Verificar se o circuito já está vinculado
        circuito_vinculado = Vinculacao.query.filter_by(circuito_id=circuito_id).first()
        if circuito_vinculado:
            return jsonify({'success': False, 'message': 'Este circuito já está vinculado a um módulo'})
        
        nova_vinculacao = Vinculacao(
            circuito_id=circuito_id,
            modulo_id=modulo_id,
            canal=canal
        )
        db.session.add(nova_vinculacao)
        db.session.commit()
        return jsonify({'success': True})
    
    # Buscar apenas circuitos não vinculados do projeto atual com informações de área e ambiente
    circuitos_nao_vinculados = (
        db.session.query(
            Circuito.id,
            Circuito.identificador,
            Circuito.nome,
            Circuito.tipo,  # <- necessário para o data-tipo do HTML
            Ambiente.nome.label('ambiente_nome'),
            Area.nome.label('area_nome'),
        )
        .select_from(Circuito)
        .join(Ambiente, Circuito.ambiente_id == Ambiente.id)
        .join(Area, Ambiente.area_id == Area.id)
        .filter(Area.projeto_id == projeto_atual_id)
        .filter(~Circuito.vinculacao.has())  # evita JOIN extra e ambiguidade
        .order_by(Area.nome, Ambiente.nome, Circuito.identificador)
        .all()
    )
    
    # Buscar vinculações com informações completas
    vinculacoes = (
        db.session.query(
            Vinculacao.id,
            Vinculacao.canal,
            Circuito.identificador,
            Circuito.nome.label('circuito_nome'),
            Ambiente.nome.label('ambiente_nome'),
            Area.nome.label('area_nome'),
            Modulo.nome.label('modulo_nome'),
            Modulo.tipo.label('modulo_tipo'),  # <- o template usa isso
        )
        .select_from(Vinculacao)
        .join(Circuito, Vinculacao.circuito_id == Circuito.id)
        .join(Ambiente, Circuito.ambiente_id == Ambiente.id)
        .join(Area, Ambiente.area_id == Area.id)
        .join(Modulo, Vinculacao.modulo_id == Modulo.id)
        .filter(Area.projeto_id == projeto_atual_id)
        .order_by(Area.nome, Ambiente.nome, Circuito.identificador, Modulo.nome, Vinculacao.canal)
        .all()
    )
    
    # Buscar apenas módulos do projeto atual
    modulos = Modulo.query.filter_by(projeto_id=projeto_atual_id).all()
    
    # Preparar informações sobre canais disponíveis por módulo
    modulos_info = []
    for modulo in modulos:
        canais_ocupados = [v.canal for v in modulo.vinculacoes]
        canais_disponiveis = [i for i in range(1, modulo.quantidade_canais + 1) if i not in canais_ocupados]
        
        modulos_info.append({
            'id': modulo.id,
            'nome': modulo.nome,
            'tipo': modulo.tipo,
            'canais_disponiveis': canais_disponiveis
        })
    
    return render_template('vinculacao.html', 
                          circuitos=circuitos_nao_vinculados, 
                          modulos=modulos_info, 
                          vinculacoes=vinculacoes)

@app.route('/vinculacao/<int:id>', methods=['DELETE'])
@login_required
def excluir_vinculacao(id):
    vinculacao = Vinculacao.query.get_or_404(id)
    
    # Verificar se a vinculação pertence ao projeto atual
    if vinculacao.circuito.ambiente.area.projeto_id != session.get('projeto_atual_id'):
        return jsonify({'success': False, 'message': 'Vinculação não pertence ao projeto atual'})
    
    db.session.delete(vinculacao)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/projeto')
@login_required
def projeto():
    projeto_atual_id = session.get('projeto_atual_id')
    areas = Area.query.filter_by(projeto_id=projeto_atual_id).all()
    return render_template('projeto.html', areas=areas)

@app.route('/exportar-csv')
@login_required
def exportar_csv():
    projeto_atual_id = session.get('projeto_atual_id')
    projeto = Projeto.query.get(projeto_atual_id)
    
    circuitos = Circuito.query.join(Ambiente).join(Area).filter(Area.projeto_id == projeto_atual_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Circuito', 'Tipo', 'Nome', 'Area', 'Ambiente', 'SAKs', 'Canal', 'Modulo', 'id Modulo'])
    
    for circuito in circuitos:
        vinculacao = Vinculacao.query.filter_by(circuito_id=circuito.id).first()
        if vinculacao:
            modulo = Modulo.query.get(vinculacao.modulo_id)
            ambiente = Ambiente.query.get(circuito.ambiente_id)
            area = Area.query.get(ambiente.area_id)
            
            # Para circuitos HVAC, mostrar vazio no campo SAK
            if circuito.tipo == 'hvac':
                sak_value = ''
            elif circuito.quantidade_saks > 1:
                sak_value = f"{circuito.sak}-{circuito.sak + circuito.quantidade_saks - 1}"
            else:
                sak_value = str(circuito.sak)
            
            writer.writerow([
                circuito.identificador,
                circuito.tipo,
                circuito.nome,
                area.nome,
                ambiente.nome,
                sak_value,
                vinculacao.canal,
                modulo.nome,
                modulo.id
            ])
    
    output.seek(0)
    
    # Obter nome do projeto para usar no nome do arquivo
    nome_projeto = projeto.nome if projeto else 'projeto'
    
    # Limpar o nome do projeto para usar no nome do arquivo
    nome_arquivo = re.sub(r'[^a-zA-Z0-9_]', '_', nome_projeto)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{nome_arquivo}_roehn.csv'
    )

@app.route('/exportar-projeto/<int:projeto_id>')
@login_required
def exportar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem acesso ao projeto
    if projeto.user_id != current_user.id and current_user.role != 'admin':
        flash('Acesso negado a este projeto', 'danger')
        return redirect(url_for('index'))
    
    # Coletar todos os dados do projeto
    projeto_data = {
        'projeto': {
            'id': projeto.id,
            'nome': projeto.nome,
            'user_id': projeto.user_id
        },
        'areas': [],
        'ambientes': [],
        'circuitos': [],
        'modulos': [],
        'vinculacoes': []
    }
    
    for area in projeto.areas:
        area_data = {
            'id': area.id,
            'nome': area.nome,
            'projeto_id': area.projeto_id
        }
        projeto_data['areas'].append(area_data)
        
        for ambiente in area.ambientes:
            ambiente_data = {
                'id': ambiente.id,
                'nome': ambiente.nome,
                'area_id': ambiente.area_id
            }
            projeto_data['ambientes'].append(ambiente_data)
            
            for circuito in ambiente.circuitos:
                circuito_data = {
                    'id': circuito.id,
                    'identificador': circuito.identificador,
                    'nome': circuito.nome,
                    'tipo': circuito.tipo,
                    'ambiente_id': circuito.ambiente_id,
                    'sak': circuito.sak
                }
                projeto_data['circuitos'].append(circuito_data)
    
    # Adicionar apenas módulos do projeto
    for modulo in Modulo.query.filter_by(projeto_id=projeto_id).all():
        modulo_data = {
            'id': modulo.id,
            'nome': modulo.nome,
            'tipo': modulo.tipo,
            'quantidade_canais': modulo.quantidade_canais
        }
        projeto_data['modulos'].append(modulo_data)
    
    for vinculacao in Vinculacao.query.all():
        # Verificar se o circuito pertence ao projeto
        circuito = Circuito.query.get(vinculacao.circuito_id)
        if circuito and circuito.ambiente.area.projeto_id == projeto_id:
            vinculacao_data = {
                'id': vinculacao.id,
                'circuito_id': vinculacao.circuito_id,
                'modulo_id': vinculacao.modulo_id,
                'canal': vinculacao.canal
            }
            projeto_data['vinculacoes'].append(vinculacao_data)
    
    # Converter para JSON
    output = io.BytesIO()
    output.write(json.dumps(projeto_data, indent=2).encode('utf-8'))
    output.seek(0)
    
    # Nome do arquivo
    nome_arquivo = f"projeto_{projeto.nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return send_file(
        output,
        mimetype='application/json',
        as_attachment=True,
        download_name=nome_arquivo
    )

@app.route('/importar-projeto', methods=['POST'])
@login_required
def importar_projeto():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    if file and file.filename.endswith('.json'):
        try:
            data = json.load(file)
            
            # Criar novo projeto - usar o nome original
            projeto_nome = data['projeto']['nome']
            novo_projeto = Projeto(nome=projeto_nome, user_id=current_user.id)
            db.session.add(novo_projeto)
            db.session.flush()  # Para obter o ID
            
            # Mapeamento de IDs antigos para novos
            area_id_map = {}
            ambiente_id_map = {}
            circuito_id_map = {}
            modulo_id_map = {}
            
            # Importar áreas
            for area_data in data['areas']:
                nova_area = Area(
                    nome=area_data['nome'],
                    projeto_id=novo_projeto.id
                )
                db.session.add(nova_area)
                db.session.flush()
                area_id_map[area_data['id']] = nova_area.id
            
            # Importar ambientes
            for ambiente_data in data['ambientes']:
                novo_ambiente = Ambiente(
                    nome=ambiente_data['nome'],
                    area_id=area_id_map[ambiente_data['area_id']]
                )
                db.session.add(novo_ambiente)
                db.session.flush()
                ambiente_id_map[ambiente_data['id']] = novo_ambiente.id
            
            # Importar circuitos
            for circuito_data in data['circuitos']:
                novo_circuito = Circuito(
                    identificador=circuito_data['identificador'],
                    nome=circuito_data['nome'],
                    tipo=circuito_data['tipo'],
                    ambiente_id=ambiente_id_map[circuito_data['ambiente_id']],
                    sak=circuito_data['sak']
                )
                db.session.add(novo_circuito)
                db.session.flush()
                circuito_id_map[circuito_data['id']] = novo_circuito.id
            
            # Importar módulos
            for modulo_data in data['modulos']:
                novo_modulo = Modulo(
                    nome=modulo_data['nome'],
                    tipo=modulo_data['tipo'],
                    quantidade_canais=modulo_data['quantidade_canais'],
                    projeto_id=novo_projeto.id
                )
                db.session.add(novo_modulo)
                db.session.flush()
                modulo_id_map[modulo_data['id']] = novo_modulo.id
            
            # Importar vinculações
            for vinculacao_data in data['vinculacoes']:
                nova_vinculacao = Vinculacao(
                    circuito_id=circuito_id_map[vinculacao_data['circuito_id']],
                    modulo_id=modulo_id_map[vinculacao_data['modulo_id']],
                    canal=vinculacao_data['canal']
                )
                db.session.add(nova_vinculacao)
            
            db.session.commit()
            
            return jsonify({'success': True, 'projeto_id': novo_projeto.id})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Erro na importação: {str(e)}'})
    
    return jsonify({'success': False, 'message': 'Formato de arquivo inválido'})

@app.route('/user/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    if not current_user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Senha atual incorreta'})
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Senha alterada com sucesso'})

@app.route('/exportar-pdf/<int:projeto_id>')
@login_required
def exportar_pdf(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se o usuário tem acesso ao projeto
    if projeto.user_id != current_user.id and current_user.role != 'admin':
        flash('Acesso negado a este projeto', 'danger')
        return redirect(url_for('index'))
    
    # Criar buffer para o PDF
    buffer = io.BytesIO()
    
    # Criar o documento PDF
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
        title=f"Projeto {projeto.nome}"
    )
    
    # Estilos - usando nomes únicos para evitar conflitos
    styles = getSampleStyleSheet()
    
    # Verificar se os estilos já existem antes de adicionar
    if 'RoehnTitle' not in styles:
        styles.add(ParagraphStyle(
            name='RoehnTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
    
    if 'RoehnSubtitle' not in styles:
        styles.add(ParagraphStyle(
            name='RoehnSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=12
        ))
    
    if 'RoehnCenter' not in styles:
        styles.add(ParagraphStyle(
            name='RoehnCenter',
            parent=styles['Normal'],
            alignment=TA_CENTER
        ))
    
    # Elementos do PDF
    elements = []
    
    # Caminho para sua imagem
    zafirologopath = "static/images/zafirologo.png"
    zafirologo = Image(zafirologopath, width=2*inch, height=2*inch)
    # Cabeçalho
    elements.append(zafirologo)
    #elements.append(Paragraph("ZAFIRO - LUXURY TECHNOLOGY", styles['RoehnTitle']))
    elements.append(Paragraph("RELATÓRIO DE PROJETO", styles['RoehnCenter']))
    elements.append(Spacer(1, 0.2*inch))
    
    # No método exportar_pdf, substitua a seção de informações do projeto:

    # Adicione este estilo personalizado antes de criar os elementos
    if 'LeftNormal' not in styles:
        styles.add(ParagraphStyle(
            name='LeftNormal',
            parent=styles['Normal'],
            alignment=TA_LEFT
        ))

    # E use este novo estilo:
    elements.append(Paragraph(f"<b>Projeto:</b> {projeto.nome}", styles['LeftNormal']))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Data de emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['LeftNormal']))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Emitido por:</b> {current_user.username}", styles['LeftNormal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Para cada área
    for area in projeto.areas:
        elements.append(Paragraph(f"ÁREA: {area.nome}", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Para cada ambiente na área
        for ambiente in area.ambientes:
            elements.append(Paragraph(f"Ambiente: {ambiente.nome}", styles['Heading3']))
            
            # Preparar dados da tabela de circuitos
            circuito_data = [["Circuito", "Nome", "Tipo", "SAKs", "Módulo", "Canal"]]
            
            for circuito in ambiente.circuitos:
                modulo_nome = "Não vinculado"
                canal = "-"
                if circuito.vinculacao:
                    modulo_nome = circuito.vinculacao.modulo.nome
                    canal = str(circuito.vinculacao.canal)
                
                # Para circuitos HVAC, mostrar vazio no campo SAK
                if circuito.tipo == 'hvac':
                    sak_value = ""
                    circuito_data.append([
                        circuito.identificador,
                        circuito.nome,
                        circuito.tipo.upper(),
                        sak_value,
                        modulo_nome,
                        canal
                    ])
                elif circuito.tipo == 'persiana':
                    # Para persianas, adicionar duas linhas: uma para subir e outra para descer
                    circuito_data.append([
                        circuito.identificador,
                        circuito.nome + " (sobe)",
                        circuito.tipo.upper(),
                        str(circuito.sak),  # SAK de subida
                        modulo_nome,
                        canal + "s"  # Indicar que é o canal de subida
                    ])
                    circuito_data.append([
                        circuito.identificador,
                        circuito.nome + " (desce)",
                        circuito.tipo.upper(),
                        str(circuito.sak + 1),  # SAK de descida
                        modulo_nome,
                        canal + "d"  # Indicar que é o canal de descida
                    ])
                else:
                    # Para outros circuitos
                    circuito_data.append([
                        circuito.identificador,
                        circuito.nome,
                        circuito.tipo.upper(),
                        str(circuito.sak),
                        modulo_nome,
                        canal
                    ])
            
            # Criar tabela de circuitos
            if len(circuito_data) > 1:
                circuito_table = Table(
                    circuito_data, 
                    colWidths=[0.7*inch, 1.5*inch, 0.8*inch, 0.6*inch, 1.2*inch, 0.6*inch],
                    repeatRows=1
                )
                
                # Estilo da tabela
                estilo_tabela = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#4d4f52")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f3f5")])
                ])
                
                # Adicionar cores diferentes por tipo de circuito
                for i, row in enumerate(circuito_data[1:], 1):
                    if row[2] == "LUZ":
                        estilo_tabela.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#fff3cd"))
                    elif row[2] == "PERSIANA":
                        # Colorir as linhas de persiana de forma diferente
                        if "(sobe)" in row[1]:
                            estilo_tabela.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#d1ecf1"))
                        elif "(desce)" in row[1]:
                            estilo_tabela.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#e8f4f8"))
                    elif row[2] == "HVAC":
                        estilo_tabela.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#d4edda"))
                
                circuito_table.setStyle(estilo_tabela)
                elements.append(circuito_table)
            else:
                elements.append(Paragraph("Nenhum circuito neste ambiente.", styles['Italic']))
            
            elements.append(Spacer(1, 0.2*inch))
        
        # Quebra de página após cada área
        if area != projeto.areas[-1]:
            elements.append(PageBreak())
    
    # Resumo de módulos - MODIFICAÇÃO AQUI
    elements.append(PageBreak())
    elements.append(Paragraph("RESUMO DE MÓDULOS", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Coletar todos os módulos do projeto
    modulos_projeto = Modulo.query.filter_by(projeto_id=projeto_id).all()
    
    if modulos_projeto:
        for modulo in modulos_projeto:
            elements.append(Paragraph(f"Módulo: {modulo.nome} ({modulo.tipo})", styles['Heading3']))
            
            # Preparar dados da tabela de canais - ADICIONANDO SEPARAÇÃO PARA PERSIANAS
            canal_data = [["Canal", "Circuito", "Nome do Circuito", "Tipo", "SAK"]]
            
            # Preencher com as vinculações deste módulo
            canais_ocupados = {v.canal: v for v in modulo.vinculacoes}
            
            for canal_num in range(1, modulo.quantidade_canais + 1):
                if canal_num in canais_ocupados:
                    vinculacao = canais_ocupados[canal_num]
                    circuito = vinculacao.circuito
                    
                    if circuito.tipo == 'persiana':
                        # Para persianas, adicionar duas linhas
                        canal_data.append([
                            str(canal_num) + "s",  # Canal de subida
                            circuito.identificador,
                            circuito.nome + " (sobe)",
                            circuito.tipo.upper(),
                            str(circuito.sak)  # SAK de subida
                        ])
                        canal_data.append([
                            str(canal_num) + "d",  # Canal de descida
                            circuito.identificador,
                            circuito.nome + " (desce)",
                            circuito.tipo.upper(),
                            str(circuito.sak + 1)  # SAK de descida
                        ])
                    else:
                        # Para outros circuitos
                        if circuito.tipo == 'hvac':
                            sak_value = ""
                        else:
                            sak_value = str(circuito.sak)
                        
                        canal_data.append([
                            str(canal_num),
                            circuito.identificador,
                            circuito.nome,
                            circuito.tipo.upper(),
                            sak_value
                        ])
                else:
                    canal_data.append([
                        str(canal_num),
                        "Livre",
                        "-",
                        "-",
                        "-"
                    ])
            
            # Criar tabela de canais - AJUSTANDO LARGURAS DAS COLUNAS
            canal_table = Table(
                canal_data, 
                colWidths=[0.7*inch, 1.0*inch, 1.5*inch, 0.8*inch, 0.8*inch],
                repeatRows=1
            )
            
            # Estilo da tabela
            estilo_canal = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#4d4f52")),
            ])
            
            # Adicionar cores diferentes por tipo de circuito
            for i, row in enumerate(canal_data[1:], 1):
                if row[3] == "LUZ":
                    estilo_canal.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#fff3cd"))
                elif row[3] == "PERSIANA":
                    # Colorir as linhas de persiana de forma diferente
                    if "(sobe)" in row[2]:
                        estilo_canal.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#d1ecf1"))
                    elif "(desce)" in row[2]:
                        estilo_canal.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#e8f4f8"))
                elif row[3] == "HVAC":
                    estilo_canal.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#d4edda"))
            
            canal_table.setStyle(estilo_canal)
            elements.append(canal_table)
            elements.append(Spacer(1, 0.3*inch))
    else:
        elements.append(Paragraph("Nenhum módulo configurado neste projeto.", styles['Italic']))
    
    # Rodapé com informações da empresa
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Zafiro - Luxury Technology", 
                             styles['RoehnCenter']))
    elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", 
                             styles['RoehnCenter']))
    
    # Construir o PDF
    doc.build(elements)
    
    buffer.seek(0)
    
    # Nome do arquivo
    nome_arquivo = f"projeto_{projeto.nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
