<template>
  <div class="score-view">
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
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const ranking = ref([])

try {
  ranking.value = JSON.parse(sessionStorage.getItem('ranking') || '[]')
} catch {
  ranking.value = []
}

function goHome() {
  router.push({ name: 'home' })
}
</script>

<style scoped>
.score-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  padding-top: 2rem;
}

h1 {
  font-size: 2rem;
  background: linear-gradient(135deg, #1db954, #1ed760);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.podium {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  justify-content: center;
  width: 100%;
}

.podium-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #16213e;
  border-radius: 12px;
  padding: 1.5rem 1rem;
  min-width: 100px;
}

.place-1 {
  order: 2;
  border: 2px solid #ffd700;
  transform: scale(1.1);
}

.place-2 {
  order: 1;
  border: 2px solid #c0c0c0;
}

.place-3 {
  order: 3;
  border: 2px solid #cd7f32;
}

.rank {
  font-size: 2rem;
  font-weight: 900;
}

.place-1 .rank { color: #ffd700; }
.place-2 .rank { color: #c0c0c0; }
.place-3 .rank { color: #cd7f32; }

.name {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0.5rem 0;
}

.pts {
  color: #1db954;
  font-weight: 700;
}

.full-ranking {
  width: 100%;
  max-width: 400px;
}

.rank-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: #16213e;
  border-radius: 8px;
  margin-bottom: 0.4rem;
}
</style>
