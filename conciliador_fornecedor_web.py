import re
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# Função para extrair apenas o número de NF ou CTE do texto usando expressões regulares
def extrair_numero_nf_cte(texto):
    padrao = r'(NF|nf|Nf|CTE|NFSE|NFSe|NFse|nfse|NF°|nf°|Nf°|Nota Fiscal| nota fiscal| Nota Fiscal de Serviço|nota fiscal de serviço)[\s°NFSSE-]?\s?(\d+)'
    correspondencias = re.search(padrao, texto)
    if correspondencias:
        return correspondencias.group(2)
    else:
        correspondencias_numero = re.search(r'\b\d+\b', texto)
        return correspondencias_numero.group() if correspondencias_numero else None

# Interface do Streamlit
st.title("Conciliação de Notas Fiscais")

# Upload do arquivo
arquivo = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])
if arquivo is not None:
    razao = pd.read_excel(arquivo, engine='openpyxl')
    razao = razao[['datalan','codi_lote','valdeb','valcre','historico']]
    
    razaideb = razao[['datalan','codi_lote','valdeb', 'historico']]
    razao['valcre'] *= -1
    razao['historico1'] = razao['historico'].apply(extrair_numero_nf_cte)
    
    razaocred = razao[['datalan','codi_lote','historico','valcre','historico1']]
    razaideb = razao[['datalan','codi_lote','historico','valdeb', 'historico1']]
    razaocred = razaocred.fillna('')
    razaideb = razaideb.fillna('')
    
    razaocred.rename(columns={'datalan':'data','valcre':'valor', 'historico1':'NF'}, inplace=True)
    razaideb.rename(columns={'datalan':'data','valdeb':'valor', 'historico1':'NF'}, inplace=True)
    
    superzarao = pd.concat([razaideb, razaocred], keys=['debito','credito'])
    superzarao = superzarao.sort_values(by='valor')
    superzarao['NF_conciliada'] = superzarao['NF'].drop_duplicates()
    superzarao['saldo'] = ''
    superzarao = superzarao[superzarao['valor'] != 0]
    
    superzarao2 = superzarao[['NF', 'valor']]
    superzarao2 = superzarao.groupby('NF')['valor'].sum().reset_index()
    superzarao2['status'] = superzarao2['valor'].apply(lambda x: 'Conciliado' if x == 0 else ('Valor a Pagar' if x < 0 else 'Falta NF'))
    
    # Exibição no Streamlit
    st.write("## Resumo por NF")
    st.dataframe(superzarao2)
    
    # Gráfico de colunas com a contagem de cada status de NF
    status_count = superzarao2['status'].value_counts().reset_index()
    status_count.columns = ['Status', 'Quantidade']
    
    # Usando Altair para criar o gráfico de colunas com rótulos
    chart = alt.Chart(status_count).mark_bar().encode(
        x=alt.X('Status', sort='-y'),
        y='Quantidade',
        color='Status'
    ).properties(
        title="Status das Notas Fiscais (NF)"
    )

    # Adicionando os rótulos de dados
    text = chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-5  # posição do rótulo acima das barras
    ).encode(
        text='Quantidade:Q'
    )

    st.altair_chart(chart + text, use_container_width=True)
    
    st.write("## Conciliação Analítica")
    st.dataframe(superzarao)
    
    # Download do resultado
    with pd.ExcelWriter('conciliacao_fornecedor.xlsx', engine='openpyxl') as writer:
        superzarao2.to_excel(writer, sheet_name='Resumo por NF')
        superzarao.to_excel(writer, sheet_name='Conciliação Analítica')
    
    with open("conciliacao_fornecedor.xlsx", "rb") as file:
        st.download_button("Baixar Conciliação", file, "conciliacao_fornecedor.xlsx")
