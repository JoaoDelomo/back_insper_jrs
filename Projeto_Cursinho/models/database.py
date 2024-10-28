from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Função para conectar ao MongoDB
def get_db():
    connection_string = "mongodb+srv://admin:admin@delomo.zxqnf.mongodb.net/?authSource=admin&retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    db = client['JRs']
    return db

# Gerar hash das senhas
senha_comum = generate_password_hash("senha_comum123")

# Dados dos usuários
aluno_joao = {
    "nome": "João",
    "matricula": "12345",
    "usuario": "joao123",
    "senha": senha_comum,
    "tipo": "aluno",
    "trilha": "naturais",
    "turma": "presencial",
    "materias": ["Matemática", "Português", "Naturais"],
    "notas": [
        {"simulado": "Simulado 1", "nota": 8.5},
        {"simulado": "Simulado 2", "nota": 9.0}
    ]
}

aluno_maria = {
    "nome": "Maria",
    "matricula": "54321",
    "usuario": "maria123",
    "senha": senha_comum,
    "tipo": "aluno",
    "trilha": "humanas",
    "turma": "online",
    "materias": ["Matemática", "Português", "Humanas"],
    "notas": [
        {"id": 1, "simulado": "Simulado 1", "nota": 7.5},
        {"id": 2, "simulado": "Simulado 2", "nota": 8.8},

    ]
}

professor_pedro = {
    "nome": "Pedro",
    "matricula": "13345",
    "usuario": "pedro123",
    "senha": senha_comum,
    "tipo": "professor",
    "materias": ["Matemática", "Naturais"],
    "avisos": [
        {
            "materia": "Matemática",
            "titulo": "Aviso Importante",
            "mensagem": "A aula foi adiada para sexta-feira."
        }
    ],
    "conteudos": [
        {
            "materia": "Matemática",
            "titulo": "Funções Quadráticas",
            "descricao": "Estudo sobre gráficos e raízes."
        }
    ]
}

gestor_ana = {
    "nome": "Ana",
    "matricula": "98765",
    "usuario": "ana123",
    "senha": senha_comum,
    "tipo": "gestor",
    "avisos": [
        {
            "materia": None,
            "titulo": "Aviso Geral",
            "mensagem": "Bem-vindos ao semestre!"
        }
    ]
}

# Dados da grade horária
grade_horaria = [
    {
        "materia": "Matemática",
        "dias": ["Segunda-feira", "Quarta-feira"],
        "horario": "08:00 - 10:00"
    },
    {
        "materia": "Português",
        "dias": ["Terça-feira", "Quinta-feira"],
        "horario": "10:00 - 12:00"
    },
    {
        "materia": "Naturais",
        "dias": ["Sexta-feira"],
        "horario": "14:00 - 16:00"
    },
    {
        "materia": "Humanas",
        "dias": ["Quarta-feira"],
        "horario": "16:00 - 18:00"
    }
]

# Função para inserir dados no MongoDB
def inserir_dados():
    db = get_db()
    try:
        # Inserir usuários na collection 'usuarios'
        db['usuarios'].insert_many([
            aluno_joao, aluno_maria, professor_pedro, gestor_ana
        ])
        print("Usuários inseridos com sucesso!")

        # Inserir a grade horária na collection 'grade_horaria'
        db['grade_horaria'].insert_many(grade_horaria)
        print("Grade horária inserida com sucesso!")

        # Verificar se os dados foram inseridos corretamente
        print("Usuários no banco de dados:")
        usuarios = db['usuarios'].find()
        for usuario in usuarios:
            print(usuario)

        print("\nGrade horária no banco de dados:")
        horarios = db['grade_horaria'].find()
        for horario in horarios:
            print(horario)

    except Exception as e:
        print(f"Erro ao inserir os dados: {e}")

# Executar a função de inserção se o script for chamado diretamente
if __name__ == "__main__":
    inserir_dados()
