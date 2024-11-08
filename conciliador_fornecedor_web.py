import re
import pandas as pd
import streamlit as st
import altair as alt

# Função para extrair o último número de NF ou CTE do texto usando expressões regulares
def extrair_numero_nf_cte(texto):
    # Padrão para encontrar NF ou CTE no texto
    padrao = r'(NF|nf|Nf|CTE|NFSE|NFSe|NFse|nfse|NF°|nf°|Nf°|Nota Fiscal|nota fiscal|Nota Fiscal de Serviço|nota fiscal de serviço)[\s°NFSSE-]?\s?(\d+)'

    # Procurar por correspondências no texto usando o padrão de regex
    correspondencias = re.findall(padrao, texto)
    
    # Se encontrar algum número associado à NF/CTE, retornar o último número
    if correspondencias:
        return correspondencias[-1][1]  # Pega o último número encontrado
    else:
        # Se não encontrar uma NF/CTE específica, procurar todos os números
        correspondencias_numero = re.findall(r'\b\d+\b', texto)
        if correspondencias_numero:
            return correspondencias_numero[-1]  # Retorna o último número encontrado
        else:
            return None  # Se não encontrar nenhum número

# Interface do Streamlit
st.title("Conciliação de Notas Fiscais")

# Upload do arquivo Excel
arquivo = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])

if arquivo is not None:
    # Carregar o arquivo Excel
    razao = pd.read_excel(arquivo, engine='openpyxl')
    
    # Filtrar as colunas relevantes
    razao = razao[['datalan', 'codi_lote', 'valdeb', 'valcre', 'historico']]
    
    # Processamento dos débitos e créditos
    razaideb = razao[['datalan', 'codi_lote', 'valdeb', 'historico']]
    razao['valcre'] *= -1  # Ajustando os créditos
    razaocred = razao[['datalan', 'codi_lote', 'historico', 'valcre', 'historico1']]

    # Aplicar a função para extrair o último número de NF ou CTE
    razao['historico1'] = razao['historico'].apply(extrair_numero_nf_cte)

    # Criando as tabelas de débito e crédito
    razaocred = razao[['datalan', 'codi_lote', 'historico', 'valcre', 'historico1']]
    razaideb = razao[['datalan', 'codi_lote', 'historico', 'valdeb', 'historico1']]
    
    # Preenchendo valores nulos
    razaocred = razaocred.fillna('')
    razaideb = razaideb.fillna('')
    
    # Renomeando as colunas
    razaocred.rename(columns={'datalan': 'data', 'valcre': 'valor', 'historico1': 'NF'}, inplace=True)
    razaideb.rename(columns={'datalan': 'data', 'valdeb': 'valor', 'historico1': 'NF'}, inplace=True)

    # Concatenando débitos e créditos
    superzarao = pd.concat([razaideb, razaocred], keys=['debito', 'credito'])

    # Ordenando pela coluna 'valor'
    superzarao = superzarao.sort_values(by='valor')

    # Removendo duplicatas na coluna 'NF'
    superzarao['NF_conciliada'] = superzarao['NF']
    superzarao['NF_conciliada'] = superzarao['NF_conciliada'].drop_duplicates()

    # Adicionando coluna de saldo e filtrando valores diferentes de 0
    superzarao['saldo'] = ''
    superzarao = superzarao[superzarao['valor'] != 0]

    # Resumo por NF (agregando os valores)
    superzarao2 = superzarao[['NF', 'valor']]
    superzarao2 = superzarao.groupby('NF')['valor'].sum().reset_index()

    # Definindo o status das NFs
    superzarao2['status'] = superzarao2['valor'].apply(lambda x: 'Conciliado' if x == 0 else ('Valor a Pagar' if x < 0 else 'Falta NF'))

    # Exibição do resumo no Streamlit
    st.write("## Resumo por NF")
    st.dataframe(superzarao2)

    # Gráfico de colunas com a contagem de cada status de NF
    status_count = superzarao2['status'].value_counts().reset_index()
    status_count.columns = ['Status', 'Quantidade']
    
    # Usando Altair para criar o gráfico de barras
    chart = alt.Chart(status_count).mark_bar().encode(
        x=alt.X('Status', sort='-y'),
        y='Quantidade',
        color='Status'
    ).properties(
        title="Status das Notas Fiscais (NF)"
    )

    # Adicionando rótulos no gráfico
    text = chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-5  # Posição do rótulo acima das barras
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
