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


usuario1 = {
    "nome": "João",
    "matricula": "12345",
    "senha": senha_joao,
    "tipo": "aluno",

    "materias": [
        {
            "nome": "Matemática",
            "professor": "Pedro",
            "notas": [
                {"atividade": "Prova 1", "nota": 9.5},
                {"atividade": "Prova 2", "nota": 8.0}
            ],
            "avisos": [
                {"titulo": "Prova 3", "mensagem": "A prova 3 será no dia 10/12."}
            ]
        },
        {
            "nome": "História",
            "professor": "Ana",
            "notas": [
                {"atividade": "Prova 1", "nota": 8.0},
                {"atividade": "Prova 2", "nota": 7.5}
            ],
            "avisos": [
                {"titulo": "Trabalho final", 
                 "conteudo": "O trabalho final deve ser entregue até o dia 15/12.",
                 "data": "10-12-2021",}
            ]
        }
    ],

    "grade_horaria": [
        {"Matematica": "8:00"},
        {"História": "10:00"}
    ]
} 


usuario3 = {
    "nome": "Pedro",
    "matricula": "13345",
    "senha": senha_joao,
    "tipo": "professor",

    "materias": ["matematica"],

    "grade_horaria": [
        {"Matematica": "8:00"}
    ]
}

usuario4 = {
    "nome": "Ana",
    "matricula": "44321",
    "senha": senha_maria,
    "tipo": "professor",

    "materias": ["história"],

    "grade_horaria": [
        {"História": "10:00"}
    ]

}

usuario5= {
    "nome": "Jorge",
    "matricula": "1222",
    "senha": senha_joao,
    "tipo": "gestor",
    "materias": [],
    "grade_horaria": []
}

# Inserir os alunos no MongoDB
db = get_db()
db['alunos'].insert_many([aluno_joao, aluno_maria])

print("João e Maria inseridos com sucesso!")
