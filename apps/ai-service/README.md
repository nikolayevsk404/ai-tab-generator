# AI Service

Microservico FastAPI responsavel pelo pipeline inicial:

- carregar audio
- detectar pitch com librosa
- converter frequencia em nota
- mapear nota para o braco de guitarra de 7 cordas

## Rodando localmente

1. Criar ambiente virtual Python.
2. Instalar `requirements.txt`.
3. Subir com `uvicorn app.main:app --reload --port 8001`.
