# Architecture

- frontend (Vue)
- backend (Laravel)
- ai-service (Python)

Pipeline:
Audio -> Basic Pitch -> Notes -> Fretboard -> GP5

---

# AI Tab Generator — Estrutura Profissional

## Monorepo (recomendado)

```
ai-tab-generator/
├── apps/
│   ├── frontend/        # Vue 3
│   ├── backend/         # Laravel API
│   └── ai-service/      # Python (IA)
├── packages/
│   └── shared/          # tipos/contratos
├── infra/
│   ├── docker/
│   └── db/
├── docs/
├── README.md
```

## Separação de responsabilidades

### apps/backend (Laravel)
Orquestrador

```
backend/
├── app/
│   ├── Jobs/
│   │   └── ProcessAudioJob.php
│   ├── Services/
│   │   └── AudioProcessingService.php
│   ├── Http/Controllers/
│   │   └── UploadController.php
│   └── Models/
│       └── AudioJob.php
├── routes/api.php
├── database/
│   └── migrations/
```

### apps/ai-service (Python)
Responsavel pela IA

```
ai-service/
├── app/
│   ├── main.py          # FastAPI ou Flask
│   ├── agent/
│   │   └── AudioToTabAgent.py
│   ├── services/
│   │   ├── transcription_stack.py
│   │   ├── audio_embeddings.py
│   │   ├── note_mapper.py
│   │   └── fretboard_mapper.py
│   ├── models/
│   └── utils/
├── tests/
├── requirements.txt
```

### apps/frontend (Vue)
Interface do usuário

```
frontend/
├── src/
│   ├── components/
│   │   ├── UploadForm.vue
│   │   └── TabViewer.vue
│   ├── services/
│   │   └── api.ts
│   └── pages/
│       └── Home.vue
```

### packages/shared
Contratos entre Laravel e Python

```
shared/
├── types/
│   └── tab.ts
```

## Regras de arquitetura

- Laravel NÃO processa áudio
- Python NÃO expõe lógica de frontend
- Frontend NÃO contém regra de negócio
- Pipeline de IA é isolado

## Tasks (para geração de código)

### TASK 1 — Setup Laravel API

Crie uma API Laravel com:

- endpoint POST /api/upload
- salvar arquivo em storage
- criar model AudioJob com:
  - id
  - status (pending, processing, done)
  - result (json)

Configurar queue (database ou redis)

### TASK 2 — Job assíncrono

Crie um Job ProcessAudioJob que:

- recebe o caminho do arquivo
- chama um microserviço Python via HTTP
- atualiza status para:
  - processing
  - done

Salvar resultado da tablatura no banco

### TASK 3 — AI Service (Python)

Crie um microserviço usando FastAPI com endpoint:

POST /process-audio

Recebe:
- arquivo de audio

Retorna:
- lista de notas detectadas
- tablatura (string + fret + tempo)

Organizar código em:
- agent
- services
- utils

### TASK 4 — Agent Pipeline

Implemente classe AudioToTabAgent com pipeline:

- load audio
- basic-pitch transcription
- embeddings de audio
- frequency → note
- note → fretboard mapping

Separar cada etapa em arquivos diferentes

### TASK 5 — Transcription Backend

Implementar transcricao com modelo pre-treinado:

- usar `basic-pitch` como backend principal
- manter fallback com `librosa`
- preservar timestamps e duracoes

Retornar lista de frequências com timestamp

### TASK 6 — Fretboard Mapping (6 cordas)

Criar função que:

- recebe nota (ex: E2)
- retorna melhor posição no braço (string + fret)

Considerar tuning padrao de 6 cordas:
E2 A2 D3 G3 B3 E4

Priorizar menor movimento de mão

### TASK 7 — Integração Laravel ↔ Python

No Laravel:

- criar service AudioProcessingService
- fazer POST para o Python service
- tratar timeout e erro

Usar Http Client do Laravel

### TASK 8 — Frontend Vue

Criar tela com:

- upload de áudio
- indicador de status (processing/done)
- exibição da tablatura

Fazer polling ou usar websocket (opcional)

### TASK 9 — Testes

Python:
- testar pitch detection
- testar mapping

Laravel:
- testar upload
- testar job

Garantir cobertura básica

### TASK 10 — Logs

Salvar:

- frequências detectadas
- notas geradas
- posição no braço

Criar logs estruturados (json)

## Pipeline

Upload → Laravel → Queue → Python → Process → Return JSON → Save → Frontend

## Dicas de execução

### Comece simples
- primeiro faça funcionar
- depois melhore a precisão

### Use heurística antes de ML
- pegar frequência dominante
- mapear diretamente para nota

### Commits
```
feat(ai): implement pitch detection pipeline
feat(agent): map notes to 7-string fretboard
feat(queue): async audio processing
```

## Resultado esperado

- IA aplicada
- microserviço Python bem definido
- backend robusto com Laravel
- pipeline real funcional
- projeto com potencial de produto

---

# Architecture (Updated with Docker)

## Services
- frontend (Vue)
- backend (Laravel)
- ai-service (Python)
- postgres
- redis (queue)

## docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: ./apps/backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  frontend:
    build: ./apps/frontend
    ports:
      - "5173:5173"

  ai-service:
    build: ./apps/ai-service
    ports:
      - "5000:5000"

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: tabdb
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```
