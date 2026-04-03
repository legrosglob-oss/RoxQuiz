<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #1a1a2e;
  color: #eee;
  min-height: 100vh;
}

#app {
  max-width: 600px;
  margin: 0 auto;
  padding: 1rem;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

button {
  cursor: pointer;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  transition: opacity 0.2s;
}

button:hover {
  opacity: 0.85;
}

button.primary {
  background: #1db954;
  color: white;
}

button.secondary {
  background: #333;
  color: white;
}

input {
  border: 2px solid #333;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  background: #16213e;
  color: #eee;
  width: 100%;
}

input:focus {
  outline: none;
  border-color: #1db954;
}
</style>
