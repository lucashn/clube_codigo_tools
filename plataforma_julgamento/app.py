from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_para_sessao'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///competicao.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELOS DE BANCO DE DADOS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    # Cascade: ao apagar o usuário, apaga as submissões dele
    submissoes = db.relationship('Submissao', backref='user', cascade='all, delete-orphan', lazy=True)

class Competicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    inicio = db.Column(db.DateTime, nullable=False)
    termino = db.Column(db.DateTime, nullable=False)
    # Cascade: ao apagar a competição, apaga os problemas associados
    problemas = db.relationship('Problema', backref='competicao', cascade='all, delete-orphan', lazy=True)

class Problema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    competicao_id = db.Column(db.Integer, db.ForeignKey('competicao.id'), nullable=False)
    letra = db.Column(db.String(1), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    # Cascade: ao apagar o problema, apaga as submissões dele
    submissoes = db.relationship('Submissao', backref='problema', cascade='all, delete-orphan', lazy=True)

class Submissao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problema_id = db.Column(db.Integer, db.ForeignKey('problema.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    codigo = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pendente')
    data_envio = db.Column(db.DateTime, default=datetime.now)

# ================= ROTAS PRINCIPAIS =================

@app.route('/')
def index():
    agora = datetime.now()
    
    # Se for admin, vê todas. Se for usuário, apenas as que não terminaram.
    if session.get('is_admin'):
        competicoes = Competicao.query.order_by(Competicao.termino.desc()).all()
    else:
        competicoes = Competicao.query.filter(Competicao.termino >= agora).order_by(Competicao.termino.asc()).all()
        
    return render_template('index.html', competicoes=competicoes, agora=agora)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        user = User.query.filter_by(nome=nome).first()
        
        if user and check_password_hash(user.senha_hash, senha):
            session['user_id'] = user.id
            session['nome'] = user.nome
            session['is_admin'] = user.is_admin
            return redirect(url_for('admin' if user.is_admin else 'index'))
        else:
            flash('Nome ou senha incorretos.', 'erro')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/competicao/<int:id_comp>', methods=['GET', 'POST'])
def competicao(id_comp):
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    comp = Competicao.query.get_or_404(id_comp)
    agora = datetime.now()

    # Redireciona usuário comum se a competição já acabou (proteção extra de rota)
    if not session.get('is_admin') and comp.termino < agora:
        flash('Esta competição já foi encerrada.', 'erro')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if comp.termino < agora:
            flash('Tempo esgotado! Não é mais possível submeter.', 'erro')
        else:
            problema_id = request.form['problema_id']
            codigo = request.form['codigo']
            nova_sub = Submissao(problema_id=problema_id, user_id=session['user_id'], codigo=codigo)
            db.session.add(nova_sub)
            db.session.commit()
            flash('Código submetido com sucesso! Aguarde o julgamento.', 'sucesso')
            return redirect(url_for('competicao', id_comp=id_comp))
        
    minhas_submissoes = Submissao.query.join(Problema).filter(
        Submissao.user_id == session['user_id'],
        Problema.competicao_id == id_comp
    ).order_by(Submissao.data_envio.desc()).all()

    # Placar específico desta competição
    placar = db.session.query(
        User.nome,
        func.count(func.distinct(Submissao.problema_id)).label('pontos')
    ).select_from(Submissao)\
     .join(User, User.id == Submissao.user_id)\
     .join(Problema, Submissao.problema_id == Problema.id)\
     .filter(Problema.competicao_id == id_comp)\
     .filter(Submissao.status == 'correta')\
     .filter(User.is_admin == False)\
     .group_by(User.id)\
     .order_by(func.count(func.distinct(Submissao.problema_id)).desc()).all()
    
    return render_template('competicao.html', comp=comp, submissoes=minhas_submissoes, placar=placar, agora=agora)

# ================= ROTAS DE ADMINISTRAÇÃO =================

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        acao = request.form.get('acao')
        if acao == 'add_competidor':
            nome = request.form['nome']
            senha = generate_password_hash(request.form['senha'])
            novo_user = User(nome=nome, senha_hash=senha, is_admin=False)
            db.session.add(novo_user)
            db.session.commit()
            flash('Competidor cadastrado!', 'sucesso')
            
        elif acao == 'add_competicao':
            nome = request.form['nome']
            inicio = datetime.strptime(request.form['inicio'], '%Y-%m-%dT%H:%M')
            termino = datetime.strptime(request.form['termino'], '%Y-%m-%dT%H:%M')
            nova_comp = Competicao(nome=nome, inicio=inicio, termino=termino)
            db.session.add(nova_comp)
            db.session.commit()
            flash('Competição cadastrada!', 'sucesso')
            
        elif acao == 'add_problema':
            comp_id = request.form['competicao_id']
            nome = request.form['nome']
            qtd_problemas = Problema.query.filter_by(competicao_id=comp_id).count()
            letra = chr(65 + qtd_problemas) 
            novo_prob = Problema(competicao_id=comp_id, letra=letra, nome=nome)
            db.session.add(novo_prob)
            db.session.commit()
            flash(f'Problema {letra} adicionado!', 'sucesso')
            
        elif acao == 'julgar':
            sub_id = request.form['submissao_id']
            novo_status = request.form['status']
            sub = Submissao.query.get(sub_id)
            sub.status = novo_status
            db.session.commit()
            flash('Submissão julgada!', 'sucesso')
            
    competicoes = Competicao.query.all()
    competidores = User.query.filter_by(is_admin=False).all()
    submissoes_pendentes = Submissao.query.filter_by(status='pendente').all()
    problemas = Problema.query.join(Competicao).order_by(Competicao.id, Problema.letra).all()
    
    return render_template('admin.html', competicoes=competicoes, competidores=competidores, pendentes=submissoes_pendentes, problemas=problemas)

@app.route('/admin/competidor/<int:id>/remover')
def remover_competidor(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('Competidor removido com sucesso.', 'sucesso')
    return redirect(url_for('admin'))

@app.route('/admin/competicao/<int:id>/remover')
def remover_competicao(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    comp = Competicao.query.get_or_404(id)
    db.session.delete(comp)
    db.session.commit()
    flash('Competição removida com sucesso.', 'sucesso')
    return redirect(url_for('admin'))

@app.route('/admin/competidor/<int:id>/editar', methods=['GET', 'POST'])
def editar_competidor(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.nome = request.form['nome']
        if request.form['senha']: # Só atualiza a senha se foi preenchida
            user.senha_hash = generate_password_hash(request.form['senha'])
        db.session.commit()
        flash('Competidor atualizado!', 'sucesso')
        return redirect(url_for('admin'))
    return render_template('editar_competidor.html', user=user)

@app.route('/admin/competicao/<int:id>/editar', methods=['GET', 'POST'])
def editar_competicao(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    comp = Competicao.query.get_or_404(id)
    if request.method == 'POST':
        comp.nome = request.form['nome']
        comp.inicio = datetime.strptime(request.form['inicio'], '%Y-%m-%dT%H:%M')
        comp.termino = datetime.strptime(request.form['termino'], '%Y-%m-%dT%H:%M')
        db.session.commit()
        flash('Competição atualizada!', 'sucesso')
        return redirect(url_for('admin'))
    return render_template('editar_competicao.html', comp=comp)

@app.route('/admin/problema/<int:id>/remover')
def remover_problema(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    prob = Problema.query.get_or_404(id)
    db.session.delete(prob)
    db.session.commit()
    flash('Problema removido com sucesso.', 'sucesso')
    return redirect(url_for('admin'))

@app.route('/admin/problema/<int:id>/editar', methods=['GET', 'POST'])
def editar_problema(id):
    if not session.get('is_admin'): return redirect(url_for('index'))
    prob = Problema.query.get_or_404(id)
    if request.method == 'POST':
        prob.letra = request.form['letra'].upper()
        prob.nome = request.form['nome']
        db.session.commit()
        flash('Problema atualizado!', 'sucesso')
        return redirect(url_for('admin'))
    return render_template('editar_problema.html', prob=prob)

@app.route('/admin/competicao/<int:id_comp>/placar')
def placar_admin(id_comp):
    # Proteção: Apenas admin pode acessar
    if not session.get('is_admin'): 
        flash('Acesso negado.', 'erro')
        return redirect(url_for('index'))
        
    comp = Competicao.query.get_or_404(id_comp)
    
    # Busca os problemas ordenados pela letra (A, B, C...) para montar as colunas
    problemas = Problema.query.filter_by(competicao_id=id_comp).order_by(Problema.letra).all()
    
    # Busca todos os usuários que não são admin (competidores)
    competidores = User.query.filter_by(is_admin=False).all()
    
    dados_placar = []
    
    for user in competidores:
        # Busca todas as submissões deste usuário nesta competição específica
        submissoes = Submissao.query.join(Problema).filter(
            Submissao.user_id == user.id,
            Problema.competicao_id == id_comp
        ).all()
        
        # Mapeia qual é o status final de cada problema para o usuário
        prob_status = {}
        for sub in submissoes:
            # A lógica aqui garante que, se ele já acertou (correta), 
            # uma submissão posterior com erro não apaga o acerto dele na tabela.
            if prob_status.get(sub.problema_id) != 'correta':
                prob_status[sub.problema_id] = sub.status
                
        # Calcula o total de pontos (apenas as corretas)
        total_pontos = sum(1 for status in prob_status.values() if status == 'correta')
        
        dados_placar.append({
            'nome': user.nome,
            'total': total_pontos,
            'status_problemas': prob_status
        })
        
    # Ordena a lista de competidores do maior total de pontos para o menor
    dados_placar.sort(key=lambda x: x['total'], reverse=True)
    
    return render_template('placar_admin.html', comp=comp, problemas=problemas, placar=dados_placar)

# ================= INICIALIZAÇÃO =================

def setup_db():
    with app.app_context():
        db.create_all()
        if not User.query.first():
            admin = User(nome='admin', senha_hash=generate_password_hash('admin'), is_admin=True)
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    setup_db()
    app.run(debug=True)