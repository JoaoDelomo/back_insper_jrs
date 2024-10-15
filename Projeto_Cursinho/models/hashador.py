from werkzeug.security import generate_password_hash
from models.database import get_db

# Gerar hash para as senhas
senha_joao = generate_password_hash("senha_joao123")
senha_maria = generate_password_hash("senha_maria123")

# Aluno João
aluno_joao = {
  "nome": "João",
  "matricula": "12345",
  "senha": senha_joao,  # Senha em hash
  "notas": [
    {
      "disciplina": "Matemática",
      "nota": 9.5
    },
    {
      "disciplina": "História",
      "nota": 8.0
    }
  ],
  "avisos": [
    {
      "titulo": "Reunião de pais",
      "mensagem": "A reunião será na próxima sexta-feira."
    },
    {
      "titulo": "Férias escolares",
      "mensagem": "As férias começam em 20 de dezembro."
    }
  ]
}

# Aluno Maria
aluno_maria = {
  "nome": "Maria",
  "matricula": "54321",
  "senha": senha_maria,  # Senha em hash
  "notas": [
    {
      "disciplina": "Matemática",
      "nota": 8.7
    },
    {
      "disciplina": "História",
      "nota": 9.0
    }
  ],
  "avisos": [
    {
      "titulo": "Entrega de trabalhos",
      "mensagem": "Os trabalhos finais devem ser entregues até o dia 15 de dezembro."
    },
    {
      "titulo": "Reunião de pais",
      "mensagem": "A reunião será na próxima segunda-feira."
    }
  ]
}

# Inserir os alunos no MongoDB
db = get_db()
db['alunos'].insert_many([aluno_joao, aluno_maria])

print("João e Maria inseridos com sucesso!")
