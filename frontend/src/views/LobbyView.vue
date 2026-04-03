<template>
  <div class="lobby">
    <h2>Partie <span class="code">{{ code }}</span></h2>

    <div class="players">
      <h3>Joueurs ({{ players.length }})</h3>
      <ul>
        <li v-for="p in players" :key="p.name" :class="{ host: p.is_host }">
          {{ p.name }}
          <span v-if="p.is_host" class="badge">Hôte</span>
        </li>
      </ul>
    </div>

    <div v-if="isHost" class="config">
      <h3>Options</h3>

      <label>
        Thème musical
        <select v-model="config.theme" @change="onThemeChange">
          <option :value="null">Aléatoire</option>
          <option v-for="t in themes" :key="t.key" :value="t.key">{{ t.label }}</option>
          <option value="__custom">Thème libre...</option>
        </select>
      </label>
      <label v-if="config.theme === '__custom'">
        Ton thème
        <input type="text" v-model="customTheme" placeholder="ex: jazz, reggae, k-pop..." @change="applyCustomTheme" />
      </label>

      <label>
        Nombre de questions
        <input type="number" v-model.number="config.num_rounds" min="3" max="30" @change="updateConfig" />
      </label>
      <label>
        Durée d'écoute (s)
        <input type="number" v-model.number="config.listen_duration" min="5" max="30" @change="updateConfig" />
      </label>
      <label>
        Temps de réponse (s)
        <input type="number" v-model.number="config.answer_duration" min="5" max="30" @change="updateConfig" />
      </label>
    </div>

    <div v-if="!isHost && selectedThemeLabel" class="theme-display">
      Thème : <strong>{{ selectedThemeLabel }}</strong>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <button v-if="isHost" class="primary start-btn" @click="startGame" :disabled="players.length < 2">
      Lancer la partie
    </button>
    <p v-else class="waiting">En attente du lancement par l'hôte...</p>

    <p class="share">Partage ce code : <strong>{{ code }}</strong></p>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '../composables/useWebSocket.js'

const props = defineProps({ code: String })
const router = useRouter()
const { connect, send, on } = useWebSocket()

const players = ref([])
const error = ref('')
const themes = ref([])
const customTheme = ref('')
const playerName = sessionStorage.getItem('playerName') || 'Joueur'
const isHost = computed(() => players.value.find(p => p.name === playerName)?.is_host ?? false)
const config = reactive({
  num_rounds: 10,
  listen_duration: 15,
  answer_duration: 15,
  theme: null,
})
const selectedThemeLabel = computed(() => {
  if (!config.theme) return null
  const found = themes.value.find(t => t.key === config.theme)
  return found ? found.label : config.theme
})

onMounted(async () => {
  try {
    const resp = await fetch('/api/themes')
    themes.value = await resp.json()
  } catch (e) {
    console.error('Failed to load themes', e)
  }

  connect(props.code, playerName)

  on('player_joined', (data) => {
    players.value = data.players
  })

  on('player_left', (data) => {
    players.value = data.players
  })

  on('config_updated', (data) => {
    const incoming = data.config
    // Si le thème reçu n'est pas dans la liste prédéfinie, c'est un thème custom
    if (incoming.theme && !themes.value.find(t => t.key === incoming.theme)) {
      customTheme.value = incoming.theme
      incoming.theme = '__custom'
    }
    Object.assign(config, incoming)
  })

  on('game_started', () => {
    router.push({ name: 'game', params: { code: props.code } })
  })

  on('error', (data) => {
    error.value = data.message || 'Erreur inconnue'
  })
})

function startGame() {
  send('start_game')
}

function onThemeChange() {
  if (config.theme !== '__custom') {
    customTheme.value = ''
    updateConfig()
  }
}

function applyCustomTheme() {
  if (customTheme.value.trim()) {
    updateConfig()
  }
}

function updateConfig() {
  const theme = config.theme === '__custom' ? (customTheme.value.trim() || null) : config.theme
  send('update_config', {
    num_rounds: config.num_rounds,
    listen_duration: config.listen_duration,
    answer_duration: config.answer_duration,
    theme,
  })
}
</script>

<style scoped>
.lobby {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding-top: 2rem;
}

.code {
  color: #1db954;
  font-family: monospace;
  font-size: 1.5rem;
  letter-spacing: 0.2rem;
}

.players {
  width: 100%;
  max-width: 400px;
}

.players ul {
  list-style: none;
  margin-top: 0.5rem;
}

.players li {
  padding: 0.5rem 1rem;
  background: #16213e;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.players li.host {
  border-left: 3px solid #1db954;
}

.badge {
  background: #1db954;
  color: white;
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
}

.config {
  width: 100%;
  max-width: 400px;
}

.config label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.config input[type="number"] {
  width: 80px;
  text-align: center;
}

.config input[type="text"] {
  flex: 1;
  min-width: 120px;
}

.config select {
  flex: 1;
  min-width: 160px;
  padding: 0.4rem;
  background: #1a1a2e;
  color: #eee;
  border: 1px solid #333;
  border-radius: 6px;
}

.theme-display {
  color: #888;
  font-size: 0.9rem;
}

.start-btn {
  font-size: 1.2rem;
  padding: 1rem 2rem;
}

.waiting {
  color: #888;
  font-style: italic;
}

.share {
  color: #666;
  font-size: 0.9rem;
  margin-top: auto;
  padding-bottom: 1rem;
}

.error {
  color: #e74c3c;
  background: #e74c3c22;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  width: 100%;
  max-width: 400px;
  text-align: center;
}
</style>
