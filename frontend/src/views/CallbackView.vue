<template>
  <div class="callback">
    <p>Connexion Spotify en cours...</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  // Les tokens sont dans le fragment (#)
  const hash = window.location.hash.substring(1)
  const params = new URLSearchParams(hash)
  const accessToken = params.get('access_token')
  const refreshToken = params.get('refresh_token')
  const gameCode = params.get('game_code')

  if (accessToken) {
    sessionStorage.setItem('spotify_access_token', accessToken)
    sessionStorage.setItem('spotify_refresh_token', refreshToken || '')
  }

  // Si ouvert en popup, envoyer le token à la fenêtre parente et fermer
  if (window.opener) {
    window.opener.postMessage({
      type: 'spotify_token',
      access_token: accessToken,
      refresh_token: refreshToken || '',
    }, '*')
    window.close()
    return
  }

  if (gameCode) {
    router.replace({ name: 'session', params: { code: gameCode } })
  } else {
    router.replace({ name: 'home' })
  }
})
</script>

<style scoped>
.callback {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
}
</style>
