import streamlit as st
import plotly.express as px
import pandas as pd

class DashboardView:
    def __init__(self):
        pass

    def render_header(self):
        st.title("Dashboard de Desempenho Imobiliário")
        st.markdown("Análise de Imóveis e Leads")

    def render_error(self, msg):
        st.error(msg)
        st.stop()
        
    def render_warning(self, msg):
        st.warning(msg)

    def render_sidebar_filters(self, df):
        """Renderiza a sidebar e retorna um dicionário com os valores escolhidos."""
        st.sidebar.header("Filtros")
        
        # Configuração de Datas
        min_date = df['Data Lead'].min().date()
        max_date = df['Data Lead'].max().date()

        with st.sidebar.form("form_periodo"):
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Data inicial", value=min_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
            end_date = col2.date_input("Data final", value=max_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
            st.markdown("")
            submitted = st.form_submit_button("Aplicar Período")
        
        if not submitted:
            # Mantém valores padrão se não submetido
            pass 
            
        st.sidebar.markdown("---")

        # Selectboxes
        def get_options(col, type_cast=str):
            if col in df.columns:
                return ['Todos'] + sorted(df[col].dropna().unique().astype(type_cast).tolist())
            return ['Todos']

        bairro = st.sidebar.selectbox("Bairro", get_options('Bairro'))
        tipo_imovel = st.sidebar.selectbox("Tipo de Imóvel", get_options('Tipo Imovel'))
        dorms = st.sidebar.selectbox("Dormitórios", get_options('Dormitorios', int))
        vagas = st.sidebar.selectbox("Vagas de Garagem", get_options('Vagas', int))

        # Range Numérico
        st.sidebar.markdown("**Valor de Locação (R$)**")
        min_db = float(df['Valor Locacao'].min()) if 'Valor Locacao' in df.columns else 0.0
        max_db = float(df['Valor Locacao'].max()) if 'Valor Locacao' in df.columns else 0.0
        
        c1, c2 = st.sidebar.columns(2)
        min_loc = c1.number_input("Mínimo", min_value=min_db, max_value=max_db, value=min_db, step=100.0)
        max_loc = c2.number_input("Máximo", min_value=min_db, max_value=max_db, value=max_db, step=100.0)

        return {
            'start_date': start_date, 'end_date': end_date,
            'bairro': bairro, 'tipo_imovel': tipo_imovel,
            'dormitorios': dorms, 'vagas': vagas,
            'min_loc': min_loc, 'max_loc': max_loc
        }

    def render_kpis(self, kpis):
        """Exibe os cartões de métricas."""
        def fmt_currency(v):
            return f"R$ {v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        
        def fmt_num(v):
            return f"{v:,}".replace(",", ".")

        k1, k2, k3, k4 = st.columns(4)
        k5, k6, k7, k8 = st.columns(4)

        k1.metric("Total de Leads", fmt_num(kpis['total_leads']))
        k2.metric("Total Comissionamento", fmt_currency(kpis['total_comissao']))
        k3.metric("Imóveis com Leads", fmt_num(kpis['imoveis_leads']))
        k4.metric("Total de Imóveis (Catálogo)", fmt_num(kpis['total_catalogo']))

        k5.metric("Leads Convertidos", fmt_num(kpis['leads_convertidos']))
        k6.metric("Taxa de Fechamento", f"{kpis['taxa_fechamento']:.2f}%")
        k7.metric("Ticket Médio Fechamento", fmt_currency(kpis['ticket_medio']))
        k8.metric("Imóveis Ativos", fmt_num(kpis['ativos_catalogo']))
        
        st.markdown("---")

    def render_charts(self, df):
        if df.empty:
            st.warning("Sem dados para exibir gráficos.")
            return

        # 1. Gráfico de Evolução Mensal
        st.subheader("Volume de Leads vs. Fechamento por Mês/Ano")
        if 'Fechamento' in df.columns:
            df['Mês/Ano'] = df['Data Lead'].dt.to_period('M').astype(str)
            df_leads = df.groupby('Mês/Ano')['ID'].nunique().reset_index(name='Total Leads')
            df_fechados = df[df['Fechamento'] == 1].groupby('Mês/Ano')['ID'].nunique().reset_index(name='Fechamentos')
            
            df_chart = pd.merge(df_leads, df_fechados, on='Mês/Ano', how='left').fillna(0)
            df_chart['Não Fechados'] = df_chart['Total Leads'] - df_chart['Fechamentos']
            
            df_long = df_chart.melt(id_vars=['Mês/Ano'], value_vars=['Fechamentos', 'Não Fechados'], var_name='Status', value_name='Qtd')
            df_long = df_long.sort_values(by='Mês/Ano')

            fig = px.bar(df_long, x='Mês/Ano', y='Qtd', color='Status', 
                         color_discrete_map={'Fechamentos': '#28a745', 'Não Fechados': '#ced4da'},
                         template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)

        # 2. Comissionamento por Corretor
        st.subheader("Comissionamento por Corretor")
        if 'Comissao' in df.columns and 'Corretor' in df.columns:
            df_com = df[df['Fechamento'] == 1].groupby('Corretor')['Comissao'].sum().reset_index().sort_values('Comissao', ascending=False).head(10)
            fig_com = px.bar(df_com, x='Corretor', y='Comissao', title="Top 10 Corretores", template='plotly_dark')
            st.plotly_chart(fig_com, use_container_width=True)

        col1, col2 = st.columns(2)
        
        # 3. Mídias
        with col1:
            st.subheader("Leads por Canal (Mídia)")
            if 'Midias' in df.columns:
                df_midia = df.groupby('Midias')['ID'].nunique().reset_index(name='Qtd').sort_values('Qtd', ascending=False).head(10)
                fig_midia = px.bar(df_midia, x='Midias', y='Qtd', template='plotly_dark')
                st.plotly_chart(fig_midia, use_container_width=True)
        
        # 4. Tipos
        with col2:
            st.subheader("Distribuição por Tipo de Imóvel")
            if 'Tipo Imovel' in df.columns:
                df_tipo = df.groupby('Tipo Imovel')['ID'].nunique().reset_index(name='Qtd')
                fig_pie = px.pie(df_tipo, values='Qtd', names='Tipo Imovel', template='plotly_dark', hole=.3)
                st.plotly_chart(fig_pie, use_container_width=True)

        # 5. Scatter Plot
        st.subheader("Dispersão: Locação vs. Dormitórios")
        if 'Valor Locacao' in df.columns and 'Dormitorios' in df.columns:
            fig_scat = px.scatter(df, x='Valor Locacao', y='Dormitorios', color='Bairro' if 'Bairro' in df.columns else None, template='plotly_dark')
            st.plotly_chart(fig_scat, use_container_width=True)

    def render_dataframe(self, df):
        st.subheader("Detalhes dos Leads (Top 100)")
        cols_show = ['ID', 'Cli Nome', 'Tipo Imovel', 'Bairro', 'Valor Locacao', 'Fechamento', 'Comissao', 'Corretor', 'Data Lead']
        cols_valid = [c for c in cols_show if c in df.columns]
        
        df_show = df[cols_valid].head(100).copy()
        
        if 'Data Lead' in df_show.columns:
            df_show['Data Lead'] = df_show['Data Lead'].dt.strftime('%d/%m/%Y')
        if 'Fechamento' in df_show.columns:
            df_show['Fechamento'] = df_show['Fechamento'].map({1: 'Sim', 0: 'Não'})
            
        st.dataframe(df_show, use_container_width=True)