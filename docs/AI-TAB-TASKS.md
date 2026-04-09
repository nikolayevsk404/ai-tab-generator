# AI Tab Generator - Tasks

## Fase 1 - Fundacao

- [ ] criar endpoint `POST /api/upload` no backend
- [ ] persistir arquivo e metadados do job
- [ ] configurar fila e worker de processamento

## Fase 2 - Processamento de IA

- [ ] implementar `POST /process-audio` no ai-service
- [ ] montar pipeline do `AudioToTabAgent`
- [ ] incluir fallback de transcricao (`basic-pitch` -> `librosa`)

## Fase 3 - Integracao

- [ ] integrar `ProcessAudioJob` com ai-service via HTTP
- [ ] salvar resultado de tab e status no backend
- [ ] expor `GET /api/result/{job_id}`

## Fase 4 - Frontend

- [ ] tela de upload e status de processamento
- [ ] polling de status/resultado
- [ ] visualizacao basica da tablatura

## Fase 5 - Qualidade e observabilidade

- [ ] testes backend (upload/job/result)
- [ ] testes ai-service (pitch/mapeamento)
- [ ] logs estruturados por etapa do pipeline
