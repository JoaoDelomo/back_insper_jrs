from flask import Flask, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId
from models.database import get_db
from flask_cors import CORS
from functools import wraps
import jwt
import datetime


app = Flask(__name__)
app.secret_key = 'chave_secreta'

CORS(app, origins=["http://localhost:5173"], supports_credentials=True)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, matricula, tipo):
        self.matricula = matricula
        self.tipo = tipo

    def get_id(self):
        return self.matricula
    
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({"message": "Token ausente"}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = load_user(data['matricula'])
        except Exception as e:
            return jsonify({"message": f"Token inválido: {str(e)}"}), 401

        return f(*args, **kwargs)

    return decorated

@login_manager.user_loader
def load_user(matricula):
    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})
    if usuario:
        return User(matricula=usuario['matricula'], tipo=usuario['tipo'])
    return None

@app.route('/login', methods=['POST', 'GET'])
def login():
    data = request.json
    matricula = data.get('matricula')
    senha = data.get('senha')

    if not matricula or not senha:
        return jsonify({"message": "Dados incompletos"}), 400

    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})

    if usuario and check_password_hash(usuario['senha'], senha):
        user = User(matricula=usuario['matricula'], tipo=usuario['tipo'])
        login_user(user)
        
        # Gerar token JWT
        token = jwt.encode({
            'matricula': usuario['matricula'],
            'tipo': usuario['tipo'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            "message": "Login realizado com sucesso",
            "token": token,
            "tipo": usuario['tipo']
        }), 200

    return jsonify({"message": "Matrícula ou senha incorretos"}), 401


@app.route('/home-aluno', methods=['GET'])
@token_required
def home_aluno():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])
    if current_user.tipo != 'aluno':
        return jsonify({"message": "Apenas alunos podem acessar esta página"}), 403

    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": current_user.matricula})
    materias = aluno.get("materias", [])
    grade = list(db['grade_horaria'].find({}, {"_id": 0}))
    avisos = list(db['avisos'].find({}, {"_id": 0}))

    return jsonify({
        "nome": aluno["nome"],
        "notas": aluno.get("notas", []),
        "materias": materias,
        "grade_horaria": grade,
        "avisos": avisos
    }), 200

@app.route('/home-professor', methods=['GET'])
@token_required
def home_professor():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'professor':
        return jsonify({"message": "Apenas professores podem acessar esta página"}), 403

    db = get_db()
    professor = db['usuarios'].find_one({"matricula": current_user.matricula})
    materias = professor.get("materias", [])
    alunos = list(db['usuarios'].find({"tipo": "aluno"}, {"_id": 0, "nome": 1, "notas": 1}))
    grade = list(db['grade_horaria'].find({}, {"_id": 0}))

    return jsonify({
        "nome": professor["nome"],
        "materias": materias,
        "alunos": alunos,
        "grade_horaria": grade
    }), 200

@app.route('/materia/<nome_materia>', methods=['GET'])
@token_required
def listar_conteudo_materia(nome_materia):
    db = get_db()
    # Busca conteúdos relacionados à matéria
    conteudos = list(db['usuarios'].aggregate([
        {"$match": {"conteudos.materia": nome_materia}},
        {"$unwind": "$conteudos"},
        {"$match": {"conteudos.materia": nome_materia}},
        {"$project": {"_id": 0, "conteudos": 1}}
    ]))

    if not conteudos:
        return jsonify({"message": "Nenhum conteúdo encontrado para esta matéria"}), 404

    return jsonify({"conteudos": [c["conteudos"] for c in conteudos]}), 200

@app.route('/professor/conteudo', methods=['POST'])
@token_required
def criar_conteudo():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'professor':
        return jsonify({"message": "Apenas professores podem criar conteúdos"}), 403

    # Buscar as matérias do professor diretamente do banco de dados
    db = get_db()
    professor = db['usuarios'].find_one({"matricula": current_user.matricula})

    if not professor:
        return jsonify({"message": "Usuário não encontrado"}), 404

    materias = professor.get('materias', [])

    # Obter os dados do conteúdo do JSON enviado
    data = request.json
    materia = data.get('materia')
    titulo = data.get('titulo')
    descricao = data.get('descricao')

    # Verificar se a matéria fornecida pertence ao professor
    if materia not in materias:
        return jsonify({"message": "Você só pode criar conteúdos para suas matérias"}), 403

    # Criar o novo conteúdo
    novo_conteudo = {
        "materia": materia,
        "titulo": titulo,
        "descricao": descricao
    }

    # Adicionar o conteúdo ao campo 'conteudos' do professor
    db['usuarios'].update_one(
        {"matricula": current_user.matricula},
        {"$push": {"conteudos": novo_conteudo}}
    )

    return jsonify({"message": "Conteúdo criado com sucesso"}), 201

@app.route('/home-gestor', methods=['GET'])
@token_required
def home_gestor():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem acessar esta página"}), 403

    db = get_db()
    alunos = list(db['usuarios'].find({"tipo": "aluno"}, {"_id": 0, "nome": 1, "notas": 1}))
    grade = list(db['grade_horaria'].find({}, {"_id": 0}))
    avisos = list(db['avisos'].find({}, {"_id": 0}))

    return jsonify({
        "alunos": alunos,
        "grade_horaria": grade,
        "avisos": avisos
    }), 200


@app.route('/gestor/criar-usuario', methods=['POST'])
@token_required
def criar_usuario():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem criar usuários"}), 403

    data = request.json
    
    senha_hash = generate_password_hash(data['senha'])

    if data.get('tipo') == 'aluno':
        trilha = data.get('trilha')
        if trilha not in ["humanas", "naturais"]:
            return jsonify({"message": "Trilha inválida"}), 400

        materias = ["matematica", "portugues", trilha]

        usuario = {
            "nome": data['nome'],
            "matricula": data['matricula'],
            "senha": senha_hash,
            "tipo": data['tipo'],
            "turma": data['turma'],
            "trilha": trilha,
            "materias": materias,
            "notas": []
        }

    elif data.get('tipo') == 'professor':
        usuario = {
            "nome": data['nome'],
            "matricula": data['matricula'],
            "senha": senha_hash,
            "tipo": data['tipo'],
            "materias": data['materias'],
            "avisos": [],
            "conteudos": []
        }

    elif data.get('tipo') == 'gestor':
        usuario = {
            "nome": data['nome'],
            "matricula": data['matricula'],
            "senha": senha_hash,
            "tipo": data['tipo'],
            "avisos": [],
        }

    db = get_db()
    db['usuarios'].insert_one(usuario)
    return jsonify({"message": "Usuário criado com sucesso"}), 201


@app.route('/gestor/notas/<aluno_id>', methods=['POST'])
@token_required
def definir_nota(aluno_id):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem definir notas"}), 403

    # Buscar o aluno pelo campo 'matricula' (ou outro identificador usado no seu banco)
    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": aluno_id})

    if not aluno:
        return jsonify({"message": "Aluno não encontrado"}), 404

    data = request.json
    nova_nota = {"simulado": data['simulado'], "nota": data['nota']}

    # Atualizar as notas do aluno encontrado
    db['usuarios'].update_one(
        {"matricula": aluno_id},
        {"$push": {"notas": nova_nota}}
    )

    return jsonify({"message": "Nota adicionada com sucesso"}), 200

@app.route('/gestor/grade-horaria', methods=['POST'])
@token_required
def criar_grade_horaria():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem criar a grade horária"}), 403

    data = request.json
    nova_entrada = {
        "materia": data['materia'],
        "dias": data['dias'],
        "horario": data['horario']
    }
    db = get_db()
    db['grade_horaria'].insert_one(nova_entrada)
    return jsonify({"message": "Grade horária adicionada com sucesso"}), 201

@app.route('/logout', methods=['POST'])
@token_required
def logout():
    logout_user()
    return jsonify({"message": "Logout bem-sucedido"}), 200

if __name__ == '__main__':
    app.run(debug=True)
