import {computed, readonly, ref} from 'vue'

export type ThemePreference = 'system' | 'light' | 'dark'
export const THEME_KEY = 'hf-theme'

function readPreference(): ThemePreference {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch { /* Private or restricted storage still permits an in-memory theme. */ }
  return 'system'
}

export function createThemeController() {
  const preference = ref<ThemePreference>(readPreference())
  const media = window.matchMedia('(prefers-color-scheme: dark)')
  const systemDark = ref(media.matches)
  const resolved = computed<'light'|'dark'>(() => preference.value === 'system' ? (systemDark.value ? 'dark' : 'light') : preference.value)

  function apply() {
    document.documentElement.dataset.theme = resolved.value
    document.documentElement.style.colorScheme = resolved.value
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', resolved.value === 'dark' ? '#171914' : '#fffef7')
  }
  function setPreference(value: ThemePreference) {
    preference.value = value
    try { localStorage.setItem(THEME_KEY, value) } catch { /* Keep the current tab usable without storage. */ }
    apply()
  }
  function systemChanged(event: MediaQueryListEvent) {
    systemDark.value = event.matches
    apply()
  }
  function storageChanged(event: StorageEvent) {
    if (event.key !== THEME_KEY && event.key !== null) return
    preference.value = readPreference()
    apply()
  }
  media.addEventListener('change', systemChanged)
  window.addEventListener('storage', storageChanged)
  apply()
  return {
    preference: readonly(preference),
    resolved,
    setPreference,
    dispose() {
      media.removeEventListener('change', systemChanged)
      window.removeEventListener('storage', storageChanged)
    },
  }
}

let controller: ReturnType<typeof createThemeController> | undefined
export function useTheme() {
  return controller ??= createThemeController()
}
