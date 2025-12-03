import pandas as pd
import numpy as np
import streamlit as st

class DataModel :
    def __init__(self):
        self.imoveis_file = 'data/imoveis.csv'
        self.leads_file = 'data/leads.csv'
    
    def _load_csv_cached(self, filepath):
        try:
            df = pd.read_csv(filepath, sep=";", encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, sep=";", encoding="latin1")
        except FileNotFoundError:
            return None
        except Exception as e:
            st.error(f"Erro ao carregar {filepath}: {e}")
            return None
        
        df.columns = df.columns.str.strip()
        return df
            
    def get_data(self):
        """Carrega e trata os dados brutos."""
        
        def clean_numeric_col(series):
            # Limpa ponto de milhar e transforma vírgula em ponto decimal
            series_copy = series.copy().astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            return pd.to_numeric(series_copy, errors='coerce')
            
        # --- CARREGA IMÓVEIS ---
        df_imoveis = self._load_csv_cached(self.imoveis_file)
        if df_imoveis is None: 
            return None, None, None, f"Arquivo '{self.imoveis_file}' não encontrado."

        cols_imoveis = ['CodigoImovel', 'TipoImovel', 'Bairro', 'PrecoLocacao', 'PrecoVenda', 'QtdDormitorios', 'QtdVagas', 'AreaUtil']
        missing_cols = [col for col in cols_imoveis if col not in df_imoveis.columns]
        
        if missing_cols:
            return None, None, None, f"Colunas faltando em Imóveis: {missing_cols}"
            
        df_imoveis_raw = df_imoveis.copy() # Preserva raw para contagem de catálogo
        
        # Tratamento e Renomeação Imóveis
        df_imoveis = df_imoveis[cols_imoveis]
        df_imoveis.rename(columns={
            'PrecoLocacao': 'Valor Locacao', 
            'PrecoVenda': 'Valor Venda', 
            'TipoImovel': 'Tipo Imovel',
        }, inplace=True)
        df_imoveis['CodigoImovel'] = df_imoveis['CodigoImovel'].astype(str).str.strip()

        # CORREÇÃO 1: Limpeza Numérica ANTES do Merge (VALOR LOCAÇÃO / VENDA)
        for col in ['Valor Locacao', 'Valor Venda', 'AreaUtil']:
            if col in df_imoveis.columns:
                df_imoveis[col] = clean_numeric_col(df_imoveis[col])
                
                # tratamento da coluna [Valor Locacao] pois está majorando em x10
                if col in ['Valor Locacao', 'Valor Venda']:
                    df_imoveis[col] = df_imoveis[col] / 10 

        # --- CARREGA LEADS ---
        df_leads = self._load_csv_cached(self.leads_file)
        if df_leads is None: 
             return None, None, None, f"Arquivo '{self.leads_file}' não encontrado."
        
        df_leads.rename(columns={'Cod Imovel': 'CodigoImovel', 'fechamento': 'Fechamento', 'comissao': 'Comissao'}, inplace=True)

        if 'Createdat Time' in df_leads.columns:
            df_leads['Data Lead'] = pd.to_datetime(df_leads['Createdat Time'], errors='coerce')
        else:
            return None, None, None, "Coluna 'Createdat Time' não encontrada em Leads."

        df_leads['CodigoImovel'] = df_leads['CodigoImovel'].astype(str).str.strip()

        # --- MERGE E LIMPEZA ---
        df_merged = pd.merge(df_leads, df_imoveis, on='CodigoImovel', how='left')
        
        # Tratamento de colunas duplicadas
        if 'Tipo Imovel_y' in df_merged.columns:
            df_merged.rename(columns={'Tipo Imovel_y': 'Tipo Imovel'}, inplace=True)
            if 'Tipo Imovel_x' in df_merged.columns: df_merged.drop(columns=['Tipo Imovel_x'], inplace=True)
            if 'TipoImovel_x' in df_merged.columns: df_merged.drop(columns=['TipoImovel_x'], inplace=True)

        # Limpeza Numérica Pós-Merge (apenas Comissao)
        for col in ['Comissao']: 
            if col in df_merged.columns:
                df_merged[col] = clean_numeric_col(df_merged[col])
                
        # Tratamento Inteiros (permanece inalterado)
        for col in ['QtdDormitorios', 'QtdVagas']:
            if col in df_merged.columns:
                df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0).astype(int)
        
        df_merged.rename(columns={'QtdDormitorios': 'Dormitorios', 'QtdVagas': 'Vagas'}, inplace=True)
        df_merged.dropna(subset=['Data Lead'], inplace=True)

        # Tratamento Fechamento
        if 'Fechamento' in df_merged.columns:
            df_merged['Fechamento'] = (
                df_merged['Fechamento'].astype(str).str.lower().str.strip()
                .replace({'sim': 1, 'não': 0, 'yes': 1, 'no': 0})
                .astype(int, errors='ignore')
            )
            df_merged['Fechamento'] = pd.to_numeric(df_merged['Fechamento'], errors='coerce').fillna(0).astype(int)

        return df_merged, df_leads, df_imoveis_raw, None

    
    def filter_data(self, df, filters):
        """Aplica os filtros selecionados na View sobre o DataFrame."""
        df_f = df.copy()

        # Filtro Data
        df_f = df_f[
            (df_f['Data Lead'].dt.date >= filters['start_date']) & 
            (df_f['Data Lead'].dt.date <= filters['end_date'])
        ]

        # Filtros Categóricos
        if filters['bairro'] != 'Todos' and 'Bairro' in df_f.columns:
            df_f = df_f[df_f['Bairro'] == filters['bairro']]
        
        if filters['tipo_imovel'] != 'Todos' and 'Tipo Imovel' in df_f.columns:
            df_f = df_f[df_f['Tipo Imovel'] == filters['tipo_imovel']]
            
        if filters['dormitorios'] != 'Todos' and 'Dormitorios' in df_f.columns:
            df_f = df_f[df_f['Dormitorios'] == filters['dormitorios']]
            
        if filters['vagas'] != 'Todos' and 'Vagas' in df_f.columns:
            df_f = df_f[df_f['Vagas'] == filters['vagas']]

        # Filtro Valor
        if 'Valor Locacao' in df_f.columns:
            df_f = df_f[(df_f['Valor Locacao'] >= filters['min_loc']) & (df_f['Valor Locacao'] <= filters['max_loc'])]

        return df_f

    
    def calculate_kpis(self, df_filtered, df_imoveis_raw):
        """Calcula todas as métricas baseadas nos dados filtrados."""
        kpis = {}
        
        # Métricas Básicas
        kpis['total_leads'] = df_filtered['ID'].nunique() if 'ID' in df_filtered.columns else 0
        kpis['imoveis_leads'] = df_filtered['CodigoImovel'].nunique()
        
        # Métricas Financeiras/Conversão
        if 'Fechamento' in df_filtered.columns:
            kpis['leads_convertidos'] = df_filtered[df_filtered['Fechamento'] == 1]['ID'].nunique()
            kpis['total_comissao'] = df_filtered[df_filtered['Fechamento'] == 1]['Comissao'].sum() if 'Comissao' in df_filtered.columns else 0
            kpis['taxa_fechamento'] = (kpis['leads_convertidos'] / kpis['total_leads']) * 100 if kpis['total_leads'] > 0 else 0
            kpis['ticket_medio'] = kpis['total_comissao'] / kpis['total_leads'] if kpis['total_leads'] > 0 else 0
        else:
            kpis['leads_convertidos'] = 0
            kpis['total_comissao'] = 0
            kpis['taxa_fechamento'] = 0
            kpis['ticket_medio'] = 0

        # Métricas Catálogo (Raw)
        kpis['total_catalogo'] = df_imoveis_raw['CodigoImovel'].nunique() if df_imoveis_raw is not None else 0
        if df_imoveis_raw is not None and 'Ativo' in df_imoveis_raw.columns:
            kpis['ativos_catalogo'] = df_imoveis_raw[df_imoveis_raw['Ativo'].astype(str).str.strip() == 'Ativo']['CodigoImovel'].nunique()
        else:
            kpis['ativos_catalogo'] = 0
            
        return kpis