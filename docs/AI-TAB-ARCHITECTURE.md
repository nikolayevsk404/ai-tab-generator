# AI Tab Generator - Architecture

## Arquitetura geral

Servicos principais:

- `apps/frontend` (Vue): upload e visualizacao da tablatura
- `apps/backend` (Laravel): API, persistencia e orquestracao de jobs
- `apps/ai-service` (Python): processamento de audio e geracao de tab
- `packages/shared`: contratos/tipos compartilhados

Pipeline macro:

`Upload -> Laravel API -> Queue -> Python AI -> Resultado JSON -> Persistencia -> Frontend`

## Estrutura recomendada

```txt
ai-tab-generator/
├── apps/
│   ├── frontend/
│   ├── backend/
│   └── ai-service/
├── packages/
│   └── shared/
├── infra/
└── docs/
```

## Separacao de responsabilidades

- backend coordena o fluxo e nunca processa audio bruto
- ai-service concentra a logica de DSP/IA e nao conhece UI
- frontend apenas aciona APIs e renderiza estado/resultado
- contratos de payload devem ficar em `packages/shared`

## Contratos e integracao

Endpoints de integracao:

- `POST /api/upload` (frontend -> backend)
- `POST /process-audio` (backend -> ai-service)
- `GET /api/result/{job_id}` (frontend -> backend)

Recomendacoes:

- manter payloads versionados
- registrar logs estruturados por etapa do pipeline
- tratar timeout/retry na comunicacao backend -> ai-service

## Observabilidade e qualidade

- logs minimos: frequencias detectadas, notas geradas, mapeamento final
- testes: upload/job (backend), pitch/mapping (ai-service)
- cobertura inicial focada no caminho feliz + erros de integracao

## Deploy local com containers (opcional)

Servicos sugeridos para `docker compose`:

- `frontend`
- `backend`
- `ai-service`
- `postgres`
- `redis`
