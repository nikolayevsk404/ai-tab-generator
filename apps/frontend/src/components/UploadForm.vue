<script setup lang="ts">
defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  submit: [file: File]
}>()

function onChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) {
    return
  }

  emit('submit', file)
  input.value = ''
}
</script>

<template>
  <label class="upload-card">
    <input accept=".mp3,.wav" class="upload-input" type="file" :disabled="disabled" @change="onChange" />
    <div class="card-head">
      <span class="upload-kicker">Clique aqui para enviar</span>
      <strong>Enviar Solo de Guitarra</strong>
    </div>
    <div class="card-stack">
      <span>Selecione um `.mp3` ou `.wav`. O backend envia para a fila e o microservico detecta automaticamente o contexto da guitarra para gerar a tab.</span>
      <span class="upload-hint">A IA tenta reconhecer o ritmo e mapeamento do braço, sem precisar de configuracao manual.</span>
    </div>
  </label>
</template>
