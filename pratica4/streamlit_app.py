import streamlit as st
import pandas as pd
import plotly.express as px

from exercicios.pratica4.db_utils import (
    get_mongo_db,
    get_race_sessions,
    get_session_details,
    get_drivers_from_session,
    get_laps_for_drivers
)


# ==========================================================
# --- Configuração da Página ---
# ==========================================================

st.set_page_config(
    page_title="OpenF1 Data Explorer",
    page_icon="🏎️",
    layout="wide"
)


st.title("🏎️ OpenF1 Data Explorer")

st.markdown(
    "Uma interface para explorar dados de corridas "
    "de Fórmula 1 armazenados no MongoDB."
)


# ==========================================================
# --- Conexão com o Banco de Dados ---
# ==========================================================

db = get_mongo_db()


if db is None:
    st.error(
        "❌ Não foi possível conectar ao MongoDB. "
        "Verifique a string de conexão e as configurações de rede."
    )
    st.stop()


# ==========================================================
# --- Barra Lateral de Filtros ---
# ==========================================================

with st.sidebar:

    st.header("Filtros da Sessão")

    # ------------------------------------------------------
    # Seleção do Ano
    # ------------------------------------------------------

    available_years = [2025, 2024, 2023]

    selected_year = st.selectbox(
        "Selecione o Ano",
        options=available_years
    )

    # ------------------------------------------------------
    # Seleção da Sessão de Corrida
    # ------------------------------------------------------

    race_sessions = get_race_sessions(
        db,
        selected_year
    )

    if not race_sessions:

        st.warning(
            f"⚠️ Nenhuma sessão de corrida encontrada para {selected_year}."
        )

        st.stop()

    # ------------------------------------------------------
    # Criar opções para o selectbox
    # ------------------------------------------------------

    session_options = {
        f"{s.get('race_name', 'Corrida Desconhecida')} - "
        f"{s.get('session_name', 'Sessão')}":
        s["session_key"]

        for s in race_sessions
    }

    selected_race_name = st.selectbox(
        "Selecione a Corrida",
        options=list(session_options.keys())
    )

    selected_session_key = session_options[
        selected_race_name
    ]


# ==========================================================
# --- Painel Principal ---
# ==========================================================

if selected_session_key:

    # ------------------------------------------------------
    # Detalhes da sessão
    # ------------------------------------------------------

    session_details = get_session_details(
        db,
        selected_session_key
    )

    if session_details:

        st.header(
            f"📊 Análise da Sessão: "
            f"{session_details.get('year', 'N/A')}"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "País",
            session_details.get(
                "country_name",
                "N/A"
            )
        )

        col2.metric(
            "Circuito",
            session_details.get(
                "circuit_short_name",
                "N/A"
            )
        )

        date_start = session_details.get(
            "date_start",
            "N/A"
        )

        if date_start != "N/A":
            date_start = date_start.split("T")[0]

        col3.metric(
            "Data",
            date_start
        )


    st.markdown("---")


    # ======================================================
    # --- Seleção de Pilotos ---
    # ======================================================

    st.subheader(
        "Comparativo de Voltas por Piloto"
    )

    drivers = get_drivers_from_session(
        db,
        selected_session_key
    )


    if not drivers:

        st.warning(
            "⚠️ Nenhum piloto encontrado para esta sessão."
        )

        st.stop()


    driver_map = {
        f"{d.get('full_name', 'Desconhecido')} "
        f"({d.get('team_name', 'Equipe N/A')})":
        d["driver_number"]

        for d in drivers
    }


    selected_drivers_names = st.multiselect(
        "Selecione um ou mais pilotos para comparar:",
        options=list(driver_map.keys()),
        default=list(driver_map.keys())[:2]
    )


    if not selected_drivers_names:

        st.info(
            "ℹ️ Por favor, selecione pelo menos um piloto "
            "para visualizar os dados."
        )

        st.stop()


    selected_driver_numbers = [
        driver_map[name]
        for name in selected_drivers_names
    ]


    # ======================================================
    # --- Buscar dados das voltas ---
    # ======================================================

    laps_df = get_laps_for_drivers(
        db,
        selected_session_key,
        selected_driver_numbers
    )


    if laps_df.empty:

        st.warning(
            "⚠️ Não foram encontrados dados de voltas "
            "para os pilotos selecionados nesta sessão."
        )

    else:

        # --------------------------------------------------
        # Mapear número do piloto para nome
        # --------------------------------------------------

        driver_number_to_name = {
            value: key
            for key, value in driver_map.items()
        }


        laps_df["driver_name"] = (
            laps_df["driver_number"]
            .map(driver_number_to_name)
        )


        # --------------------------------------------------
        # Remover voltas inválidas
        # --------------------------------------------------

        laps_df = laps_df.dropna(
            subset=["lap_duration"]
        )

        laps_df = laps_df[
            laps_df["lap_duration"] > 0
        ]


        # ==================================================
        # --- Gráfico ---
        # ==================================================

        st.subheader(
            "📈 Gráfico de Desempenho (Tempo de Volta)"
        )


        fig = px.line(
            laps_df,
            x="lap_number",
            y="lap_duration",
            color="driver_name",
            title="Comparativo de Tempo de Volta Durante a Corrida",
            labels={
                "lap_number": "Número da Volta",
                "lap_duration": "Duração da Volta (segundos)",
                "driver_name": "Piloto"
            },
            markers=True
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        # ==================================================
        # --- Tabela ---
        # ==================================================

        with st.expander(
            "📋 Ver tabela de dados das voltas"
        ):

            st.dataframe(
                laps_df[
                    [
                        "driver_name",
                        "lap_number",
                        "lap_duration"
                    ]
                ]
                .sort_values(
                    by=[
                        "driver_name",
                        "lap_number"
                    ]
                )
                .reset_index(drop=True),

                use_container_width=True
            )