import os
import random

import pandas as pd

from datetime import datetime

from dotenv import load_dotenv

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


# ==========================================================
# --- Carregar variáveis do arquivo .env ---
# ==========================================================

load_dotenv()


# ==========================================================
# --- Função para conexão real ao MongoDB ---
# ==========================================================

def get_mongo_db():

    mongo_uri = os.getenv(
        "MONGO_URI",
        "mongodb://localhost:27017"
    )

    db_name = os.getenv(
        "MONGO_DB",
        "openf1_data"
    )

    try:

        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=2000
        )

        client.admin.command("ping")

        return client[db_name]

    except ConnectionFailure:

        print(
            "⚠️ Não foi possível conectar ao MongoDB."
        )

        return None


# ==========================================================
# --- Sessões ---
# ==========================================================

def get_race_sessions(db, year):

    if db is None:
        return _mock_get_race_sessions(year)


    sessions = list(
        db.sessions.find(
            {
                "year": int(year)
            },
            {
                "_id": 0
            }
        )
    )


    if not sessions:

        return _mock_get_race_sessions(year)


    return sessions


# ==========================================================
# --- Detalhes da sessão ---
# ==========================================================

def get_session_details(db, session_key):

    if db is None:

        return _mock_get_session_details(
            session_key
        )


    session = db.sessions.find_one(
        {
            "session_key": session_key
        },
        {
            "_id": 0
        }
    )


    if not session:

        return _mock_get_session_details(
            session_key
        )


    return session


# ==========================================================
# --- Pilotos ---
# ==========================================================

def get_drivers_from_session(
    db,
    session_key
):

    if db is None:

        return _mock_get_drivers_from_session(
            session_key
        )


    drivers = list(
        db.drivers.find(
            {
                "session_key": session_key
            },
            {
                "_id": 0
            }
        )
    )


    if not drivers:

        return _mock_get_drivers_from_session(
            session_key
        )


    return drivers


# ==========================================================
# --- Voltas ---
# ==========================================================

def get_laps_for_drivers(
    db,
    session_key,
    driver_numbers
):

    if db is None:

        return _mock_get_laps_for_drivers(
            session_key,
            driver_numbers
        )


    laps = list(
        db.laps.find(
            {
                "session_key": session_key,
                "driver_number": {
                    "$in": driver_numbers
                }
            },
            {
                "_id": 0
            }
        )
    )


    if not laps:

        return _mock_get_laps_for_drivers(
            session_key,
            driver_numbers
        )


    return pd.DataFrame(laps)


# ==========================================================
# --- MOCKS ---
# ==========================================================

def _mock_get_race_sessions(year):

    return [

        {
            "session_key": f"{year}_AUS_GP",
            "race_name": "GP da Austrália",
            "session_name": "Corrida"
        },

        {
            "session_key": f"{year}_BRA_GP",
            "race_name": "GP do Brasil",
            "session_name": "Corrida"
        },

        {
            "session_key": f"{year}_MON_GP",
            "race_name": "GP de Mônaco",
            "session_name": "Corrida"
        }

    ]


def _mock_get_session_details(session_key):

    return {

        "year": session_key.split("_")[0],

        "country_name":
            "Brasil"
            if "BRA" in session_key
            else "Austrália"
            if "AUS" in session_key
            else "Mônaco",

        "circuit_short_name":
            "Interlagos"
            if "BRA" in session_key
            else "Albert Park"
            if "AUS" in session_key
            else "Monte Carlo",

        "date_start":
            datetime.now().strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
    }


def _mock_get_drivers_from_session(
    session_key
):

    return [

        {
            "driver_number": 1,
            "full_name": "Max Verstappen",
            "team_name": "Red Bull"
        },

        {
            "driver_number": 16,
            "full_name": "Charles Leclerc",
            "team_name": "Ferrari"
        },

        {
            "driver_number": 44,
            "full_name": "Lewis Hamilton",
            "team_name": "Mercedes"
        },

        {
            "driver_number": 63,
            "full_name": "George Russell",
            "team_name": "Mercedes"
        }

    ]


def _mock_get_laps_for_drivers(
    session_key,
    driver_numbers
):

    laps_data = []


    for driver in driver_numbers:

        base_time = random.uniform(
            85,
            95
        )


        for lap in range(1, 31):

            lap_duration = (
                base_time +
                random.uniform(-2, 2)
            )


            laps_data.append({

                "driver_number":
                    driver,

                "lap_number":
                    lap,

                "lap_duration":
                    lap_duration

            })


    return pd.DataFrame(laps_data)