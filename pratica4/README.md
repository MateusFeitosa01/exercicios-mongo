# OpenF1 Data Explorer

Aplicação em **Streamlit** para visualizar e comparar dados da Fórmula 1 armazenados no MongoDB.

## Como rodar

### 1. Clone o projeto

```bash
git clone <URL_DO_REPOSITORIO>
cd pratica4
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o `.env`

Crie um arquivo `.env` na raiz:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=openf1_data
```

### 5. Execute o Streamlit

```bash
python -m streamlit run streamlit_app.py
```

Acesse:

```text
http://localhost:8501
```
