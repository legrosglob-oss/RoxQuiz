import { ref, onUnmounted } from 'vue'

export function useWebSocket() {
  const ws = ref(null)
  const connected = ref(false)
  const lastMessage = ref(null)
  const handlers = new Map()

  function connect(gameCode, playerName) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}/ws/${gameCode}/${playerName}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
    }

    ws.value.onclose = () => {
      connected.value = false
    }

    ws.value.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      lastMessage.value = msg
      const handler = handlers.get(msg.type)
      if (handler) handler(msg.data)
    }
  }

  function send(type, data = {}) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type, data }))
    }
  }

  function on(type, handler) {
    handlers.set(type, handler)
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  onUnmounted(disconnect)

  return { connected, lastMessage, connect, send, on, disconnect }
}
