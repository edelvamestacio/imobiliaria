
from models.DataModel import DataModel
from view.DashboardViews import DashboardView


class MainController:
    def __init__(self):
        self.model = DataModel()
        self.view = DashboardView()

    def run(self):
        # 1. Carregar Dados
        data, df_leads_raw, df_imoveis_raw, error = self.model.get_data()
        
        # 2. Setup Inicial da View
        self.view.render_header()
        
        if error:
            self.view.render_error(error)
            return

        if data is None or data.empty:
            self.view.render_warning("Dataset vazio.")
            return

        # 3. Renderizar Sidebar e Obter Filtros
        filters = self.view.render_sidebar_filters(data)

        # 4. Filtrar Dados via Model
        filtered_data = self.model.filter_data(data, filters)

        # 5. Calcular KPIs
        kpis = self.model.calculate_kpis(filtered_data, df_imoveis_raw)

        # 6. Atualizar View com Dados Processados
        self.view.render_kpis(kpis)
        self.view.render_charts(filtered_data)
        self.view.render_dataframe(filtered_data)
