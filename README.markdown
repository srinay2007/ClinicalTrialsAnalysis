# Clinical Trials App

A simplified application for managing clinical trials data, with a chatbot powered by Open AI API, hosted on an Azure VM.

## Setup

1. **Create Azure VM**:
   - Use Ubuntu 22.04, Standard_D2s_v3.
   - Install Docker, Docker Compose, and Nginx: `sudo apt-get update && sudo apt-get install -y docker.io docker-compose nginx`.
   - Enable SSH and open ports 80, 5432, 8000, 3000.

2. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd clinical-trials-app
   ```

3. **Configure Environment**:
   - Copy `backend/.env.example` to `backend/.env` and set:
     - `DATABASE_URL` (e.g., `postgresql+psycopg2://user:password@postgres:5432/trials_db`)
     - `OPENAI_API_KEY` (from Open AI platform)
     - `API_KEY` (for LLM API access)
   - Copy `frontend/.env.example` to `frontend/.env` and set `REACT_APP_API_URL` (e.g., `http://<vm-ip>:8000/api/v1`).

4. **Set Up PostgreSQL with pgvector**:
   ```bash
   docker-compose up -d postgres
   docker exec -it <postgres-container> bash
   apt-get update && apt-get install -y postgresql-server-dev-15 gcc make
   git clone https://github.com/pgvector/pgvector.git
   cd pgvector
   make && make install
   psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE EXTENSION vector;"
   ```

5. **Run Application**:
   ```bash
   docker-compose up -d
   sudo cp nginx.conf /etc/nginx/sites-available/clinical-trials
   sudo ln -sf /etc/nginx/sites-available/clinical-trials /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

6. **Access**:
   - Frontend: `http://<vm-ip>:80`
   - API: `http://<vm-ip>:80/api/v1`
   - LLM API: `http://<vm-ip>:80/api/v1/chat/completions` (use `X-API-Key`)

## CI/CD
- Configure GitHub Actions with secrets: `AZURE_VM_IP`, `AZURE_VM_USER`, `AZURE_VM_SSH_KEY`.
- Ensure `.env` files are not committed (listed in `.gitignore`).

## Notes
- Replace `<vm-ip>` with your Azure VM's public IP or domain.
- Secure with HTTPS in production (e.g., via Let's Encrypt).
- Monitor Open AI API usage via their platform.

## Folder Structure 

ClinicalTrialsAnalysis/
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── chatbot.py
│   │   │   └── llm.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── clinical_trials.py
│   │   │   └── vectors.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scraping.py
│   │   │   └── vector_search.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── db.py
│   │   ├── chatbot/
│   │   │   ├── __init__.py
│   │   │   └── llm.py
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   └── Chatbot.js
│   │   ├── services/
│   │   │   └── api.js
│   │   └── App.js
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
├── nginx.conf
├── .gitignore
├── README.md
└── LICENSE
