# Smart City Dashboard

Dashboard geoespacial com API FastAPI, interface Streamlit, MongoDB e SQLite.

## Requisitos

- Python 3.11
- Docker Desktop

## Executar no Windows

Rode os comandos a partir desta pasta (`smart_city`). Crie o ambiente virtual e instale as dependências:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requeriments.txt
```

Inicie o MongoDB. Na primeira execução:

```powershell
docker run -d --name smart_city_mongo -p 27017:27017 -v smart_city_mongo_data:/data/db mongo:7.0
```

Nas próximas execuções, use `docker start smart_city_mongo`.

Em um terminal com o ambiente virtual ativado, carregue os dados e inicie a API:

```powershell
python scripts/seed_data.py
uvicorn backend.main:app --reload
```

Em outro terminal, também na pasta `smart_city` e com o ambiente ativado, inicie o dashboard:

```powershell
streamlit run dashboard/app.py
```

Abra:

- Dashboard: <http://localhost:8501>
- API e documentação: <http://localhost:8000/docs>

O seed recria os dados de demonstração da coleção espacial. Execute-o novamente apenas quando quiser repopular esses dados.
