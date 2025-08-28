Folder Structure

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
