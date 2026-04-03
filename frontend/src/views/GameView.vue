<template>
  <div class="game">
    <div class="header">
      <span>Question {{ round }} / {{ totalRounds }}</span>
      <span class="timer" v-if="timeLeft > 0">{{ timeLeft }}s</span>
    </div>

    <!-- Phase : écoute + question -->
    <div v-if="phase === 'question'" class="question-phase">
      <div class="music-indicator" :class="{ playing: isPlaying }">
        <div class="pulse"></div>
        <span>{{ isPlaying ? 'Écoute...' : 'Prépare-toi' }}</span>
      </div>

      <div class="question-card">
        <h3>{{ question.text }}</h3>

        <!-- QCM -->
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

        <!-- Texte libre -->
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
    </div>

    <!-- Phase : résultats du round -->
    <div v-else-if="phase === 'results'" class="results-phase">
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

    <!-- Scores en bas -->
    <div class="scoreboard">
      <div v-for="(score, name) in scores" :key="name" class="score-item">
        {{ name }}: {{ score }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '../composables/useWebSocket.js'
import { useSpotify } from '../composables/useSpotify.js'

const props = defineProps({ code: String })
const router = useRouter()
const { connect, send, on } = useWebSocket()
const { isPlaying, playPreview, stop } = useSpotify()

const playerName = sessionStorage.getItem('playerName') || 'Joueur'
const phase = ref('question')
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

onMounted(() => {
  connect(props.code, playerName)

  on('new_round', (data) => {
    phase.value = 'question'
    round.value = data.round
    totalRounds.value = data.total_rounds
    question.value = data.question
    selectedAnswer.value = ''
    textAnswer.value = ''
    answered.value = false

    // Jouer la musique
    if (data.track.preview_url) {
      playPreview(data.track.preview_url, data.listen_duration)
    }

    startTimer(data.round_deadline)
  })

  on('round_result', (data) => {
    phase.value = 'results'
    correctAnswer.value = data.correct_answer
    correctPlayers.value = data.correct_players
    scores.value = data.scores
    trackInfo.value = data.track
    stop()
    clearInterval(timerInterval)
  })

  on('game_over', (data) => {
    stop()
    clearInterval(timerInterval)
    // Stocker le ranking pour ScoreView
    sessionStorage.setItem('ranking', JSON.stringify(data.ranking))
    router.push({ name: 'score', params: { code: props.code } })
  })
})

onUnmounted(() => {
  stop()
  clearInterval(timerInterval)
})
</script>

<style scoped>
.game {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  font-size: 0.9rem;
  color: #888;
}

.timer {
  background: #1db954;
  color: white;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 1.1rem;
}

.music-indicator {
  text-align: center;
  padding: 1.5rem;
  color: #888;
}

.music-indicator.playing {
  color: #1db954;
}

.pulse {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #1db95433;
  margin: 0 auto 1rem;
}

.music-indicator.playing .pulse {
  animation: pulse 1.5s ease-in-out infinite;
  background: #1db95466;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.2); opacity: 1; }
}

.question-card {
  background: #16213e;
  border-radius: 12px;
  padding: 1.5rem;
}

.question-card h3 {
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.choices {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.choice-btn {
  background: #1a1a2e;
  color: #eee;
  padding: 0.75rem 1rem;
  border: 2px solid #333;
  border-radius: 8px;
  text-align: left;
  font-size: 1rem;
}

.choice-btn.selected {
  border-color: #1db954;
  background: #1db95422;
}

.choice-btn.disabled {
  opacity: 0.6;
}

.text-answer {
  display: flex;
  gap: 0.5rem;
}

.text-answer input {
  flex: 1;
}

.answered-msg {
  color: #1db954;
  margin-top: 0.75rem;
  font-size: 0.9rem;
}

.results-phase {
  flex: 1;
}

.track-reveal {
  display: flex;
  gap: 1rem;
  align-items: center;
  background: #16213e;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.album-art {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
}

.correct-answer {
  color: #1db954;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.round-scores {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.score-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: #16213e;
  border-radius: 8px;
}

.score-row.correct {
  border-left: 3px solid #1db954;
}

.scoreboard {
  margin-top: auto;
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding: 0.75rem;
  background: #16213e;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #888;
  flex-wrap: wrap;
}
</style>
