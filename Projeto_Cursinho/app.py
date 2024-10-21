from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from models.database import get_db

# Configuração do Flask
app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
        matricula = request.form.get('matricula')
        senha = request.form.get('senha')
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

# Rota do Professor
@app.route('/home-professor')
@login_required
def home_professor():
    if current_user.tipo != 'professor':
        return "Apenas professores podem acessar esta página.", 403

    db = get_db()
    professor = db['usuarios'].find_one({"matricula": current_user.get_id(), "tipo": "professor"})
    alunos = list(db['usuarios'].find({"tipo": "aluno"}))
    avisos = list(db['avisos'].find({"autor": current_user.get_id()}))

    return render_template('home_professor.html', professor=professor, alunos=alunos, avisos=avisos)

# Rota para Criar/Editar Nota
@app.route('/notas/manage/<aluno_id>', methods=['GET', 'POST'])
@app.route('/notas/manage/<aluno_id>/<int:nota_idx>', methods=['GET', 'POST'])
@login_required
def manage_nota(aluno_id, nota_idx=None):
    db = get_db()
    aluno = db['usuarios'].find_one({"_id": ObjectId(aluno_id)})
    nota = aluno['notas'][nota_idx] if nota_idx is not None else None

    if request.method == 'POST':
        disciplina = request.form['disciplina']
        titulo = request.form.get('titulo', 'Sem título')
        valor = float(request.form['nota'])

        if nota:  # Atualizar nota existente
            db['usuarios'].update_one(
                {"_id": ObjectId(aluno_id)},
                {"$set": {f"notas.{nota_idx}.disciplina": disciplina, 
                          f"notas.{nota_idx}.titulo": titulo, 
                          f"notas.{nota_idx}.nota": valor}}
            )
        else:  # Adicionar nova nota
            nova_nota = {
                "disciplina": disciplina,
                "titulo": titulo,
                "nota": valor
            }
            db['usuarios'].update_one(
                {"_id": ObjectId(aluno_id)},
                {"$push": {"notas": nova_nota}}
            )

        flash("Nota salva com sucesso!")
        return redirect(url_for('home_professor'))

    return render_template('manage_nota.html', aluno=aluno, nota=nota)


# Rota para excluir nota
@app.route('/notas/excluir/<aluno_id>/<int:nota_idx>', methods=['POST'])
@login_required
def excluir_nota(aluno_id, nota_idx):
    db = get_db()
    db['usuarios'].update_one(
        {"_id": ObjectId(aluno_id)},
        {"$unset": {f"notas.{nota_idx}": 1}}
    )
    db['usuarios'].update_one(
        {"_id": ObjectId(aluno_id)},
        {"$pull": {"notas": None}}
    )
    flash("Nota excluída com sucesso!")
    return redirect(url_for('home_professor'))



# Rota para Criar/Editar Aviso
@app.route('/avisos/manage', methods=['GET', 'POST'])
@app.route('/avisos/manage/<aviso_id>', methods=['GET', 'POST'])
@login_required
def manage_aviso(aviso_id=None):
    db = get_db()
    aviso = db['avisos'].find_one({"_id": ObjectId(aviso_id)}) if aviso_id else None

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        mensagem = request.form.get('mensagem')

        aviso_data = {"titulo": titulo, "mensagem": mensagem, "autor": current_user.get_id()}

        if aviso:
            db['avisos'].update_one({"_id": ObjectId(aviso_id)}, {"$set": aviso_data})
            flash("Aviso atualizado com sucesso!")
        else:
            db['avisos'].insert_one(aviso_data)
            flash("Aviso criado com sucesso!")

        return redirect(url_for('home_professor' if current_user.tipo == 'professor' else 'home_gestor'))

    return render_template('manage_aviso.html', aviso=aviso)

# Rota para Excluir Aviso
@app.route('/avisos/excluir/<aviso_id>', methods=['POST'])
@login_required
def excluir_aviso(aviso_id):
    db = get_db()
    db['avisos'].delete_one({"_id": ObjectId(aviso_id)})
    flash("Aviso excluído com sucesso!")

    return redirect(url_for('home_professor' if current_user.tipo == 'professor' else 'home_gestor'))

# Rota do Gestor
@app.route('/home-gestor')
@login_required
def home_gestor():
    if current_user.tipo != 'gestor':
        return "Apenas gestores podem acessar esta página.", 403

    db = get_db()
    avisos = list(db['avisos'].find())

    return render_template('home_gestor.html', avisos=avisos)

if __name__ == '__main__':
    app.run(debug=True)

