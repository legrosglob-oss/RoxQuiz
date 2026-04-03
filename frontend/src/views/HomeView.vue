<template>
  <div class="home">
    <h1 class="title">Hitster</h1>
    <p class="subtitle">Le jeu musical en ligne</p>

    <div class="form-section">
      <input
        v-model="playerName"
        placeholder="Ton prénom"
        maxlength="20"
        @keyup.enter="joinMode ? joinGame() : createGame()"
      />
    </div>

    <div v-if="!joinMode" class="actions">
      <button class="primary" @click="createGame" :disabled="!playerName.trim()">
        Créer une partie
      </button>
      <button class="secondary" @click="joinMode = true">
        Rejoindre une partie
      </button>
    </div>

    <div v-else class="actions">
      <input
        v-model="gameCode"
        placeholder="Code de la partie"
        maxlength="6"
        @keyup.enter="joinGame"
        class="code-input"
      />
      <button class="primary" @click="joinGame" :disabled="!playerName.trim() || !gameCode.trim()">
        Rejoindre
      </button>
      <button class="secondary" @click="joinMode = false">
        Retour
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const playerName = ref('')
const gameCode = ref('')
const joinMode = ref(false)
const error = ref('')

async function createGame() {
  if (!playerName.value.trim()) return
  try {
    const resp = await fetch('/api/game', { method: 'POST' })
    const data = await resp.json()
    sessionStorage.setItem('playerName', playerName.value.trim())
    router.push({ name: 'session', params: { code: data.code } })
  } catch {
    error.value = 'Erreur lors de la création de la partie'
  }
}

async function joinGame() {
  if (!playerName.value.trim() || !gameCode.value.trim()) return
  const code = gameCode.value.trim().toUpperCase()
  try {
    const resp = await fetch(`/api/game/${code}`)
    const data = await resp.json()
    if (data.error) {
      error.value = 'Partie introuvable'
      return
    }
    sessionStorage.setItem('playerName', playerName.value.trim())
    router.push({ name: 'session', params: { code } })
  } catch {
    error.value = 'Erreur de connexion'
  }
}
</script>

<style scoped>
.home {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}

.title {
  font-size: 3rem;
  background: linear-gradient(135deg, #1db954, #1ed760);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #888;
  font-size: 1.1rem;
}

.form-section {
  width: 100%;
  max-width: 300px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
  max-width: 300px;
}

.code-input {
  text-align: center;
  text-transform: uppercase;
  font-size: 1.5rem;
  letter-spacing: 0.3rem;
}

.error {
  color: #e74c3c;
  font-size: 0.9rem;
}
</style>
