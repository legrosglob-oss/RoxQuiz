<template>
  <div class="session">
    <!-- LOBBY -->
    <div v-if="phase === 'lobby'" class="lobby">
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

      <!-- Spotify connection pour l'hôte -->
      <div v-if="isHost" class="spotify-status">
        <div v-if="spotifyReady" class="spotify-connected">
          Spotify connecté
          <button class="spotify-disconnect-btn" @click="disconnectSpotify">Déconnecter</button>
        </div>
        <div v-else-if="hasToken" class="spotify-connecting">
          Connexion Spotify en cours...
          <button class="spotify-disconnect-btn" @click="disconnectSpotify">Réessayer</button>
        </div>
        <button v-else class="spotify-login-btn" @click="openSpotifyLogin">
          Se connecter à Spotify
        </button>
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

      <button v-if="isHost" class="primary start-btn" @click="startGame" :disabled="players.length < 1 || !spotifyReady">
        Lancer la partie
      </button>
      <p v-if="isHost && !spotifyReady" class="hint">Connecte-toi à Spotify Premium pour lancer</p>
      <p v-if="!isHost" class="waiting">En attente du lancement par l'hôte...</p>

      <p class="share">Partage ce code : <strong>{{ code }}</strong></p>
    </div>

    <!-- QUESTION -->
    <div v-else-if="phase === 'question'" class="game">
      <div class="header">
        <span>Question {{ round }} / {{ totalRounds }}</span>
        <span class="timer" v-if="timeLeft > 0">{{ timeLeft }}s</span>
      </div>

      <div class="music-indicator" :class="{ playing: currentHasAudio }">
        <div class="pulse"></div>
        <span v-if="currentHasAudio">Écoute...</span>
        <span v-else>Pas d'audio</span>
      </div>

      <div class="question-card">
        <h3>{{ question.text }}</h3>

        <div v-if="question.type === 'mcq'" class="choices">
          <button
            v-for="choice in question.choices"
            :key="choice"
            class="choice-btn"
            :class="{ selected: selectedAnswer === choice, disabled: answered }"
            @click="submitChoice(choice)"
            :disabled="answered"
          >
            {{ choice }}
          </button>
        </div>

        <div v-else class="text-answer">
          <input
            v-model="textAnswer"
            placeholder="Ta réponse..."
            @keyup.enter="submitText"
            :disabled="answered"
          />
          <button class="primary" @click="submitText" :disabled="answered || !textAnswer.trim()">
            Valider
          </button>
        </div>

        <p v-if="answered" class="answered-msg">Réponse envoyée !</p>
      </div>

      <div class="scoreboard">
        <div v-for="(score, name) in scores" :key="name" class="score-item">
          {{ name }}: {{ score }}
        </div>
      </div>
    </div>

    <!-- ROUND RESULTS -->
    <div v-else-if="phase === 'results'" class="game">
      <div class="header">
        <span>Résultat — Question {{ round }} / {{ totalRounds }}</span>
      </div>

      <div class="track-reveal" v-if="trackInfo">
        <img v-if="trackInfo.image_url" :src="trackInfo.image_url" class="album-art" />
        <div>
          <h3>{{ trackInfo.name }}</h3>
          <p>{{ trackInfo.artist }} — {{ trackInfo.album }} ({{ trackInfo.year }})</p>
        </div>
      </div>

      <p class="correct-answer">Réponse : <strong>{{ correctAnswer }}</strong></p>

      <div class="round-scores">
        <div
          v-for="(score, name) in scores"
          :key="name"
          class="score-row"
          :class="{ correct: correctPlayers.includes(name) }"
        >
          <span>{{ name }}</span>
          <span>{{ score }} pts</span>
        </div>
      </div>
    </div>

    <!-- GAME OVER -->
    <div v-else-if="phase === 'finished'" class="score-view">
      <h1>Fin de la partie !</h1>

      <div class="podium" v-if="ranking.length">
        <div
          v-for="(player, index) in ranking.slice(0, 3)"
          :key="player.name"
          class="podium-item"
          :class="`place-${index + 1}`"
        >
          <div class="rank">{{ index + 1 }}</div>
          <div class="name">{{ player.name }}</div>
          <div class="pts">{{ player.score }} pts</div>
        </div>
      </div>

      <div class="full-ranking" v-if="ranking.length > 3">
        <div v-for="(player, index) in ranking.slice(3)" :key="player.name" class="rank-row">
          <span>{{ index + 4 }}. {{ player.name }}</span>
          <span>{{ player.score }} pts</span>
        </div>
      </div>

      <button class="primary" @click="goHome">Nouvelle partie</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '../composables/useWebSocket.js'
import { useSpotify } from '../composables/useSpotify.js'

const props = defineProps({ code: String })
const router = useRouter()
const { connected, connect, send, on } = useWebSocket()
const { isPlaying, isReady: spotifyPlayerReady, deviceId, hasToken, initPlayer, playTrack, stop, disconnect: spotifyDisconnect } = useSpotify()

const playerName = sessionStorage.getItem('playerName') || 'Joueur'

// State
const phase = ref('lobby')
const error = ref('')
const players = ref([])
const themes = ref([])
const customTheme = ref('')
const config = reactive({ num_rounds: 10, listen_duration: 15, answer_duration: 15, theme: null })
const selectedThemeLabel = computed(() => {
  if (!config.theme) return null
  const found = themes.value.find(t => t.key === config.theme)
  return found ? found.label : config.theme
})
const isHost = computed(() => players.value.find(p => p.name === playerName)?.is_host ?? false)
const spotifyReady = computed(() => hasToken.value && spotifyPlayerReady.value)

// Game state
const round = ref(0)
const totalRounds = ref(10)
const question = ref({ text: '', type: 'mcq', choices: [] })
const selectedAnswer = ref('')
const textAnswer = ref('')
const answered = ref(false)
const timeLeft = ref(0)
const scores = ref({})
const correctAnswer = ref('')
const correctPlayers = ref([])
const trackInfo = ref(null)
const currentHasAudio = ref(false)
const ranking = ref([])

let timerInterval = null

function startTimer(deadline) {
  clearInterval(timerInterval)
  const update = () => {
    const remaining = Math.ceil(deadline - Date.now() / 1000)
    timeLeft.value = remaining > 0 ? remaining : 0
    if (remaining <= 0) clearInterval(timerInterval)
  }
  update()
  timerInterval = setInterval(update, 1000)
}

function submitChoice(choice) {
  if (answered.value) return
  selectedAnswer.value = choice
  answered.value = true
  send('submit_answer', { answer: choice })
}

function submitText() {
  if (answered.value || !textAnswer.value.trim()) return
  answered.value = true
  send('submit_answer', { answer: textAnswer.value.trim() })
}

function startGame() {
  error.value = ''
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

function goHome() {
  router.push({ name: 'home' })
}

function disconnectSpotify() {
  spotifyDisconnect()
  spotifyTokenSent = false
}

function openSpotifyLogin() {
  const url = `/api/spotify/login?game_code=${props.code}`
  const w = 500, h = 700
  const left = window.screenX + (window.innerWidth - w) / 2
  const top = window.screenY + (window.innerHeight - h) / 2
  window.open(url, 'spotify-login', `width=${w},height=${h},left=${left},top=${top}`)
}

// Envoyer le token Spotify et device_id au backend quand prêt
let spotifyTokenSent = false
watch([spotifyPlayerReady, deviceId, connected, players], () => {
  if (!spotifyTokenSent && spotifyPlayerReady.value && deviceId.value && connected.value && isHost.value) {
    console.log('[RoxQuiz] Sending Spotify token, device:', deviceId.value)
    send('set_spotify_token', {
      access_token: sessionStorage.getItem('spotify_access_token'),
      device_id: deviceId.value,
    })
    spotifyTokenSent = true
  }
})

function onSpotifyMessage(event) {
  if (event.data?.type === 'spotify_token') {
    sessionStorage.setItem('spotify_access_token', event.data.access_token)
    sessionStorage.setItem('spotify_refresh_token', event.data.refresh_token || '')
    hasToken.value = true
    initPlayer()
  }
}

onMounted(async () => {
  window.addEventListener('message', onSpotifyMessage)

  // Charger les thèmes disponibles
  try {
    const resp = await fetch('/api/themes')
    themes.value = await resp.json()
  } catch (e) {
    console.error('Failed to load themes', e)
  }

  // Initialiser le player Spotify si l'hôte a un token
  if (hasToken.value) {
    await initPlayer()
  }

  connect(props.code, playerName)

  // Lobby events
  on('player_joined', (data) => { players.value = data.players })
  on('player_left', (data) => { players.value = data.players })
  on('config_updated', (data) => {
    const incoming = data.config
    if (incoming.theme && !themes.value.find(t => t.key === incoming.theme)) {
      customTheme.value = incoming.theme
      incoming.theme = '__custom'
    }
    Object.assign(config, incoming)
  })
  on('error', (data) => { error.value = data.message || 'Erreur inconnue' })
  on('reconnected', (data) => { players.value = data.players })

  // Game events
  on('game_started', (data) => {
    totalRounds.value = data.num_rounds
  })

  on('new_round', (data) => {
    phase.value = 'question'
    round.value = data.round
    totalRounds.value = data.total_rounds
    question.value = data.question
    selectedAnswer.value = ''
    textAnswer.value = ''
    answered.value = false

    // Seul l'hôte joue la musique via le Web Playback SDK
    const canPlay = isHost.value && spotifyPlayerReady.value && data.track.spotify_uri
    currentHasAudio.value = data.has_audio

    if (canPlay) {
      playTrack(data.track.spotify_uri)
    }

    startTimer(data.round_deadline)
  })

  on('round_result', (data) => {
    phase.value = 'results'
    correctAnswer.value = data.correct_answer
    correctPlayers.value = data.correct_players
    scores.value = data.scores
    trackInfo.value = data.track
    clearInterval(timerInterval)
  })

  on('game_over', (data) => {
    phase.value = 'finished'
    ranking.value = data.ranking
    stop()
    clearInterval(timerInterval)
  })
})

onUnmounted(() => {
  window.removeEventListener('message', onSpotifyMessage)
  stop()
  clearInterval(timerInterval)
})
</script>

<style scoped>
.session { flex: 1; display: flex; flex-direction: column; }

/* Lobby */
.lobby {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; gap: 1.5rem; padding-top: 2rem;
}
.code {
  color: #1db954; font-family: monospace; font-size: 1.5rem; letter-spacing: 0.2rem;
}
.players { width: 100%; max-width: 400px; }
.players ul { list-style: none; margin-top: 0.5rem; }
.players li {
  padding: 0.5rem 1rem; background: #16213e; border-radius: 8px;
  margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;
}
.players li.host { border-left: 3px solid #1db954; }
.badge {
  background: #1db954; color: white; font-size: 0.7rem;
  padding: 0.2rem 0.5rem; border-radius: 4px; text-transform: uppercase;
}

.spotify-status { width: 100%; max-width: 400px; text-align: center; }
.spotify-connected {
  color: #1db954; font-weight: 600; padding: 0.5rem;
  background: #1db95422; border-radius: 8px;
}
.spotify-login-btn {
  display: inline-block; background: #1db954; color: white;
  padding: 0.75rem 1.5rem; border-radius: 24px; text-decoration: none;
  font-weight: 600; font-size: 1rem;
}
.spotify-login-btn:hover { opacity: 0.85; }
.spotify-connecting {
  color: #e8a838; font-weight: 600; padding: 0.5rem;
  background: #e8a83822; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; gap: 0.75rem;
}
.spotify-disconnect-btn {
  background: transparent; color: #888; border: 1px solid #444;
  padding: 0.3rem 0.8rem; border-radius: 12px; font-size: 0.75rem;
  cursor: pointer;
}
.spotify-disconnect-btn:hover { color: #e74c3c; border-color: #e74c3c; }

.config { width: 100%; max-width: 400px; }
.config label {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.5rem; font-size: 0.9rem;
}
.config input[type="number"] { width: 80px; text-align: center; }
.config input[type="text"] { flex: 1; min-width: 120px; }
.config select {
  flex: 1; min-width: 160px; padding: 0.4rem;
  background: #1a1a2e; color: #eee; border: 1px solid #333; border-radius: 6px;
}
.theme-display { color: #888; font-size: 0.9rem; }
.start-btn { font-size: 1.2rem; padding: 1rem 2rem; }
.waiting { color: #888; font-style: italic; }
.hint { color: #888; font-size: 0.85rem; }
.share { color: #666; font-size: 0.9rem; margin-top: auto; padding-bottom: 1rem; }
.error {
  color: #e74c3c; background: #e74c3c22;
  padding: 0.75rem 1rem; border-radius: 8px;
  width: 100%; max-width: 400px; text-align: center;
}

/* Game */
.game { flex: 1; display: flex; flex-direction: column; gap: 1rem; }
.header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 0; font-size: 0.9rem; color: #888;
}
.timer {
  background: #1db954; color: white; padding: 0.3rem 0.8rem;
  border-radius: 20px; font-weight: 700; font-size: 1.1rem;
}
.music-indicator { text-align: center; padding: 1.5rem; color: #888; }
.music-indicator.playing { color: #1db954; }
.pulse {
  width: 60px; height: 60px; border-radius: 50%;
  background: #1db95433; margin: 0 auto 1rem;
}
.music-indicator.playing .pulse {
  animation: pulse 1.5s ease-in-out infinite; background: #1db95466;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.2); opacity: 1; }
}
.question-card { background: #16213e; border-radius: 12px; padding: 1.5rem; }
.question-card h3 { margin-bottom: 1rem; font-size: 1.2rem; }
.choices { display: flex; flex-direction: column; gap: 0.5rem; }
.choice-btn {
  background: #1a1a2e; color: #eee; padding: 0.75rem 1rem;
  border: 2px solid #333; border-radius: 8px; text-align: left; font-size: 1rem;
}
.choice-btn.selected { border-color: #1db954; background: #1db95422; }
.choice-btn.disabled { opacity: 0.6; }
.text-answer { display: flex; gap: 0.5rem; }
.text-answer input { flex: 1; }
.answered-msg { color: #1db954; margin-top: 0.75rem; font-size: 0.9rem; }

.track-reveal {
  display: flex; gap: 1rem; align-items: center;
  background: #16213e; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
}
.album-art { width: 80px; height: 80px; border-radius: 8px; object-fit: cover; }
.correct-answer { color: #1db954; margin-bottom: 1rem; font-size: 1.1rem; }
.round-scores { display: flex; flex-direction: column; gap: 0.4rem; }
.score-row {
  display: flex; justify-content: space-between;
  padding: 0.5rem 1rem; background: #16213e; border-radius: 8px;
}
.score-row.correct { border-left: 3px solid #1db954; }
.scoreboard {
  margin-top: auto; display: flex; gap: 1rem; justify-content: center;
  padding: 0.75rem; background: #16213e; border-radius: 8px;
  font-size: 0.85rem; color: #888; flex-wrap: wrap;
}

/* Score */
.score-view {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; gap: 2rem; padding-top: 2rem;
}
.score-view h1 {
  font-size: 2rem; background: linear-gradient(135deg, #1db954, #1ed760);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.podium {
  display: flex; gap: 1rem; align-items: flex-end;
  justify-content: center; width: 100%;
}
.podium-item {
  display: flex; flex-direction: column; align-items: center;
  background: #16213e; border-radius: 12px; padding: 1.5rem 1rem; min-width: 100px;
}
.place-1 { order: 2; border: 2px solid #ffd700; transform: scale(1.1); }
.place-2 { order: 1; border: 2px solid #c0c0c0; }
.place-3 { order: 3; border: 2px solid #cd7f32; }
.rank { font-size: 2rem; font-weight: 900; }
.place-1 .rank { color: #ffd700; }
.place-2 .rank { color: #c0c0c0; }
.place-3 .rank { color: #cd7f32; }
.name { font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0; }
.pts { color: #1db954; font-weight: 700; }
.full-ranking { width: 100%; max-width: 400px; }
.rank-row {
  display: flex; justify-content: space-between;
  padding: 0.5rem 1rem; background: #16213e; border-radius: 8px; margin-bottom: 0.4rem;
}
</style>
