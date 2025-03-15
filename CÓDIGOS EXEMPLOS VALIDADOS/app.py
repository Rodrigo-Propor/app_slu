import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import numpy as np
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.grid import grid
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.card import card
import extra_streamlit_components as stx

# Configuração da página
st.set_page_config(
    page_title="Dashboard Demonstrativo",
    page_icon="📊",
    layout="wide"
)

# Função para criar dados fictícios de vendas
def criar_dados_vendas():
    produtos = ['Laptop', 'Smartphone', 'Tablet', 'Monitor', 'Teclado']
    lojas = ['Loja A', 'Loja B', 'Loja C', 'Loja D']
    
    dados = []
    for mes in range(1, 13):
        for produto in produtos:
            for loja in lojas:
                vendas = np.random.randint(50, 500)
                preco = {
                    'Laptop': 3000,
                    'Smartphone': 2000,
                    'Tablet': 1500,
                    'Monitor': 800,
                    'Teclado': 200
                }[produto]
                
                dados.append({
                    'Data': f'2024-{mes:02d}-01',
                    'Produto': produto,
                    'Loja': loja,
                    'Vendas': vendas,
                    'Receita': vendas * preco
                })
    
    return pd.DataFrame(dados)

# Função para criar dados de projetos
def criar_dados_projetos():
    projetos = ['Projeto A', 'Projeto B', 'Projeto C', 'Projeto D']
    start_date = datetime(2024, 1, 1)
    
    dados = []
    for projeto in projetos:
        inicio = start_date + timedelta(days=np.random.randint(0, 30))
        duracao = np.random.randint(30, 120)
        
        dados.append({
            'Projeto': projeto,
            'Início': inicio,
            'Duração': duracao,
            'Fim': inicio + timedelta(days=duracao),
            'Progresso': np.random.randint(0, 100),
            'Status': np.random.choice(['Em andamento', 'Concluído', 'Atrasado'])
        })
    
    return pd.DataFrame(dados)

# Criando dados fictícios
df_vendas = criar_dados_vendas()
df_projetos = criar_dados_projetos()

# Logo e título
col_logo1, col_logo2, col_logo3 = st.columns([4, 4, 2])
with col_logo3:
    st.image("images/logo_propor.jpg", width=200)
st.markdown("---")

# Criando o TabBar
escolha_tab = stx.tab_bar(data=[
    stx.TabBarItemData(id="tab1", title="Dashboard", description="Visão geral"),
    stx.TabBarItemData(id="tab2", title="Análise de Vendas", description="Detalhes de vendas"),
    stx.TabBarItemData(id="tab3", title="Projetos", description="Gestão de projetos"),
    stx.TabBarItemData(id="tab4", title="Análise Regional", description="Desempenho por região")
])

# Tab 1 - Dashboard
if escolha_tab == "tab1":
    colored_header(
        label="Dashboard Geral",
        description="Visão geral do negócio",
        color_name="blue-70"
    )
    
    # Métricas em cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Vendas", f"{df_vendas['Vendas'].sum():,.0f}")
    with col2:
        st.metric("Receita Total", f"R$ {df_vendas['Receita'].sum():,.2f}")
    with col3:
        st.metric("Ticket Médio", f"R$ {df_vendas['Receita'].mean():,.2f}")
    with col4:
        st.metric("Número de Lojas", len(df_vendas['Loja'].unique()))
    style_metric_cards()
    
    # Grid com cards informativos
    my_grid = grid(3, vertical_align="bottom")
    
    # Card 1
    with my_grid.container():
        card(
            title="Top Produtos",
            text=df_vendas.groupby('Produto')['Vendas'].sum().nlargest(3).to_string()
        )
    
    # Card 2
    with my_grid.container():
        card(
            title="Melhor Loja",
            text=df_vendas.groupby('Loja')['Receita'].sum().nlargest(1).to_string()
        )
    
    # Card 3
    with my_grid.container():
        card(
            title="Projetos Ativos",
            text=f"Total de {len(df_projetos)} projetos em andamento"
        )

# Tab 2 - Análise de Vendas
elif escolha_tab == "tab2":
    colored_header(
        label="Análise Detalhada de Vendas",
        description="Explore os dados de vendas",
        color_name="green-70"
    )
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        produto_selecionado = st.selectbox("Selecione o Produto", df_vendas['Produto'].unique())
    with col2:
        loja_selecionada = st.selectbox("Selecione a Loja", df_vendas['Loja'].unique())
    
    # DataFrame filtrado
    df_filtrado = df_vendas[
        (df_vendas['Produto'] == produto_selecionado) &
        (df_vendas['Loja'] == loja_selecionada)
    ]
    
    # Gráficos
    fig1 = px.line(df_filtrado, x='Data', y='Vendas', title='Evolução de Vendas')
    st.plotly_chart(fig1, use_container_width=True)
    
    fig2 = px.bar(df_filtrado, x='Data', y='Receita', title='Receita por Período')
    st.plotly_chart(fig2, use_container_width=True)

# Tab 3 - Projetos
elif escolha_tab == "tab3":
    colored_header(
        label="Gestão de Projetos",
        description="Acompanhamento de projetos",
        color_name="red-70"
    )
    
    # Visão geral dos projetos
    st.subheader("Status dos Projetos")
    
    # Cards de status
    cols_status = st.columns(3)
    with cols_status[0]:
        num_andamento = len(df_projetos[df_projetos['Status'] == 'Em andamento'])
        st.info(f"Em andamento: {num_andamento}")
    with cols_status[1]:
        num_concluidos = len(df_projetos[df_projetos['Status'] == 'Concluído'])
        st.success(f"Concluídos: {num_concluidos}")
    with cols_status[2]:
        num_atrasados = len(df_projetos[df_projetos['Status'] == 'Atrasado'])
        st.error(f"Atrasados: {num_atrasados}")
    
    # Informações dos projetos em cards
    st.subheader("Detalhes dos Projetos")
    for _, projeto in df_projetos.iterrows():
        with st.expander(f"{projeto['Projeto']} - {projeto['Progresso']}% Concluído"):
            st.write(f"Início: {projeto['Início'].strftime('%d/%m/%Y')}")
            st.write(f"Duração prevista: {projeto['Duração']} dias")
            st.write(f"Status: {projeto['Status']}")
            st.progress(projeto['Progresso'] / 100)

# Tab 4 - Análise Regional (substituindo o mapa)
else:
    colored_header(
        label="Análise Regional",
        description="Desempenho por região",
        color_name="violet-70"
    )
    
    # Análise por loja
    st.subheader("Desempenho por Loja")
    
    # Gráfico de vendas por loja
    fig_vendas_loja = px.bar(
        df_vendas.groupby('Loja')['Vendas'].sum().reset_index(),
        x='Loja',
        y='Vendas',
        title='Total de Vendas por Loja',
        color='Loja'
    )
    st.plotly_chart(fig_vendas_loja, use_container_width=True)
    
    # Gráfico de receita por loja
    fig_receita_loja = px.pie(
        df_vendas.groupby('Loja')['Receita'].sum().reset_index(),
        values='Receita',
        names='Loja',
        title='Distribuição de Receita por Loja'
    )
    st.plotly_chart(fig_receita_loja, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("Detalhamento por Loja")
    df_analise_loja = df_vendas.groupby('Loja').agg({
        'Vendas': 'sum',
        'Receita': 'sum'
    }).reset_index()
    
    df_analise_loja['Ticket Médio'] = df_analise_loja['Receita'] / df_analise_loja['Vendas']
    st.dataframe(df_analise_loja.style.format({
        'Vendas': '{:,.0f}',
        'Receita': 'R$ {:,.2f}',
        'Ticket Médio': 'R$ {:,.2f}'
    }), use_container_width=True)