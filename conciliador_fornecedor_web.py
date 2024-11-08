import re
import pandas as pd
import streamlit as st
import openpyxl

# Função para extrair o número da NF ou CTE do texto usando expressões regulares
def extrair_numero_nf_cte(texto):
    # Padrão para encontrar um número de NF ou CTE no texto
    padrao = r'(NF|nf|Nf|CTE|NFSE|NFSe|NFse|nfse|NF°|nf°|Nf°|Nota Fiscal|nota fiscal|Nota Fiscal de Serviço|nota fiscal de serviço)[\s°NFSSE-]?\s?(\d+)'
    
    # Procurar por correspondências no texto usando o padrão de regex
    correspondencias = re.findall(padrao, texto)
    
    if correspondencias:
        return correspondencias[-1][1]  # Retorna o último número encontrado
    else:
        # Se não houver correspondência com o padrão anterior, tentar encontrar apenas um número
        correspondencias_numero = re.findall(r'\b\d+\b', texto)
        if correspondencias_numero:
            return correspondencias_numero[-1]  # Retorna o último número encontrado
        else:
            return None

# Interface do Streamlit
st.title("Conciliação de Notas Fiscais")

# Upload do arquivo Excel
arquivo = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])
if arquivo is not None:
    try:
        # Carregar o arquivo Excel
        razao = pd.read_excel(arquivo, engine='openpyxl')
        st.write("Colunas do DataFrame:", razao.columns)  # Exibe as colunas para depuração
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        raise

    # Verifique se as colunas necessárias estão presentes
    colunas_necessarias = ['datalan', 'codi_lote', 'valdeb', 'valcre', 'historico']
    for col in colunas_necessarias:
        if col not in razao.columns:
            st.error(f"A coluna '{col}' está faltando no arquivo Excel!")
            raise ValueError(f"A coluna '{col}' está faltando no arquivo Excel!")

    # Criar a coluna 'historico1' para armazenar o número da NF/CTE extraído
    razao['historico1'] = razao['historico'].apply(extrair_numero_nf_cte)

    # Verificar se a coluna 'historico1' foi criada corretamente
    st.write("Primeiros registros da coluna 'historico1':")
    st.write(razao[['historico', 'historico1']].head())

    # Criar DataFrames de Débito e Crédito
    razaideb = razao[['datalan', 'codi_lote', 'valdeb', 'historico1']]
    razao['valcre'] *= -1  # Ajuste para os valores de crédito
    razaocred = razao[['datalan', 'codi_lote', 'historico', 'valcre', 'historico1']]

    # Preencher valores nulos
    razaocred = razaocred.fillna('')
    razaideb = razaideb.fillna('')

    # Renomear as colunas para facilitar a leitura
    razaocred.rename(columns={'datalan': 'data', 'valcre': 'valor', 'historico1': 'NF'}, inplace=True)
    razaideb.rename(columns={'datalan': 'data', 'valdeb': 'valor', 'historico1': 'NF'}, inplace=True)

    # Concatenar os dados de Débito e Crédito
    superzarao = pd.concat([razaideb, razaocred], keys=['debito', 'credito'])

    # Ordenar pela coluna 'valor' para facilitar a visualização
    superzarao = superzarao.sort_values(by='valor')

    # Criar uma coluna 'NF_conciliada' com valores únicos para a NF
    superzarao['NF_conciliada'] = superzarao['NF']
    superzarao['NF_conciliada'] = superzarao['NF_conciliada'].drop_duplicates()

    # Adicionar uma coluna 'saldo', inicialmente vazia
    superzarao['saldo'] = ''
    superzarao = superzarao[superzarao['valor'] != 0]  # Filtrar valores diferentes de zero

    # Resumo por NF (agregando os valores)
    superzarao2 = superzarao[['NF', 'valor']]
    superzarao2 = superzarao.groupby('NF')['valor'].sum().reset_index()

    # Definir o status das NFs (Conciliado, Valor a Pagar, Falta NF)
    superzarao2['status'] = superzarao2['valor'].apply(lambda x: 'Conciliado' if x == 0 else ('Valor a Pagar' if x < 0 else 'Falta NF'))

    # Exibir o resumo das NFs no Streamlit
    st.write("## Resumo por NF")
    st.dataframe(superzarao2)

    # Gráfico de barras com a contagem de cada status de NF
    status_count = superzarao2['status'].value_counts().reset_index()
    status_count.columns = ['Status', 'Quantidade']

    chart = alt.Chart(status_count).mark_bar().encode(
        x=alt.X('Status', sort='-y'),
        y='Quantidade',
        color='Status'
    ).properties(
        title="Status das Notas Fiscais (NF)"
    )

    # Exibir o gráfico
    st.altair_chart(chart, use_container_width=True)

    # Exibir a conciliação analítica
    st.write("## Conciliação Analítica")
    st.dataframe(superzarao)

    # Download do resultado
    with pd.ExcelWriter('conciliacao_fornecedor.xlsx', engine='openpyxl') as writer:
        superzarao2.to_excel(writer, sheet_name='Resumo por NF')
        superzarao.to_excel(writer, sheet_name='Conciliação Analítica')

    # Link de download do arquivo
    with open("conciliacao_fornecedor.xlsx", "rb") as file:
        st.download_button("Baixar Conciliação", file, "conciliacao_fornecedor.xlsx")
