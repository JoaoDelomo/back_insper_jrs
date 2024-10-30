from flask import Flask, request, jsonify, redirect, url_for, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId
from models.database import get_db
from flask_cors import CORS , cross_origin
from functools import wraps
import jwt
import datetime
from flask_pymongo import PyMongo
import base64
from flask import jsonify
import gridfs


app = Flask(__name__)
app.secret_key = 'chave_secreta'
app.config['MONGO_URI'] = "mongodb+srv://admin:admin@delomo.zxqnf.mongodb.net/JRs"
mongo = PyMongo(app)



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}}, allow_headers="*", origins="*")

class User(UserMixin):
    def __init__(self, matricula, tipo):
        self.matricula = matricula
        self.tipo = tipo

    def get_id(self):
        return self.matricula
    
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', None)
        if token:
            token = token.split(" ")[1]

        if not token:
            return jsonify({"message": "Token ausente"}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = load_user(data['matricula'])

            if not current_user:
                return jsonify({"message": "Usuário não encontrado"}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expirado"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"message": f"Token inválido: {str(e)}"}), 401

        # Passa o usuário atual no kwargs para evitar conflitos
        kwargs['current_user'] = current_user
        return f(*args, **kwargs)

    return decorated


@login_manager.user_loader
def load_user(matricula):
    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})
    if usuario:
        return User(matricula=usuario['matricula'], tipo=usuario['tipo'])
    return None  # Certifique-se de que None é retornado apenas quando o usuário não existe.


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
def home_aluno(current_user=None):
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



@app.route('/home-gestor', methods=['GET'])
@token_required
def home_gestor(**kwargs):
    current_user = kwargs.get('current_user')

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem acessar esta página"}), 403

    db = get_db()
    alunos = list(db['usuarios'].find({"tipo": "aluno"}, {"_id": 0, "nome": 1, "notas": 1}))
    grade = list(db['grade_horaria'].find({}, {"_id": 0}))
    avisos = list(db['avisos'].find({"materia": "geral"}, {"_id": 1, "titulo": 1, "conteudo": 1, "autor": 1, "data": 1, "materia": 1}))

    for aviso in avisos:
        aviso['_id'] = str(aviso['_id'])

    return jsonify({
        "avisos": avisos
    }), 200


@app.route('/editar-aviso/<aviso_id>', methods=['PUT'])
@token_required
def editar_aviso(aviso_id):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor' and current_user.tipo != 'professor':
        return jsonify({"message": "Apenas gestores e professores podem editar avisos"}), 403

    data = request.json

    db = get_db()
    aviso = db['avisos'].find_one({"_id": ObjectId(aviso_id)})

    if not aviso:
        return jsonify({"message": "Aviso não encontrado"}), 404

    db['avisos'].update_one(
        {"_id": ObjectId(aviso_id)},
        {"$set": {"titulo": data['titulo'], "conteudo": data['conteudo']}}
    )

    return jsonify({"message": "Aviso editado com sucesso"}), 200

@app.route('/deletar-aviso/<aviso_id>', methods=['DELETE'])
@token_required
def deletar_aviso(aviso_id):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor' and current_user.tipo != 'professor':
        return jsonify({"message": "Apenas gestores e professores podem deletar avisos"}), 403

    db = get_db()
    aviso = db['avisos'].find_one({"_id": ObjectId(aviso_id)})

    if not aviso:
        return jsonify({"message": "Aviso não encontrado"}), 404

    db['avisos'].delete_one({"_id": ObjectId(aviso_id)})

    return jsonify({"message": "Aviso deletado com sucesso"}), 200


@app.route('/criar-aviso', methods=['POST'])
@token_required
def criar_aviso():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor' and current_user.tipo != 'professor':
        return jsonify({"message": "Apenas gestores e professores podem criar avisos"}), 403

    data = request.json

    matricula = current_user.matricula
    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})
    nome_autor = usuario['nome']
    
    novo_aviso = {
        "titulo": data['titulo'],
        "conteudo": data['conteudo'],
        "materia": data.get('materia'),
        "autor": nome_autor,
        "data": datetime.datetime.now().strftime("%d/%m/%Y")

    }

    db = get_db()
    db['avisos'].insert_one(novo_aviso)
    return jsonify({"message": "Aviso criado com sucesso"}), 201

@app.route('/gestor/lista-alunos', methods=['GET'])
@token_required
def listar_alunos(**kwargs):
    current_user = kwargs.get('current_user')

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem listar alunos"}), 403

    db = get_db()
    alunos = list(db['usuarios'].find({"tipo": "aluno"}, {"_id": 0, "nome": 1, "matricula": 1, "turma": 1, "trilha": 1}))
    return jsonify({"alunos": alunos}), 200


@app.route('/gestor/editar-aluno/<aluno_matricula>', methods=['PUT'])
@token_required
def editar_aluno(aluno_matricula):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem editar alunos"}), 403

    data = request.json

    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": aluno_matricula})

    if not aluno:
        return jsonify({"message": "Aluno não encontrado"}), 404

    db['usuarios'].update_one(
        {"matricula": aluno_matricula},
        {"$set": {"nome": data['nome'], "turma": data['turma'], "trilha": data['trilha']}}
    )

    return jsonify({"message": "Aluno editado com sucesso"}), 200

@app.route('/gestor/deletar-aluno/<aluno_matricula>', methods=['DELETE'])
@token_required
def deletar_aluno(aluno_matricula):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem deletar alunos"}), 403

    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": aluno_matricula})

    if not aluno:
        return jsonify({"message": "Aluno não encontrado"}), 404

    db['usuarios'].delete_one({"matricula": aluno_matricula})

    return jsonify({"message": "Aluno deletado com sucesso"}), 200


@app.route('/gestor/lista-professores', methods=['GET'])
@token_required
def listar_professores(**kwargs):
    current_user = kwargs.get('current_user')

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem listar professores"}), 403

    db = get_db()
    professores = list(db['usuarios'].find(
        {"tipo": "professor"},
        {"_id": 0, "nome": 1, "matricula": 1, "materias": 1}
    ))

    return jsonify({"professores": professores}), 200


@app.route('/gestor/editar-professor/<professor_matricula>', methods=['PUT'])
@token_required
def editar_professor(professor_matricula):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem editar professores"}), 403

    data = request.json

    db = get_db()
    professor = db['usuarios'].find_one({"matricula": professor_matricula})

    if not professor:
        return jsonify({"message": "Professor não encontrado"}), 404

    db['usuarios'].update_one(
        {"matricula": professor_matricula},
        {"$set": {"nome": data['nome'], "materias": data['materias']}}
    )

    return jsonify({"message": "Professor editado com sucesso"}), 200

@app.route('/gestor/deletar-professor/<professor_matricula>', methods=['DELETE'])
@token_required
def deletar_professor(professor_matricula):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem deletar professores"}), 403

    db = get_db()
    professor = db['usuarios'].find_one({"matricula": professor_matricula})

    if not professor:
        return jsonify({"message": "Professor não encontrado"}), 404

    db['usuarios'].delete_one({"matricula": professor_matricula})

    return jsonify({"message": "Professor deletado com sucesso"}), 200

@app.route('/gestor/lista-gestores', methods=['GET'])
@token_required
def listar_gestores(**kwargs):
    current_user = kwargs.get('current_user')

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem listar gestores"}), 403

    db = get_db()
    gestores = list(db['usuarios'].find(
        {"tipo": "gestor"},
        {"_id": 0, "nome": 1, "matricula": 1}
    ))

    return jsonify({"gestores": gestores}), 200


@app.route('/gestor/editar-gestor/<gestor_matricula>', methods=['PUT'])
@token_required
def editar_gestor(gestor_matricula):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem editar gestores"}), 403

    data = request.json

    db = get_db()
    gestor = db['usuarios'].find_one({"matricula": gestor_matricula})

    if not gestor:
        return jsonify({"message": "Gestor não encontrado"}), 404

    db['usuarios'].update_one(
        {"matricula": gestor_matricula},
        {"$set": {"nome": data['nome']}}
    )

    return jsonify({"message": "Gestor editado com sucesso"}), 200

@app.route('/gestor/deletar-gestor/<gestor_matricula>', methods=['DELETE'])
@token_required
def deletar_gestor(gestor_matricula):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem deletar gestores"}), 403

    db = get_db()
    gestor = db['usuarios'].find_one({"matricula": gestor_matricula})

    if not gestor:
        return jsonify({"message": "Gestor não encontrado"}), 404

    db['usuarios'].delete_one({"matricula": gestor_matricula})

    return jsonify({"message": "Gestor deletado com sucesso"}), 200

@app.route('/gestor/criar-usuario', methods=['POST'])
@token_required
def criar_usuario():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem criar usuários"}), 403

    data = request.json

    matricula = data['matricula']
    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})
    if usuario:
        return jsonify({"message": "Matrícula já existe"}), 400
    
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
    nova_nota = {"simulado": data['simulado'], "nota": data['nota'], "id": len(aluno.get("notas", []))}

    # Atualizar as notas do aluno encontrado
    db['usuarios'].update_one(
        {"matricula": aluno_id},
        {"$push": {"notas": nova_nota}}
    )

    return jsonify({"message": "Nota adicionada com sucesso"}), 200


@app.route('/gestor/listar_notas/<aluno_matricula>', methods=['GET'])
@token_required
def listar_notas_aluno(aluno_matricula):
    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": aluno_matricula})

    if not aluno:
        return jsonify({"message": "Aluno não encontrado"}), 404

    return jsonify({"notas": aluno.get("notas", [])}), 200

@app.route('/gestor/<aluno_matricula>/editar-nota/<simulado_id>', methods=['PUT'])
@token_required
def editar_nota(aluno_matricula, simulado_id):
    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": aluno_matricula})

    if not aluno:
        return jsonify({"message": "Aluno não encontrado"}), 404

    aluno_notas = aluno.get("notas", [])
    nova_nota = request.json
    aluno_notas[int(simulado_id)] = nova_nota

    db['usuarios'].update_one(
        {"matricula": aluno_matricula},
        {"$set": {"notas": aluno_notas}}
    )

    return jsonify({"message": "Nota editada com sucesso"}), 200

@app.route('/gestor/<aluno_matricula>/deletar-nota/<simulado_id>', methods=['DELETE'])
@token_required
def deletar_nota(aluno_matricula, simulado_id):
    db = get_db()
    aluno = db['usuarios'].find_one({"matricula": aluno_matricula})

    if not aluno:
        return jsonify({"message": "Aluno não encontrado"}), 404

    # Converter simulado_id para inteiro, caso seja necessário
    simulado_id = int(simulado_id)

    # Filtrar as notas, removendo a que corresponde ao simulado_id
    notas_atualizadas = [nota for nota in aluno['notas'] if nota['id'] != simulado_id]

    # Verificar se houve alguma alteração (se o simulado existia)
    if len(notas_atualizadas) == len(aluno['notas']):
        return jsonify({"message": "Simulado não encontrado"}), 404

    # Atualizar o documento no banco de dados com as notas filtradas
    db['usuarios'].update_one(
        {"matricula": aluno_matricula},
        {"$set": {"notas": notas_atualizadas}}
    )

    return jsonify({"message": "Nota deletada com sucesso"}), 200

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

@app.route('/listar-avisos/<materia>', methods=['GET'])
@token_required
def listar_avisos(materia):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'gestor' and current_user.tipo != 'professor':
        return jsonify({"message": "Apenas gestores podem criar a grade horária"}), 403

    db = get_db()
    avisos = list(db['avisos'].find({"materia": materia}, {"_id": 1, "titulo": 1, "conteudo": 1, "autor": 1, "data": 1, "materia": 1}))
    for aviso in avisos:
        aviso['_id'] = str(aviso['_id'])
    return jsonify({"avisos": avisos}), 200

@app.route('/listar_conteudos/<materia>', methods=['GET'])
def listar_conteudos(materia):
    # Converte a matéria para minúsculas para garantir a correspondência correta
    materia_normalizada = materia.lower()
    
    db = get_db()

    conteudos = list(mongo.db['conteudos'].find({"materia": materia}, {"_id": 1, "titulo": 1, "descricao": 1, "materia": 1, "autor": 1, "data": 1, "arquivos": 1}))
    
    # Gera URLs de download para cada arquivo
    for conteudo in conteudos:
        conteudo['_id'] = str(conteudo['_id'])

    return jsonify({"conteudos": conteudos}), 200

@app.route('/criar-conteudo', methods=['POST'])
@token_required
def criar_conteudo():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])

    if current_user.tipo != 'professor' and current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas professores e gestores podem criar conteúdos"}), 403
    
    matricula = current_user.matricula
    db = get_db()
    usuario = db['usuarios'].find_one({"matricula": matricula})
    nome_autor = usuario['nome']
    
    # Obtém os dados de texto do FormData
    titulo = request.form.get('titulo')
    descricao = request.form.get('descricao')
    materia = request.form.get('materia')
    
    # Obtém os arquivos
    files = request.files.getlist('arquivos')

    arquivos = []
    for file in files:
        filename = file.filename  # Usar secure_filename para evitar problemas com nomes
        mongo.save_file(filename, file)
        id = mongo.db['fs.files'].find_one({"filename": filename})['_id']
        arquivos.append({"filename": filename, "id": str(id)})
    
    novo_conteudo = {
        "materia": materia,
        "titulo": titulo,
        "descricao": descricao,
        "autor": nome_autor,
        "data": datetime.datetime.now().strftime("%d/%m/%Y"),
        "arquivos": arquivos,
    }

    db = get_db()
    db['conteudos'].insert_one(novo_conteudo)
    return jsonify({"message": "Conteúdo criado com sucesso"}), 201

@app.route('/editar-conteudo/<conteudo_id>', methods=['PUT'])
@token_required
def editar_conteudo(conteudo_id):
    try:
        token = request.headers['Authorization'].split(" ")[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = load_user(data['matricula'])
        
        if current_user.tipo != 'professor' and current_user.tipo != 'gestor':
            return jsonify({"message": "Apenas professores e gestores podem editar conteúdos"}), 403

        # Pegando dados do FormData
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        
        db = get_db()
        conteudo = db['conteudos'].find_one({"_id": ObjectId(conteudo_id)})

        if not conteudo:
            return jsonify({"message": "Conteúdo não encontrado"}), 404
        
        # Processando arquivos
        arquivos_existentes = request.form.getlist('arquivosExistentes')
        arquivos = []

        print(arquivos_existentes)

        for id in arquivos_existentes:

            arquivos.append({"filename": mongo.db['fs.files'].find_one({"_id": ObjectId(id)})['filename'], "id": id})
        if 'arquivos' in request.files:
            files = request.files.getlist('arquivos')
            for file in files:
                if file.filename:  # Verifica se um arquivo foi realmente enviado
                    filename = file.filename  # Garante um nome de arquivo seguro
                    mongo.save_file(filename, file)
                    id = mongo.db['fs.files'].find_one({"filename": filename})['_id']
                    arquivos.append({"filename": filename, "id": str(id)})

        


        update_data = {
            "titulo": titulo,
            "descricao": descricao,
        }

        
        print(arquivos)

        update_data["arquivos"] = arquivos

        db['conteudos'].update_one(
            {"_id": ObjectId(conteudo_id)},
            {"$set": update_data}
        )

        return jsonify({"message": "Conteúdo editado com sucesso"}), 200
        
    except Exception as e:
        print(f"Erro ao editar conteúdo: {str(e)}")
        return jsonify({"message": "Erro ao editar conteúdo", "error": str(e)}), 500

@app.route('/deletar-conteudo/<conteudo_id>', methods=['DELETE'])
@token_required
def deletar_conteudo(conteudo_id):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])
    
    if current_user.tipo != 'professor' and current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas professores e gestores podem deletar conteúdos"}), 403

    db = get_db()
    conteudo = db['conteudos'].find_one({"_id": ObjectId(conteudo_id)})

    for arquivo in conteudo['arquivos']:
        db['fs.files'].delete_one({"_id": ObjectId(arquivo['id'])})

    if not conteudo:
        return jsonify({"message": "Conteúdo não encontrado"}), 404

    db['conteudos'].delete_one({"_id": ObjectId(conteudo_id)})

    return jsonify({"message": "Conteúdo deletado com sucesso"}), 200

@app.route('/deletar-arquivo/<id>', methods=['DELETE'])
@token_required
def deletar_arquivo(id):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])
    
    if current_user.tipo != 'professor' and current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas professores e gestores podem deletar arquivos"}), 403

    db = get_db()
    arquivo = db['fs.files'].find_one({"_id": ObjectId(id)})

    if not arquivo:
        return jsonify({"message": "Arquivo não encontrado"}), 404

    db['fs.files'].delete_one({"_id": ObjectId(id)})

    return jsonify({"message": "Arquivo deletado com sucesso"}), 200


@app.route('/baixar-arquivo/<id>', methods=['GET'])
@token_required
def baixar_arquivo(id):
    db = get_db()
    fs = gridfs.GridFS(db)
    try:
        # Verifica se o arquivo existe
        arquivo = db['fs.files'].find_one({"_id": ObjectId(id)})
        if not arquivo:
            return jsonify({"message": "Arquivo não encontrado"}), 404
        
        # Obtém o conteúdo do arquivo do GridFS
        grid_out =fs.get(ObjectId(id))
        file_content = grid_out.read()
        
        # Codifica o conteúdo em Base64
        base64_content = base64.b64encode(file_content).decode('utf-8')
        filename = arquivo['filename']

        # Retorna o conteúdo codificado
        return jsonify({"filename": filename, "content": base64_content}), 200
    
    except Exception as e:
        return jsonify({"message": "Erro ao baixar o arquivo", "error": str(e)}), 500


@app.route('/listar-aulas/<materia>', methods=['GET'])
@token_required
def listar_aulas(materia):
    db = get_db()
    aulas = list(db['grade_horaria'].find({"materia": materia}, {"_id": 1, "horarioInicio": 1, "horarioFim": 1}))
    for aula in aulas:
        aula['_id'] = str(aula['_id'])
    return jsonify({"aulas": aulas}), 200

@app.route('/criar-aula', methods=['POST'])
@token_required
def criar_aula():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])
    
    if current_user.tipo != 'gestor' :
        return jsonify({"message": "Apenas gestores podem criar aulas"}), 403
    
    data = request.json
    nova_aula = {
        "materia": data['materia'],
        "horarioInicio": data['horarioInicio'],
        "horarioFim": data['horarioFim']
    }
    db = get_db()
    db['grade_horaria'].insert_one(nova_aula)
    return jsonify({"message": "Aula adicionada com sucesso"}), 201

@app.route('/editar-aula/<aula_id>', methods=['PUT'])
@token_required
def editar_aula(aula_id):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])
    
    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem editar aulas"}), 403

    data = request.json
    db = get_db()
    aula = db['grade_horaria'].find_one({"_id": ObjectId(aula_id)})

    if not aula:
        return jsonify({"message": "Aula não encontrada"}), 404

    db['grade_horaria'].update_one(
        {"_id": ObjectId(aula_id)},
        {"$set": {"horarioInicio": data['horarioInicio'], "horarioFim": data['horarioFim']}}
    )

    return jsonify({"message": "Aula editada com sucesso"}), 200

@app.route('/deletar-aula/<aula_id>', methods=['DELETE'])
@token_required
def deletar_aula(aula_id):
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])
    
    if current_user.tipo != 'gestor':
        return jsonify({"message": "Apenas gestores podem deletar aulas"}), 403

    db = get_db()
    aula = db['grade_horaria'].find_one({"_id": ObjectId(aula_id)})

    if not aula:
        return jsonify({"message": "Aula não encontrada"}), 404

    db['grade_horaria'].delete_one({"_id": ObjectId(aula_id)})

    return jsonify({"message": "Aula deletada com sucesso"}), 200

@app.route('/professor/listar-materias', methods=['GET'])
@token_required
def listar_materias_professor():
    token = request.headers['Authorization'].split(" ")[1]
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    current_user = load_user(data['matricula'])
    
    if current_user.tipo != 'professor':
        return jsonify({"message": "Apenas professores podem deletar aulas"}), 403
    
    professor_matricula = current_user.matricula

    db = get_db()
    professor = db['usuarios'].find_one({"matricula": professor_matricula})

    if not professor:
        return jsonify({"message": "Professor não encontrado"}), 404
    

    return jsonify({"materias": professor.get("materias", [])}), 200


@app.route('/logout', methods=['POST'])
@token_required
def logout():
    logout_user()
    return jsonify({"message": "Logout bem-sucedido"}), 200

if __name__ == '__main__':
    app.run(debug=True)
