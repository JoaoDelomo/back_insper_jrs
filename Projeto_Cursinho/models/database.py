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

# Dados dos usuários
aluno_joao = {
    "nome": "João",
    "matricula": "12345",
    "senha": senha_joao,
    "tipo": "aluno",
    "notas": [
        {"disciplina": "Matemática", "nota": 9.5},
        {"disciplina": "História", "nota": 8.0}
    ],
    "avisos": [
        {"titulo": "Reunião de pais", "mensagem": "A reunião será na próxima sexta-feira."},
        {"titulo": "Férias escolares", "mensagem": "As férias começam em 20 de dezembro."}
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
    ],
    "avisos": [
        {"titulo": "Entrega de trabalhos", "mensagem": "Os trabalhos finais devem ser entregues até o dia 15 de dezembro."},
        {"titulo": "Reunião de pais", "mensagem": "A reunião será na próxima segunda-feira."}
    ]
}

professor_pedro = {
    "nome": "Pedro",
    "matricula": "13345",
    "senha": senha_joao,  # Reutilizando a senha do João para simplificar
    "tipo": "professor",
    "materias": ["Matemática"],
    "avisos": [
        {"titulo": "Prova 3", "mensagem": "A prova 3 será no dia 10/12."}
    ],
    "grade_horaria": [
        {"Matemática": "8:00"}
    ]
}

gestor_jorge = {
    "nome": "Jorge",
    "matricula": "1222",
    "senha": senha_joao,  # Reutilizando a senha do João para simplificar
    "tipo": "gestor",
    "materias": [],
    "grade_horaria": []
}

# Função para inserir dados no MongoDB
def inserir_dados():
    db = get_db()
    try:
        # Inserir os usuários (alunos, professores e gestores) na collection 'usuarios'
        db['usuarios'].insert_many([aluno_joao, aluno_maria, professor_pedro, gestor_jorge])
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
