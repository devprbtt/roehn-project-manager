# Documentação Técnica Detalhada – ROEHN Project Manager

Este documento cobre todas as funções, rotas, modelos e scripts utilitários do projeto.  
Inclui:  
- Rotas e funções Flask  
- Modelos SQLAlchemy: campos e relações  
- Funções auxiliares e utilitárias  
- Funções JavaScript usadas nos templates  

---

## 1. Modelos SQLAlchemy

### Projeto

```python
class Projeto(db.Model):
    id: int
    nome: str
    user_id: int
    areas: relationship to Area
    # Métodos: __repr__, etc.
```
- **Descrição:** Representa um projeto cadastrado pelo usuário.  
- **Relações:** Um projeto possui várias áreas.

### Area

```python
class Area(db.Model):
    id: int
    nome: str
    projeto_id: int
    ambientes: relationship to Ambiente
```
- **Descrição:** Área dentro do projeto (ex: "Sala", "Cozinha").
- **Relações:** Uma área possui vários ambientes. Pertence a um projeto.

### Ambiente

```python
class Ambiente(db.Model):
    id: int
    nome: str
    area_id: int
    circuitos: relationship to Circuito
```
- **Descrição:** Ambiente físico dentro de uma área.
- **Relações:** Pertence à área; possui vários circuitos.

### Circuito

```python
class Circuito(db.Model):
    id: int
    identificador: str
    nome: str
    tipo: str
    ambiente_id: int
    sak: int
    quantidade_saks: int
    vinculacao: relationship to Vinculacao (one-to-one)
```
- **Descrição:** Representa um circuito (ex: luz, persiana, HVAC).
- **Relações:** Pertence a um ambiente; pode ter uma vinculação.

### Modulo

```python
class Modulo(db.Model):
    id: int
    nome: str
    tipo: str
    quantidade_canais: int
    projeto_id: int
    vinculacoes: relationship to Vinculacao
```
- **Descrição:** Módulo físico de automação.
- **Relações:** Pertence ao projeto; possui várias vinculações.

### Vinculacao

```python
class Vinculacao(db.Model):
    id: int
    circuito_id: int
    modulo_id: int
    canal: int
    circuito: relationship to Circuito
    modulo: relationship to Modulo
```
- **Descrição:** Relaciona um circuito a um canal de módulo.

---

## 2. Rotas e Funções Flask

### index()
- **Rota:** `/`  
- **Método:** GET  
- **Descrição:** Página inicial, lista projetos do usuário.  
- **Retorno:** Renderiza `index.html`.

### selecionar_projeto(projeto_id)
- **Rota:** `/projeto/<int:projeto_id>`  
- **Método:** GET  
- **Parâmetros:** projeto_id  
- **Descrição:** Seleciona projeto ativo e armazena na sessão.  
- **Retorno:** Redireciona para a página inicial.

### novo_projeto()
- **Rota:** `/projeto/novo`  
- **Método:** POST  
- **Parâmetros:** nome (form)  
- **Descrição:** Cria novo projeto para o usuário.  
- **Retorno:** JSON com sucesso/erro.

### excluir_projeto(projeto_id)
- **Rota:** `/projeto/<int:projeto_id>`  
- **Método:** DELETE  
- **Parâmetros:** projeto_id  
- **Descrição:** Exclui projeto e limpa sessão se necessário.  
- **Retorno:** JSON.

### areas() / excluir_area(id)
- **Rota:** `/areas`, `/areas/<int:id>`  
- **Método:** GET, POST, DELETE  
- **Parâmetros:** nome (form), id  
- **Descrição:** Lista/cadastra áreas, exclui área se não houver ambientes vinculados.  
- **Retorno:** Renderiza HTML ou JSON.

### ambientes() / excluir_ambiente(id)
- **Rota:** `/ambientes`, `/ambientes/<int:id>`  
- **Método:** GET, POST, DELETE  
- **Parâmetros:** nome, area_id, id  
- **Descrição:** Lista/cadastra ambientes, exclui ambiente se não houver circuitos.  
- **Retorno:** HTML ou JSON.

### circuitos() / excluir_circuito(id)
- **Rota:** `/circuitos`, `/circuitos/<int:id>`  
- **Método:** GET, POST, DELETE  
- **Parâmetros:** nome, tipo, ambiente_id, id  
- **Descrição:** Lista/cadastra circuitos, exclui circuito se não houver vinculação.  
- **Retorno:** HTML ou JSON.

### modulos() / excluir_modulo(id)
- **Rota:** `/modulos`, `/modulos/<int:id>`  
- **Método:** GET, POST, DELETE  
- **Parâmetros:** nome, tipo, id  
- **Descrição:** Lista/cadastra módulos, exclui módulo se não houver vinculações.  
- **Retorno:** HTML ou JSON.

### vinculacao() / excluir_vinculacao(id)
- **Rota:** `/vinculacao`, `/vinculacao/<int:id>`  
- **Método:** GET, POST, DELETE  
- **Parâmetros:** circuito_id, modulo_id, canal, id  
- **Descrição:** Lista/cadastra vinculações, exclui vinculação.  
- **Retorno:** HTML ou JSON.

### exportar_csv()
- **Rota:** `/exportar-csv`  
- **Método:** GET  
- **Descrição:** Exporta todos os circuitos do projeto em CSV.  
- **Retorno:** Arquivo CSV.

### exportar_projeto(projeto_id)
- **Rota:** `/exportar-projeto/<int:projeto_id>`  
- **Método:** GET  
- **Descrição:** Exporta dados completos do projeto em JSON.  
- **Retorno:** Arquivo JSON.

### importar_projeto()
- **Rota:** `/importar-projeto`  
- **Método:** POST  
- **Descrição:** Importa projeto a partir de arquivo JSON.  
- **Retorno:** JSON.

### exportar_pdf(projeto_id)
- **Rota:** `/exportar-pdf/<int:projeto_id>`  
- **Método:** GET  
- **Descrição:** Gera relatório PDF do projeto.  
- **Retorno:** Arquivo PDF.

---

## 3. Funções Auxiliares Python (helpers)

- Funções para conversão, manipulação de SAK, validação de permissões, etc., podem estar em arquivos separados ou no corpo das rotas.  
- Docstrings devem descrever propósito, parâmetros e retorno.

Exemplo:
```python
def calcular_proximo_sak(tipo, projeto_id):
    """
    Calcula o próximo SAK disponível para um circuito.
    Parâmetros:
        tipo: str - Tipo do circuito
        projeto_id: int - Projeto de referência
    Retorno:
        int - SAK sugerido
    """
    # Implementação...
```

---

## 4. Funções JavaScript (Templates e Static)

### static/js/script.js

- **showAlert(message, type='success')**
  - Exibe mensagem de alerta Bootstrap por 5 segundos.
  - Parâmetros: mensagem (string), tipo (string - success/danger/warning).
  - Retorno: nenhum (efeito visual na UI).
  - Uso: pode ser chamado de qualquer template.

### index.html

- **selecionarProjeto(id)**
  - Redireciona usuário para a página do projeto.
- **exportarProjeto(id)**
  - Redireciona para exportação do projeto.
- **excluirProjeto(id)**
  - Envia requisição DELETE, recarrega página ao sucesso.
- **importarProjeto()**
  - Envia arquivo via POST para importar projeto.
- **editarProjeto(id, nome)**
  - Abre modal de edição.
- **salvarEdicaoProjeto()**
  - Atualiza nome do projeto via PUT.

### areas.html / ambientes.html / circuitos.html

- **excluirArea(id)**, **excluirAmbiente(id)**, **excluirCircuito(id)**
  - Envia requisição DELETE, atualizando UI conforme resposta.

### vinculacao.html

- **atualizarCompatibilidade()**, **atualizarCanais()**
  - Atualizam opções de módulos/canais.
- **excluirVinculacao(id)**
  - Exclui vinculação via requisição DELETE.

### projeto.html

- **formatPhoneNumber(input)**, **formatIPAddress(input)**
  - Funções de formatação de campos.
- **Validação do formulário**
  - Impede submissão se dados estiverem inválidos.

---

## 5. Sugestões de Melhoria

- Adicionar docstrings em todas funções Python.
- Comentar funções JS com JSDoc.
- Documentar helpers e métodos personalizados dos modelos.
- Manter este documento sempre atualizado.

---

Dúvidas? Fale com o mantenedor ou abra uma issue 😉
