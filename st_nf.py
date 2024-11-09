import streamlit as st
import re
import pandas as pd
import numpy as np
from io import BytesIO
import plotly.express as px

# Definir as credenciais corretas
USERNAME = "pretorian"
PASSWORD = "Pretorian123"

# Função de autenticação
def authenticate(username, password):
    return username == USERNAME and password == PASSWORD

# Interface do Streamlit para a página de login
def login_page():
    st.title("Login")
    st.write("Digite suas credenciais para acessar.")

    # Campos de login e senha
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    # Botão de login
    if st.button("Entrar"):
        if authenticate(username, password):
            st.session_state["authenticated"] = True
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos.")

# Função para extrair números de NF ou CTE do texto
def extrair_numero_nf_cte(texto):
    padrao_nf_cte = r'(NF|nf|Nf|CTE|NFSE|NFSe|NFse|nfse|NF°|nf°|Nf°|Nota Fiscal| nota fiscal| Nota Fiscal de Serviço|nota fiscal de serviço)[\s°NFSSE-]?\s?(\d+)'
    padrao_devolucao = r'(DEVOLUÇÃO|Devolução|Devolucao|devolução|devolucao|Devolução de Produto|devolução de produto)[\s°NFSSE-]?\s?(\d+)'
    
    correspondencias_nf_cte = re.search(padrao_nf_cte, texto)
    correspondencias_devolucao = re.search(padrao_devolucao, texto)

    if correspondencias_nf_cte:
        return correspondencias_nf_cte.group(2)
    elif correspondencias_devolucao:
        return correspondencias_devolucao.group(2)
    else:
        correspondencias_numero = re.search(r'\b\d+\b', texto)
        if correspondencias_numero:
            return correspondencias_numero.group()
        else:
            return None

# Função para adicionar 'NF' antes de um número no final do texto
def adicionar_nf(texto):
    padrao_numero = r'(\d+)$'
    correspondencia_numero = re.search(padrao_numero, texto)
    
    if correspondencia_numero:
        numero = correspondencia_numero.group(1)
        novo_texto = texto[:correspondencia_numero.start(1)] + "NF " + numero
        return novo_texto
    else:
        return texto

# Página principal após login
def main_page():
    #st.title("Bem-vindo")
    #st.write("Parabéns, você está autenticado.")
    
    st.title("Conciliação de Notas Fiscais")
    st.write("Carregue o arquivo Excel para iniciar o processo de conciliação.")

    # Upload do arquivo Excel
    uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])

    if uploaded_file:
        # Ler o arquivo para um DataFrame
        razao = pd.read_excel(uploaded_file, engine='openpyxl')
        razao = razao[['datalan', 'codi_lote', 'valdeb', 'valcre', 'historico']]
        
        # Preparar os DataFrames de débito e crédito
        razaideb = razao[['datalan', 'codi_lote', 'valdeb', 'historico']]
        razao['valcre'] *= -1
        razao['historico1'] = '' + razao['historico'].apply(extrair_numero_nf_cte)
        
        razaocred = razao[['datalan', 'codi_lote', 'historico', 'valcre', 'historico1']]
        razaideb = razao[['datalan', 'codi_lote', 'historico', 'valdeb', 'historico1']]
        
        razaocred = razaocred.fillna('')
        razaideb = razaideb.fillna('')
        
        razaocred.rename(columns={'datalan': 'data', 'valcre': 'valor', 'historico1': 'NF'}, inplace=True)
        razaideb.rename(columns={'datalan': 'data', 'valdeb': 'valor', 'historico1': 'NF'}, inplace=True)
        
        # Concatenar os DataFrames de débito e crédito
        superzarao = pd.concat([razaideb, razaocred], keys=['debito', 'credito'])
        superzarao['tipo'] = np.where(superzarao['historico'].str.contains('DEVOLUÇÃO', case=False), 'Devolução', 'Normal')
        
        # Filtrar devoluções
        devolucoes = superzarao[superzarao['tipo'] == 'Devolução']
        superzarao = superzarao.sort_values(by='valor')
        superzarao['NF_conciliada'] = superzarao['NF'].drop_duplicates()
        superzarao = superzarao[superzarao['valor'] != 0]
        superzarao['historico'] = superzarao['historico'].apply(adicionar_nf)
        
        devolucoes['NF_original'] = devolucoes['historico'].str.findall(r'(NF|nf|Nf)\s?(\d+)').str[1]
        devolucoes['NF_original'] = devolucoes['NF_original'].astype(str)
        parts = devolucoes['NF_original'].str.split(r"[(),']") 
        devolucoes['NF_original'] = parts.str.join('')
        
        # Agrupar e consolidar resultados
        superzarao['NF'] = superzarao['historico'].str.split().str[-1]
        resultado = superzarao.groupby('NF')['valor'].sum().reset_index()
        resultado['valor'] = round(resultado['valor'], 2)
        resultado['status'] = resultado['valor'].apply(lambda x: 'Conciliado' if x == 0 else ('Valor a Pagar' if x < 0 else 'Falta NF'))
        status_counts = resultado['status'].value_counts()

        # Exibir totalizador de status
        st.write("### Totalizador de Status")
        st.write(status_counts)

        # Preparar os dados para o gráfico de barras do Plotly
        status_df = pd.DataFrame({
            'Status': status_counts.index,
            'Quantidade': status_counts.values
        })

        # Exibir gráfico de barras no Streamlit com três cores distintas e rótulos
        st.write("### Gráfico de Status")
        colors = ['#4CAF50', '#FFC107', '#F44336']  # Cores para Conciliado, Falta NF e Valor a Pagar
        fig = px.bar(status_df, x='Status', y='Quantidade', color='Status', text='Quantidade',
                     color_discrete_sequence=colors)
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, width=700, height=400)
        st.plotly_chart(fig)

        # Exibir tabelas adicionais
        st.write("### Resumo por NF")
        st.write(resultado)

        st.write("### Conciliação Analítica")
        st.write(superzarao)

        st.write("### Notas Devolução")
        st.write(devolucoes)
        
        # Função para download do arquivo gerado
        def to_excel(df_dict):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for sheet_name, df in df_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            return output.getvalue()
        
        # Botão para baixar o arquivo Excel gerado
        df_dict = {
            "Totalizador": status_counts.to_frame(),
            "Resumo por NF": resultado,
            "Conciliação Analítica": superzarao,
            "Notas Devolução": devolucoes
        }
        excel_data = to_excel(df_dict)

        st.download_button(
            label="Baixar relatório de conciliação",
            data=excel_data,
            file_name="conciliacao_fornecedor.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Adicionando a assinatura no rodapé
    st.write("---")
    st.write("Criado por Adolfo Hugo Silva")

# Lógica principal de verificação de login
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_page()
else:
    main_page()
