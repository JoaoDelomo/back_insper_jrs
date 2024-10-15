from flask import Flask, render_template, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from models.database import get_db

app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configurando o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelo do usuário para autenticação
class User(UserMixin):
    def __init__(self, matricula):
        self.matricula = matricula

    def get_id(self):
        return self.matricula

# Função para carregar o usuário pelo ID (matrícula)
@login_manager.user_loader
def load_user(matricula):
    db = get_db()
    aluno = db['alunos'].find_one({"matricula": matricula})
    if aluno:
        return User(matricula=aluno['matricula'])
    return None

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']

        # Verificar o aluno no banco de dados
        db = get_db()
        aluno = db['alunos'].find_one({"matricula": matricula})

        if aluno and check_password_hash(aluno['senha'], senha):
            user = User(matricula=aluno['matricula'])
            login_user(user)
            return redirect(url_for('dashboard'))

        return 'Matrícula ou senha incorretos.'

    return render_template('login.html')

# Rota para logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rota para o dashboard (acessível apenas após login)
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    aluno = db['alunos'].find_one({"matricula": current_user.get_id()})

    if aluno:
        return render_template('dashboard.html', aluno=aluno)
    else:
        return "Erro ao carregar as informações."

# Rota para ver avisos (apenas para o aluno logado)
@app.route('/avisos')
@login_required
def avisos():
    db = get_db()
    aluno = db['alunos'].find_one({"matricula": current_user.get_id()})

    if aluno and "avisos" in aluno:
        avisos = aluno['avisos']
        return render_template('avisos.html', avisos=avisos, aluno=aluno)
    else:
        return "Nenhum aviso encontrado."

# Rota para ver notas (apenas para o aluno logado)
@app.route('/notas')
@login_required
def notas():
    db = get_db()
    aluno = db['alunos'].find_one({"matricula": current_user.get_id()})

    if aluno and "notas" in aluno:
        notas = aluno['notas']
        return render_template('notas.html', notas=notas, aluno=aluno)
    else:
        return "Nenhuma nota encontrada."

if __name__ == '__main__':
    app.run(debug=True)
