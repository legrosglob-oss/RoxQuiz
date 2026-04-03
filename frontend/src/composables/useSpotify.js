import { ref } from 'vue'

let sdkReady = false
let sdkReadyPromise = null

function loadSpotifySDK() {
  if (sdkReadyPromise) return sdkReadyPromise
  sdkReadyPromise = new Promise((resolve) => {
    if (sdkReady) { resolve(); return }
    const script = document.createElement('script')
    script.src = 'https://sdk.scdn.co/spotify-player.js'
    script.async = true
    document.body.appendChild(script)
    window.onSpotifyWebPlaybackSDKReady = () => {
      sdkReady = true
      resolve()
    }
  })
  return sdkReadyPromise
}

// Singleton state — survit aux navigations
const isPlaying = ref(false)
const isReady = ref(false)
const deviceId = ref('')
const hasToken = ref(!!sessionStorage.getItem('spotify_access_token'))
const error = ref('')
let player = null
let previewAudio = null

function getToken() {
  return sessionStorage.getItem('spotify_access_token') || ''
}

async function initPlayer() {
  const token = getToken()
  if (!token) return

  // Si le player existe déjà et est prêt, ne pas recréer
  if (player && isReady.value) {
    console.log('[Spotify] Player already ready, reusing')
    return
  }

  // Si un player existe mais n'est plus prêt, le déconnecter proprement
  if (player) {
    player.disconnect()
    player = null
    isReady.value = false
    deviceId.value = ''
  }

  await loadSpotifySDK()

  player = new window.Spotify.Player({
    name: 'RoxQuiz',
    getOAuthToken: (cb) => cb(getToken()),
    volume: 0.8,
  })

  error.value = ''

  player.addListener('ready', ({ device_id }) => {
    deviceId.value = device_id
    isReady.value = true
    error.value = ''
    console.log('[Spotify] Player ready, device:', device_id)
  })

  player.addListener('not_ready', () => {
    isReady.value = false
    console.log('[Spotify] Player not ready')
  })

  player.addListener('player_state_changed', (state) => {
    if (state) {
      isPlaying.value = !state.paused
    }
  })

  player.addListener('initialization_error', ({ message }) => {
    console.error('[Spotify] Init error:', message)
    error.value = message
  })

  player.addListener('authentication_error', ({ message }) => {
    console.error('[Spotify] Auth error:', message)
    error.value = message
    refreshToken()
  })

  player.addListener('account_error', ({ message }) => {
    console.error('[Spotify] Account error:', message)
    error.value = 'Spotify Premium requis pour la lecture'
  })

  const connected = await player.connect()
  console.log('[Spotify] connect() =>', connected)
}

async function playTrack(spotifyUri) {
  if (!deviceId.value || !getToken()) return
  try {
    const resp = await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${deviceId.value}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ uris: [spotifyUri] }),
    })
    if (!resp.ok) {
      const text = await resp.text()
      console.error('[Spotify] play error:', resp.status, text)
    }
  } catch (e) {
    console.error('[Spotify] play fetch error:', e)
  }
}

async function refreshToken() {
  const rt = sessionStorage.getItem('spotify_refresh_token')
  if (!rt) return
  try {
    const resp = await fetch('/api/spotify/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    })
    const data = await resp.json()
    if (data.access_token) {
      sessionStorage.setItem('spotify_access_token', data.access_token)
    }
  } catch (e) {
    console.error('[Spotify] Refresh failed:', e)
  }
}

function playPreview(previewUrl) {
  stopPreview()
  if (!previewUrl) return
  previewAudio = new Audio(previewUrl)
  previewAudio.volume = 0.8
  previewAudio.play().then(() => {
    isPlaying.value = true
  }).catch((e) => {
    console.error('[Spotify] Preview play error:', e)
  })
  previewAudio.addEventListener('ended', () => {
    isPlaying.value = false
  })
}

function stopPreview() {
  if (previewAudio) {
    previewAudio.pause()
    previewAudio.src = ''
    previewAudio = null
  }
}

function stop() {
  if (player) {
    player.pause()
  }
  stopPreview()
  isPlaying.value = false
}

function disconnect() {
  if (player) {
    player.disconnect()
    player = null
  }
  sessionStorage.removeItem('spotify_access_token')
  sessionStorage.removeItem('spotify_refresh_token')
  isReady.value = false
  isPlaying.value = false
  deviceId.value = ''
  hasToken.value = false
  error.value = ''
}

export function useSpotify() {
  return { isPlaying, isReady, deviceId, hasToken, error, initPlayer, playTrack, playPreview, stop, refreshToken, disconnect }
}
