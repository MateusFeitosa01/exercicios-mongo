import streamlit as st
import pandas as pd
import plotly.express as px
import db_utils as db_utils

# Configuração da página
st.set_page_config(
    page_title="OpenF1 Data Explorer - Persistência Poliglota",
    page_icon="🏎️",
    layout="wide"
)

# Inicializa banco SQLite se necessário
db_utils.init_sqlite_db()

st.title("🏎️ OpenF1 Data Explorer")
st.markdown("---")

# Criando abas para navegação na aplicação
tab_analysis, tab_history = st.tabs(["📊 Análise de Sessão", "📜 Histórico de Análises (SQLite)"])

# =========================================================
# ABA 1: ANÁLISE DE SESSÃO (MONGODB & GERADOR DE RESUMO)
# =========================================================
with tab_analysis:
    st.sidebar.header("🔍 Filtros da Sessão")
    
    # 1. Seleção do Ano
    try:
        available_years = db_utils.get_available_years()
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB: {e}")
        available_years = []

    if available_years:
        selected_year = st.sidebar.selectbox("Selecione o Ano", available_years)
        
        # 2. Seleção da Sessão
        sessions = db_utils.get_sessions_by_year(selected_year)
        session_options = {
            f"{s.get('country_name', '')} - {s.get('session_name', '')} ({s.get('location', '')})": s
            for s in sessions
        }
        
        selected_session_label = st.sidebar.selectbox("Selecione a Corrida/Sessão", list(session_options.keys()))
        selected_session_data = session_options[selected_session_label]
        session_key = selected_session_data["session_key"]
        
        # Exibição dos Detalhes da Sessão
        col_info1, col_info2, col_info3 = st.columns(3)
        col_info1.metric("País", selected_session_data.get("country_name", "N/A"))
        col_info2.metric("Circuito", selected_session_data.get("circuit_short_name", "N/A"))
        col_info3.metric("Sessão", selected_session_data.get("session_name", "N/A"))
        
        # 3. Seleção de Múltiplos Pilotos
        drivers_list = db_utils.get_drivers_by_session(session_key)
        driver_map = {d["label"]: d["driver_number"] for d in drivers_list}
        
        selected_driver_labels = st.sidebar.multiselect(
            "Selecione os Pilotos para Comparação",
            options=list(driver_map.keys()),
            default=list(driver_map.keys())[:2] if len(driver_map) >= 2 else list(driver_map.keys())
        )
        
        selected_driver_numbers = [driver_map[lbl] for lbl in selected_driver_labels]
        
        if selected_driver_numbers:
            # Leitura do MongoDB
            df_laps = db_utils.get_laps_data(session_key, selected_driver_numbers)
            
            if not df_laps.empty and "lap_duration" in df_laps.columns and "lap_number" in df_laps.columns:
                # Trata a coluna de identificação do piloto
                if "driver_acronym" in df_laps.columns:
                    df_laps["driver_id"] = df_laps["driver_acronym"].fillna(df_laps["driver_number"].astype(str))
                else:
                    df_laps["driver_id"] = df_laps["driver_number"].astype(str)

                # Gráfico Interativo com Plotly
                st.subheader("📈 Comparação de Desempenho por Volta")
                fig = px.line(
                    df_laps,
                    x="lap_number",
                    y="lap_duration",
                    color="driver_id",
                    labels={"lap_number": "Número da Volta", "lap_duration": "Tempo da Volta (s)", "driver_id": "Piloto"},
                    title="Tempo de Volta ao Longo da Corrida"
                )
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de dados brutos
                with st.expander("📄 Ver Dados Brutos das Voltas (MongoDB)"):
                    st.dataframe(df_laps, use_container_width=True)
                
                st.markdown("---")
                
                # Botão para calcular métricas e persistir no SQLite
                if st.button("💾 Gerar e Salvar Resumo da Análise (SQLite)", type="primary"):
                    metrics_list = []
                    
                    for driver in selected_driver_labels:
                        d_num = driver_map[driver]
                        driver_laps = df_laps[df_laps["driver_number"] == d_num].copy()
                        
                        if not driver_laps.empty:
                            # Removendo voltas de in/out pitstop para cálculo de consistência (se as colunas existirem)
                            clean_laps = driver_laps.copy()
                            if "is_pit_out_lap" in clean_laps.columns:
                                clean_laps = clean_laps[clean_laps["is_pit_out_lap"] != True]
                            
                            fastest = float(driver_laps["lap_duration"].min())
                            avg_time = float(driver_laps["lap_duration"].mean())
                            total_laps = int(driver_laps["lap_number"].count())
                            std_dev = float(clean_laps["lap_duration"].std()) if len(clean_laps) > 1 else 0.0
                            
                            metrics_list.append({
                                "session_name": selected_session_label,
                                "driver_name": driver,
                                "fastest_lap": round(fastest, 3) if pd.notna(fastest) else None,
                                "average_lap_time": round(avg_time, 3) if pd.notna(avg_time) else None,
                                "total_laps": total_laps,
                                "consistency_std_dev": round(std_dev, 3) if pd.notna(std_dev) else None
                            })
                    
                    if metrics_list:
                        db_utils.save_analysis_report(metrics_list)
                        st.success("Métricas agregadas salvas com sucesso no banco relacional SQLite (`analysis_reports.db`)!")
                        st.dataframe(pd.DataFrame(metrics_list), use_container_width=True)
                    else:
                        st.warning("Não foi possível calcular métricas para os pilotos selecionados.")
            else:
                st.warning("Nenhum dado de volta encontrado para os filtros selecionados.")
        else:
            st.info("Selecione pelo menos um piloto na barra lateral para prosseguir.")
    else:
        st.error("Nenhuma sessão encontrada na base MongoDB.")

# =========================================================
# ABA 2: HISTÓRICO DE ANÁLISES (SQLITE)
# =========================================================
with tab_history:
    st.header("📜 Relatórios Salvos no SQLite")
    st.markdown("Esta seção exibe os dados sumarizados persistidos no banco relacional **SQLite**.")
    
    df_history = db_utils.get_analysis_history()
    
    if not df_history.empty:
        st.dataframe(
            df_history,
            column_config={
                "id": "ID",
                "session_name": "Sessão",
                "driver_name": "Piloto",
                "fastest_lap": st.column_config.NumberColumn("Melhor Volta (s)", format="%.3f"),
                "average_lap_time": st.column_config.NumberColumn("Média de Volta (s)", format="%.3f"),
                "total_laps": "Total de Voltas",
                "consistency_std_dev": st.column_config.NumberColumn("Desvio Padrão / Consistência (s)", format="%.3f"),
                "analysis_timestamp": "Data/Hora do Registro"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma análise foi salva ainda. Vá até a aba 'Análise de Sessão' e clique em 'Gerar e Salvar Resumo da Análise'.")