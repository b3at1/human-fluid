<script setup lang="ts">
import {useTheme, type ThemePreference} from '../stores/theme'
const {preference, setPreference} = useTheme()
</script>

<template>
  <label class="theme-switch">
    <span>Appearance</span>
    <select aria-label="Appearance" :value="preference" @change="setPreference(($event.target as HTMLSelectElement).value as ThemePreference)">
      <option value="system">System</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  </label>
</template>
