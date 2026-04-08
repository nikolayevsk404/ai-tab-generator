# AI Tab Generator

Monorepo local para gerar uma primeira versao funcional do fluxo de audio para tablatura, com:

- frontend em Vue 3
- backend em Laravel 13
- microservico Python com FastAPI + librosa

## Documentacao

Os documentos de requisitos e planejamento ficam em `doc/`:

- `doc/README.md`: indice da documentacao
- `doc/AI-TAB-README.md`: visao geral original do produto
- `doc/AI-TAB-ARCHITECTURE.md`: diretrizes de arquitetura
- `doc/AI-TAB-AGENT.md`: resumo do agent principal
- `doc/AI-TAB-TASKS.md`: backlog inicial

## Estrutura

```txt
apps/
  backend/
  frontend/
  ai-service/
packages/
  shared/
doc/
```

## Fluxo

1. Frontend envia o audio para `POST /api/upload`.
2. Laravel salva o arquivo, cria `audio_jobs` e despacha `ProcessAudioJob`.
3. O job chama o microservico Python em `POST /process-audio`.
4. O resultado da tablatura, logs e um export `.gp5` ficam salvos no backend.
5. Frontend faz polling em `GET /api/result/{job_id}`.

## Banco local

Neste setup local, o backend usa SQLite para reduzir atrito e fazer o pipeline funcionar rapido na maquina.

## Como rodar

Backend:

`cd /var/www/projects/ai-tab-generator/apps/backend && php artisan migrate && php artisan serve`

Queue worker:

`cd /var/www/projects/ai-tab-generator/apps/backend && php artisan queue:work`

Frontend:

`cd /var/www/projects/ai-tab-generator/apps/frontend && npm run dev`

AI service:

`cd /var/www/projects/ai-tab-generator/apps/ai-service && python3 -m uvicorn app.main:app --reload --port 8001`
