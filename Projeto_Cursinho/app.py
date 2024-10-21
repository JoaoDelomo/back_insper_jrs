from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from models.database import get_db
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'chave_secreta'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, matricula):
        self.matricula = matricula

    def get_id(self):
        return self.matricula

@login_manager.user_loader
def load_user(matricula):
    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})
    if usuario:
        return User(matricula=usuario['matricula'])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']

        db = get_db()
        usuario = db['usuarios'].find_one({"matricula": matricula})

        if usuario and check_password_hash(usuario['senha'], senha):
            user = User(matricula=usuario['matricula'])
            login_user(user)

            if usuario['tipo'] == 'aluno':
                return redirect(url_for('home_aluno'))
            elif usuario['tipo'] == 'professor':
                return redirect(url_for('home_professor'))
            elif usuario['tipo'] == 'gestor':
                return redirect(url_for('home_gestor'))

        return "Matrícula ou senha incorretos."
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home-aluno')
@login_required
def home_aluno():
    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": current_user.get_id(), "tipo": "aluno"})

    if aluno:
        return render_template('home_aluno.html', aluno=aluno, avisos=aluno.get('avisos', []))
    return "Aluno não encontrado", 404


@app.route('/home-professor')
@login_required
def home_professor():
    db = get_db()
    professor = db['usuarios'].find_one({"matricula": current_user.get_id(), "tipo": "professor"})
    return render_template('home_professor.html', professor=professor)

@app.route('/home-gestor')
@login_required
def home_gestor():
    db = get_db()
    gestor = db['usuarios'].find_one({"matricula": current_user.get_id(), "tipo": "gestor"})
    return render_template('home_gestor.html', gestor=gestor)

if __name__ == '__main__':
    app.run(debug=True)
