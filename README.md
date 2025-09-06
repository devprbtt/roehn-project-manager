# ROEHN Project Manager

**Uma aplicação Flask para gerenciar projetos do ROEHN WIZARD**

---

## 📋 Visão Geral

ROEHN Project Manager é uma aplicação web desenvolvida com Flask, destinada a facilitar o gerenciamento de projetos do ROEHN WIZARD. O sistema oferece funcionalidades para cadastro, acompanhamento e administração de projetos de forma intuitiva e eficiente.

---

## ✨ Funcionalidades

- Cadastro de projetos
- Listagem e busca de projetos
- Edição e remoção de projetos
- Gerenciamento de usuários (se aplicável)
- Interface amigável e responsiva
- Autenticação de usuários (se implementado)
- Relatórios e estatísticas (se implementado)

---

## 🚀 Instalação

Siga os passos abaixo para executar o projeto localmente:

### 1. Clone o repositório

```bash
git clone https://github.com/devprbtt/roehn-project-manager.git
cd roehn-project-manager
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure variáveis de ambiente

Crie um arquivo `.env` com as variáveis necessárias, como `FLASK_APP`, `FLASK_ENV` e credenciais de banco de dados.

### 5. Execute a aplicação

```bash
flask run
```

Acesse: [http://localhost:5000](http://localhost:5000)

---

## 🛠 Estrutura do Projeto

```text
roehn-project-manager/
├── app/                  # Código principal da aplicação
│   ├── static/           # Arquivos estáticos (CSS, JS, imagens)
│   ├── templates/        # Templates HTML
│   ├── __init__.py
│   └── routes.py
├── requirements.txt      # Dependências Python
├── README.md             # Documentação do projeto
└── .env                  # Configurações de ambiente
```

---

## 📑 Uso

1. Inicialize o servidor Flask como mostrado acima.
2. Acesse o endereço local no navegador.
3. Cadastre e gerencie projetos conforme necessário.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork este repositório
2. Crie uma branch: `git checkout -b minha-feature`
3. Faça suas alterações
4. Realize um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

## 📬 Contato

Dúvidas ou sugestões?  
Entre em contato pelo GitHub: [devprbtt](https://github.com/devprbtt)

---

## 📚 Referências

- [Flask Documentation](https://flask.palletsprojects.com/)
