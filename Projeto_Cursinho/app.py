from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

# Configuração do Flask
app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Conectar ao MongoDB
def get_db():
    connection_string = "mongodb+srv://admin:admin@delomo.zxqnf.mongodb.net/?authSource=admin&retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    db = client['JRs']
    return db

# Modelo de Usuário
class User(UserMixin):
    def __init__(self, matricula, tipo):
        self.matricula = matricula
        self.tipo = tipo

    def get_id(self):
        return self.matricula

# Carregar o usuário no Flask-Login
@login_manager.user_loader
def load_user(matricula):
    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})
    if usuario:
        return User(matricula=usuario['matricula'], tipo=usuario['tipo'])
    return None

# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']
        db = get_db()
        usuario = db['usuarios'].find_one({"matricula": matricula})

        if usuario and check_password_hash(usuario['senha'], senha):
            user = User(matricula=usuario['matricula'], tipo=usuario['tipo'])
            login_user(user)
            if user.tipo == 'aluno':
                return redirect(url_for('home_aluno'))
            elif user.tipo == 'professor':
                return redirect(url_for('home_professor'))
            elif user.tipo == 'gestor':
                return redirect(url_for('home_gestor'))
        flash("Matrícula ou senha incorretos.")
    return render_template('login.html')

# Rota de Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rota do Aluno
@app.route('/home-aluno')
@login_required
def home_aluno():
    if current_user.tipo != 'aluno':
        return "Apenas alunos podem acessar esta página.", 403

    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": current_user.get_id(), "tipo": "aluno"})
    avisos = list(db['avisos'].find())

    return render_template('home_aluno.html', aluno=aluno, avisos=avisos)

# Rota para criar/editar aviso (Unificada)
@app.route('/avisos/manage', methods=['GET', 'POST'])
@app.route('/avisos/manage/<aviso_id>', methods=['GET', 'POST'])
@login_required
def manage_aviso(aviso_id=None):
    db = get_db()
    aviso = None

    if aviso_id:
        aviso = db['avisos'].find_one({"_id": ObjectId(aviso_id)})

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        mensagem = request.form.get('mensagem')
        disciplina = request.form.get('disciplina')

        if aviso:  # Editar aviso
            db['avisos'].update_one(
                {"_id": ObjectId(aviso_id)},
                {"$set": {"titulo": titulo, "mensagem": mensagem, "disciplina": disciplina}}
            )
        else:  # Criar novo aviso
            novo_aviso = {
                "titulo": titulo,
                "mensagem": mensagem,
                "disciplina": disciplina,
                "autor": current_user.get_id(),
                "tipo_autor": current_user.tipo
            }
            db['avisos'].insert_one(novo_aviso)

        return redirect(url_for('home_gestor' if current_user.tipo == 'gestor' else 'home_professor'))

    return render_template('manage_aviso.html', aviso=aviso)

# Rota para excluir aviso
@app.route('/avisos/excluir/<aviso_id>', methods=['POST'])
@login_required
def excluir_aviso(aviso_id):
    db = get_db()
    db['avisos'].delete_one({"_id": ObjectId(aviso_id)})
    flash("Aviso excluído com sucesso!")

    return redirect(url_for('home_gestor' if current_user.tipo == 'gestor' else 'home_professor'))

# Rota do Professor
@app.route('/home-professor')
@login_required
def home_professor():
    if current_user.tipo != 'professor':
        return "Apenas professores podem acessar esta página.", 403

    db = get_db()
    professor = db['usuarios'].find_one({"matricula": current_user.get_id(), "tipo": "professor"})
    avisos = list(db['avisos'].find({"autor": current_user.get_id()}))

    return render_template('home_professor.html', professor=professor, avisos=avisos)

# Rota do Gestor
@app.route('/home-gestor')
@login_required
def home_gestor():
    if current_user.tipo != 'gestor':
        return "Apenas gestores podem acessar esta página.", 403

    db = get_db()
    gestor = db['usuarios'].find_one({"matricula": current_user.get_id(), "tipo": "gestor"})
    avisos = list(db['avisos'].find())

    return render_template('home_gestor.html', gestor=gestor, avisos=avisos)

if __name__ == '__main__':
    app.run(debug=True)
