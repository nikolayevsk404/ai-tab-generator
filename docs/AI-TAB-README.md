# AI Tab Generator - Product Overview

## Visao geral

Sistema para converter audio de guitarra (`.mp3`/`.wav`) em tablatura estruturada, usando pipeline assincrono entre frontend, backend e servico de IA.

## Objetivos

- aplicar IA em processamento de audio (DSP + heuristica)
- desacoplar API/orquestracao do processamento especializado
- gerar base evolutiva para exportacao `.gp5` e MIDI
- demonstrar arquitetura multi-stack alem de CRUD

## Escopo funcional

- upload de audio pelo frontend
- processamento assincrono com fila no backend
- deteccao de pitch e mapeamento para braço da guitarra
- retorno de tablatura em JSON para visualizacao

## Stack

- Backend API: Laravel (PHP)
- Frontend: Vue 3 (Vite)
- AI Service: Python (FastAPI, `librosa`, `numpy`)
- Persistencia local atual: SQLite (com opcao de evoluir para PostgreSQL)

## Fluxo de alto nivel

`Audio -> Upload API -> Queue Job -> AI Service -> Tab JSON -> Persistencia -> Frontend`

Endpoints principais:

- `POST /api/upload`
- `GET /api/result/{job_id}`

Exemplo de saida:

```json
[
  { "string": 7, "fret": 0, "time": 0.1 },
  { "string": 6, "fret": 3, "time": 0.5 }
]
```

## Diferenciais tecnicos

- pipeline de audio real com servico dedicado
- integracao Laravel + Python via job assincrono
- arquitetura preparada para evolucao de qualidade de transcricao

## Documentos relacionados

- `AI-TAB-ARCHITECTURE.md`
- `AI-TAB-AGENT.md`
- `AI-TAB-TASKS.md`