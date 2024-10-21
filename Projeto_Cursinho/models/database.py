from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Função para conectar ao MongoDB
def get_db():
    connection_string = "mongodb+srv://admin:admin@delomo.zxqnf.mongodb.net/?authSource=admin&retryWrites=true&w=majority"
    client = MongoClient(connection_string)
    db = client['JRs']
    return db

# Gerar hash das senhas
senha_joao = generate_password_hash("senha_joao123")
senha_maria = generate_password_hash("senha_maria123")
senha_lucas = generate_password_hash("senha_lucas123")
senha_ana = generate_password_hash("senha_ana123")

# Dados dos usuários
aluno_joao = {
    "nome": "João",
    "matricula": "12345",
    "senha": senha_joao,
    "tipo": "aluno",
    "notas": [
        {"disciplina": "Matemática", "nota": 9.5},
        {"disciplina": "História", "nota": 8.0}
    ]
}

aluno_maria = {
    "nome": "Maria",
    "matricula": "54321",
    "senha": senha_maria,
    "tipo": "aluno",
    "notas": [
        {"disciplina": "Matemática", "nota": 8.7},
        {"disciplina": "História", "nota": 9.0}
    ]
}

aluno_lucas = {
    "nome": "Lucas",
    "matricula": "67890",
    "senha": senha_lucas,
    "tipo": "aluno",
    "notas": [
        {"disciplina": "Física", "nota": 7.5},
        {"disciplina": "Química", "nota": 6.8}
    ]
}

professor_pedro = {
    "nome": "Pedro",
    "matricula": "13345",
    "senha": senha_joao,
    "tipo": "professor",
    "materias": ["Matemática"]
}

professora_ana = {
    "nome": "Ana",
    "matricula": "98765",
    "senha": senha_ana,
    "tipo": "professor",
    "materias": ["História"]
}

gestor_jorge = {
    "nome": "Jorge",
    "matricula": "1222",
    "senha": senha_joao,
    "tipo": "gestor"
}

# Função para inserir dados no MongoDB
def inserir_dados():
    db = get_db()
    try:
        # Inserir todos os usuários na collection 'usuarios'
        db['usuarios'].insert_many([
            aluno_joao, aluno_maria, aluno_lucas,
            professor_pedro, professora_ana, gestor_jorge
        ])
        print("Usuários inseridos com sucesso!")

        # Verificar se os dados foram inseridos corretamente
        usuarios = db['usuarios'].find()
        print("Usuários no banco de dados:")
        for usuario in usuarios:
            print(usuario)
    except Exception as e:
        print(f"Erro ao inserir os dados: {e}")

# Executar a função de inserção se o script for chamado diretamente
if __name__ == "__main__":
    inserir_dados()
