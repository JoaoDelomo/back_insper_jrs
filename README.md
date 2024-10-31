
# Back-end da plataforma desenvolvida para o Cursinho Insper durante a segunda fase do processo seletivo da Insper Jr 2024.2

**Dupla**: Guilherme Kaidei e João Delomo

Este back-end foi construído com Flask (Python). Abaixo estão as instruções para baixar, instalar as dependências e rodar a aplicação localmente.

## Pré-requisitos

Certifique-se de que você tenha instalado:
- **Python** (versão 3.8 ou superior)
- **pip** (gerenciador de pacotes do Python)

## Como baixar e rodar o projeto

### 1. Clone o repositório

Clone o repositório em sua máquina local usando o comando:

```bash
git clone https://github.com/seu_usuario/back-end-jr
```

### 2. Crie e ative um ambiente virtual

Navegue até a pasta do projeto e crie um ambiente virtual com os comandos:

```bash
python -m venv venv
```

Ative o ambiente virtual:

- **No Windows**:
  ```bash
  venv\Scripts\activate
  ```
- **No MacOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 3. Instale as dependências

Instale as dependências listadas no arquivo requirements.txt:

```bash
pip install -r requirements.txt
```

### 4. Rode a aplicação

Execute o seguinte comando para iniciar o servidor Flask:

```bash
flask run
```

A aplicação estará disponível em [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

### Observação sobre CORS

Caso encontre problemas de CORS ao fazer requisições, verifique se está utilizando um navegador que não altera os headers de requisição. Alguns navegadores, como o Brave, podem fazer isso. Para contornar, utilize a extensão "CORS Unblock" ou um navegador alternativo para acessar a aplicação.
