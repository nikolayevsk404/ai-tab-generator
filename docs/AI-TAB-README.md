# AI Tab Generator

## Visão Geral
Converte áudio em tablatura de guitarra.

## Stack
Laravel + Vue + Python

## Objetivo
IA aplicada em áudio + microserviço

---

# AI Tab Generator

## Visão Geral

Sistema que recebe um áudio (guitarra) e gera automaticamente uma tablatura compatível com Guitar Pro.

Inspirado no workflow de músicos técnicos (ex: Tosin Abasi), o objetivo é demonstrar:

- IA aplicada em áudio (DSP + ML)
- Pipeline inteligente (Agent)
- Integração multi-stack (Laravel + Python)
- Engenharia além de CRUD

## Tech Stack

### Backend API
- Laravel (PHP)
- PostgreSQL

### Frontend
- Vue 3

### AI Service
- Python
- librosa (audio processing)
- numpy

## Features

### Core
- Upload de áudio (.mp3/.wav)
- Processamento assíncrono
- Geração de tablatura (JSON)

### Output
- Visualização simples no frontend
- Export futuro:
  - .gp5 (Guitar Pro)
  - MIDI

### IA
- Detecção de pitch (frequência)
- Mapeamento para braço da guitarra (7 cordas)

## AI Architecture

### Conceito

O agent é um pipeline inteligente (não é chatbot).

Fluxo:
Audio → Pitch Detection → Note Mapping → Fretboard Mapping → Tab Output

## Agent Definition

### Nome
AudioToTabAgent

### Input
- arquivo de áudio (.wav/.mp3)

### Output
```json
[
  { "string": 7, "fret": 0, "time": 0.1 },
  { "string": 6, "fret": 3, "time": 0.5 }
]
```

## Pipeline

### 1. Load Audio
```python
y, sr = librosa.load(file_path)
```

### 2. Pitch Detection
```python
pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
```

### 3. Convert Frequency → Note
```python
def freq_to_note(freq):
    # ex: 440Hz → A4
    return note
```

### 4. Map Note → Fretboard (7 cordas)
```python
TUNING = ["B1","E2","A2","D3","G3","B3","E4"]

def map_to_fret(note):
    # retorna melhor string + fret
    return {"string": 7, "fret": 5}
```

### 5. Generate Tab
```python
tab = [
  {"string": 6, "fret": 3, "time": 0.2}
]
```

## Arquitetura

```
/frontend (Vue)
   ↓ HTTP
/backend (Laravel API)
   ↓
/queue (job async)
   ↓
/python-service (AI)
   ↓
/database (PostgreSQL)
```

## API

### Upload
```
POST /api/upload
```

Response:
```json
{
  "job_id": "123"
}
```

### Get Result
```
GET /api/result/{job_id}
```

## Processamento Assíncrono

Laravel Queue:

```php
ProcessAudioJob::dispatch($filePath);
```

## Testes

### Python
- Deve detectar notas corretamente
- Deve mapear notas para posições válidas

```python
def test_map_note():
    assert map_to_fret("E2")["string"] == 6
```

### Backend
- Upload funciona
- Job é processado

## Logs

```json
{
  "detected_notes": ["E2", "G2"],
  "mapped_positions": [
    { "string": 6, "fret": 0 }
  ]
}
```

## Backlog Inicial

### TASK 1 — Laravel API
Crie uma API Laravel com:
- endpoint de upload
- armazenamento de arquivos
- fila (queue) configurada

### TASK 2 — Job
Crie um Job ProcessAudioJob que:
- recebe caminho do arquivo
- chama o serviço Python

### TASK 3 — Python Service
Crie um microserviço Python com Flask que:
- recebe áudio via POST
- retorna JSON de notas detectadas

### TASK 4 — Pipeline IA
Implemente:
- pitch detection com librosa
- conversão para notas
- mapeamento para fretboard

### TASK 5 — Vue Frontend
Crie tela com:
- upload de arquivo
- status do processamento
- exibição da tablatura

### TASK 6 — Persistência
Salvar resultado no PostgreSQL

## Diferenciais Técnicos

- IA aplicada em áudio
- Microserviço Python integrado com Laravel
- Pipeline real de processamento
- Suporte a guitarra de 7 cordas
- Base para exportar Guitar Pro

## Custos

- librosa roda local
- sem necessidade de API paga