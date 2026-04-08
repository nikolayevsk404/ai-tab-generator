# AI Service

Microservico FastAPI responsavel pela transcricao de solos de guitarra e geracao
do `.gp5`.

Arquitetura atual:

- transcricao principal com backend modular
- fallback heuristico com `librosa`
- suporte a embeddings de audio para classificacao/contexto
- exportacao Guitar Pro 5 com foco em solo monofonico

Stack prevista para evolucao:

- `basic-pitch` como backend principal de transcricao de notas
- `madmom` para beats/BPM/grade ritmica
- `torchopenl3` para embeddings de audio

Mesmo sem essas libs opcionais instaladas, o servico continua funcionando com o
fallback atual.

## Rodando localmente

1. Criar ambiente virtual Python.
2. Instalar `requirements.txt`.
3. Opcionalmente instalar `basic-pitch`, `madmom` e `torchopenl3` para usar os backends pre-treinados.
4. Subir com `uvicorn app.main:app --reload --port 8001`.
