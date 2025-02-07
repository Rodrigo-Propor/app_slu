import streamlit as st
import pandas as pd
import plotly.express as px

# Criando dados fictícios de vendas
dados_vendas = {
    'Produto': ['Notebook', 'Smartphone', 'Tablet', 'Monitor', 'Teclado'] * 4,
    'Mês': ['Janeiro', 'Janeiro', 'Janeiro', 'Janeiro', 'Janeiro',
            'Fevereiro', 'Fevereiro', 'Fevereiro', 'Fevereiro', 'Fevereiro',
            'Março', 'Março', 'Março', 'Março', 'Março',
            'Abril', 'Abril', 'Abril', 'Abril', 'Abril'],
    'Vendas': [150, 300, 80, 120, 200,
               180, 280, 90, 150, 220,
               200, 320, 100, 140, 180,
               160, 290, 85, 130, 210],
    'Receita': [750000, 300000, 120000, 180000, 40000,
                900000, 280000, 135000, 225000, 44000,
                1000000, 320000, 150000, 210000, 36000,
                800000, 290000, 127500, 195000, 42000]
}

df = pd.DataFrame(dados_vendas)

# Configuração da página
st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
st.title("Dashboard de Vendas - Visualizações Alternativas")

# Criando as tabs para diferentes visualizações
tab1, tab2, tab3 = st.tabs(["📊 Tabela de Dados", "📈 Gráfico de Vendas", "💰 Gráfico de Receita"])

with tab1:
    st.write("### Visão em Tabela")
    st.dataframe(df, use_container_width=True)

with tab2:
    st.write("### Gráfico de Vendas por Produto")
    fig_vendas = px.bar(df, 
                        x='Produto', 
                        y='Vendas',
                        color='Mês',
                        barmode='group',
                        title='Vendas por Produto e Mês')
    st.plotly_chart(fig_vendas, use_container_width=True)

with tab3:
    st.write("### Gráfico de Receita por Produto")
    fig_receita = px.line(df, 
                         x='Mês', 
                         y='Receita',
                         color='Produto',
                         markers=True,
                         title='Receita por Produto ao Longo dos Meses')
    st.plotly_chart(fig_receita, use_container_width=True)

# Métricas gerais
st.write("---")
st.write("### Métricas Gerais")

col1, col2, col3 = st.columns(3)
with col1:
    total_vendas = df['Vendas'].sum()
    st.metric("Total de Vendas", f"{total_vendas:,} unidades")

with col2:
    total_receita = df['Receita'].sum()
    st.metric("Receita Total", f"R$ {total_receita:,.2f}")

with col3:
    ticket_medio = total_receita / total_vendas
    st.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

# Análise por produto
st.write("### Análise por Produto")
produto_selecionado = st.selectbox("Selecione um produto", df['Produto'].unique())

df_produto = df[df['Produto'] == produto_selecionado]
col4, col5 = st.columns(2)

with col4:
    st.write(f"Vendas mensais de {produto_selecionado}")
    fig_vendas = px.bar(df_produto, 
                        x='Mês', 
                        y='Vendas',
                        title=f'Vendas Mensais - {produto_selecionado}')
    st.plotly_chart(fig_vendas, use_container_width=True)

with col5:
    st.write(f"Receita mensal de {produto_selecionado}")
    fig_receita = px.bar(df_produto, 
                         x='Mês', 
                         y='Receita',
                         title=f'Receita Mensal - {produto_selecionado}')
    st.plotly_chart(fig_receita, use_container_width=True)  