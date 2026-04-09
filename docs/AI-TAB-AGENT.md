# AI Tab Generator - Agent Spec

## Nome

`AudioToTabAgent`

## Papel no sistema

Converter audio em uma representacao de tablatura tocavel, preservando timing e minimizando ambiguidades no mapeamento de corda/traste.

## Entrada

- arquivo de audio (`.wav`/`.mp3`)
- metadados opcionais (BPM, tuning alvo, assinatura de tempo)

## Saida

Lista de eventos de tab em JSON:

```json
[
  { "string": 7, "fret": 0, "time": 0.1 },
  { "string": 6, "fret": 3, "time": 0.5 }
]
```

## Pipeline do agent

1. carregar e normalizar audio
2. transcrever frequencias/notas (`basic-pitch` quando disponivel)
3. aplicar fallback com `librosa` em caso de baixa confianca
4. converter frequencia para nota musical
5. mapear nota para braço da guitarra (string + fret)
6. quantizar eventos no grid ritmico
7. retornar tab final e logs tecnicos

## Regras operacionais

- priorizar menor movimento de mao entre eventos consecutivos
- evitar posicoes invalidas para o tuning configurado
- manter timestamps consistentes entre transcricao e tab final

## Evolucoes sugeridas

- ajuste de confianca por trecho de audio
- suporte a multiplos tunings e quantidade de cordas
- exportacao dedicada para `.gp5` e MIDI
