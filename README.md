# Projeto: Sistema de Conciliação de Notas Fiscais com Streamlit

## Descrição

Este projeto consiste em uma aplicação web desenvolvida em Python utilizando a biblioteca Streamlit, cujo objetivo é automatizar e simplificar o processo de conciliação de notas fiscais (NF) e notas de devolução. A aplicação realiza a leitura de um arquivo Excel contendo dados contábeis, extrai informações de NF e devoluções, consolida e classifica essas informações e exibe um resumo gráfico. Ao final do processamento, o sistema permite o download de um relatório de conciliação detalhado.

## Funcionalidades

- **Autenticação de Usuário**: Implementação de uma tela de login com verificação de credenciais para controlar o acesso à aplicação.
- **Extração de Informações de NF e Devoluções**: Utilização de expressões regulares para capturar números de NF e devoluções de produtos nos textos dos registros.
- **Conciliação e Classificação de Dados**:
  - Filtragem de registros de débito e crédito no arquivo carregado.
  - Agrupamento e cálculo dos valores conciliados, separados entre "Conciliado", "Valor a Pagar" e "Falta NF".
- **Visualização e Análise dos Resultados**:
  - Exibição de um gráfico de barras interativo com o total de registros para cada status de conciliação.
  - Visualização dos detalhes de cada NF e notas de devolução.
- **Exportação de Relatório**: Geração de um arquivo Excel consolidado para download, contendo as informações de conciliação.

## Estrutura do Código

1. **Login e Autenticação**: O código inicializa a aplicação com uma tela de login e verifica se o usuário possui as credenciais corretas antes de liberar o acesso ao conteúdo.
   
2. **Processamento do Arquivo Excel**:
   - Ao carregar o arquivo, os dados são importados para um DataFrame, que é manipulado para separar informações de débito e crédito.
   - A função `extrair_numero_nf_cte` é usada para identificar e extrair números de NF e devoluções.
   - As notas de devolução são separadas e analisadas especificamente para comparações com as notas fiscais originais.

3. **Consolidação e Agrupamento**:
   - Cria-se um DataFrame consolidado de todas as movimentações, com identificação de devoluções e tipo de operação (crédito ou débito).
   - Os dados são agrupados e classificados conforme o status ("Conciliado", "Valor a Pagar", "Falta NF").

4. **Visualização**:
   - Um gráfico de barras interativo é gerado para apresentar o total de registros em cada status.
   - Detalhes de cada NF e devoluções são exibidos em tabelas.

5. **Exportação de Relatório**:
   - Utilizando a função `to_excel`, o sistema gera um arquivo Excel contendo o resumo e as análises detalhadas, disponível para download.

## Requisitos

- **Python 3.7+**
- Bibliotecas:
  - `streamlit`
  - `pandas`
  - `numpy`
  - `openpyxl`
  - `plotly`
  
Para instalar as dependências, execute:
```bash
pip install streamlit pandas numpy openpyxl plotly
```

## Executando a Aplicação

1. Clone este repositório e navegue até a pasta do projeto.
2. Execute o comando:
   ```bash
   streamlit run nome_do_arquivo.py
   ```
3. Acesse a aplicação no seu navegador no endereço: `http://localhost:8501`

## Contribuição

Este projeto foi desenvolvido por Adolfo Hugo Silva. Sugestões, melhorias e colaborações são bem-vindas.
