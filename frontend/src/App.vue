<script setup lang="ts">
import {onMounted} from 'vue'
import {useGuest} from './stores/guest'
import ThemeSwitch from './components/ThemeSwitch.vue'
const guest=useGuest();onMounted(guest.init)
</script>
<template>
 <a class="skip" href="#main">Skip to content</a>
 <div class="app-layout">
 <aside class="rail"><RouterLink to="/" class="brand" aria-label="Human Fluid home"><span class="brand-symbol" aria-hidden="true">h<span>f</span><i></i></span><span>human<br>fluid<span class="brand-period">.</span></span></RouterLink>
 <div class="rail-label">A PRACTICE IN THINKING</div>
 <nav aria-label="Main navigation"><RouterLink to="/" :class="{selected:$route.path==='/'||$route.path.startsWith('/train')}"><span aria-hidden="true">↗</span> Train <small>01</small></RouterLink><RouterLink to="/review"><span aria-hidden="true">↺</span> Review <small>02</small></RouterLink><RouterLink to="/progress"><span aria-hidden="true">▥</span> Progress <small>03</small></RouterLink><RouterLink to="/about"><span aria-hidden="true">◎</span> About <small>04</small></RouterLink></nav>
 <div class="rail-footer"><ThemeSwitch/><span class="guest-dot"></span> Guest notebook<small>Progress saved on this device</small><RouterLink to="/settings">Settings & AI access ↗</RouterLink><RouterLink v-if="guest.me?.admin" to="/admin">Admin ↗</RouterLink></div>
 </aside>
 <div class="workspace"><header class="topbar"><span>TRAIN STRATEGIES. TEST TRANSFER.</span><span class="top-status"><span class="guest-dot"></span> YOUR SPACE TO REASON</span></header>
 <main id="main" tabindex="-1"><div v-if="guest.error" class="error" role="alert">{{guest.error}} <button @click="guest.init">Retry connection</button></div><RouterView v-if="guest.ready" :key="$route.path"/><p v-else-if="!guest.error" role="status">Opening your notebook…</p></main>
 <footer class="page-footer"><span>Human Fluid / an ongoing experiment</span><RouterLink to="/about">Practice with curiosity. Measure with care. ↗</RouterLink></footer>
 </div></div>
</template>
