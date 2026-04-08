# Agent

## Nome
AudioToTabAgent

## Pipeline
- carregar audio
- gerar embedding de audio
- transcrever notas com `basic-pitch` quando disponivel
- usar fallback com `librosa` quando necessario
- quantizar no grid ritmico
- mapear no braco de 6 cordas
- exportar `.gp5`
