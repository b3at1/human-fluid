import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import {readFileSync} from 'node:fs'
import {runInNewContext} from 'node:vm'
import {resolve} from 'node:path'
import {createThemeController, THEME_KEY} from '../src/stores/theme'

let media: MediaQueryList
const controllers: ReturnType<typeof createThemeController>[] = []
function create() {
  const controller = createThemeController()
  controllers.push(controller)
  return controller
}
function systemDark(matches: boolean) {
  Object.defineProperty(media, 'matches', {value: matches, configurable: true})
  media.dispatchEvent(Object.assign(new Event('change'), {matches}))
}
beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
  document.head.innerHTML = '<meta name="theme-color" content="#fffef7">'
  media = Object.assign(new EventTarget(), {matches: false, media: '(prefers-color-scheme: dark)'}) as MediaQueryList
  vi.stubGlobal('matchMedia', vi.fn(() => media))
})
afterEach(() => {
  controllers.splice(0).forEach(controller => controller.dispose())
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('appearance preference', () => {
  it('follows system changes while System is selected', () => {
    const controller = create()
    expect(controller.preference.value).toBe('system')
    expect(document.documentElement.dataset.theme).toBe('light')
    systemDark(true)
    expect(controller.resolved.value).toBe('dark')
    expect(document.documentElement.style.colorScheme).toBe('dark')
    expect(document.querySelector('meta[name="theme-color"]')?.getAttribute('content')).toBe('#171914')
  })
  it('persists an explicit choice and ignores system changes until System is restored', () => {
    const controller = create()
    controller.setPreference('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    controller.setPreference('light')
    systemDark(true)
    expect(controller.resolved.value).toBe('light')
    expect(create().preference.value).toBe('light')
    controller.setPreference('system')
    expect(controller.resolved.value).toBe('dark')
  })
  it('synchronizes another tab’s changed preference', () => {
    const controller = create()
    localStorage.setItem(THEME_KEY, 'dark')
    window.dispatchEvent(new StorageEvent('storage', {key: THEME_KEY, newValue: 'dark'}))
    expect(controller.preference.value).toBe('dark')
    expect(controller.resolved.value).toBe('dark')
    localStorage.clear()
    window.dispatchEvent(new StorageEvent('storage', {key: null}))
    expect(controller.preference.value).toBe('system')
  })
  it('works in memory when browser storage is unavailable', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('Storage blocked') })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('Storage blocked') })
    const controller = create()
    expect(() => controller.setPreference('dark')).not.toThrow()
    expect(document.documentElement.dataset.theme).toBe('dark')
  })
})

describe('pre-paint bootstrap', () => {
  const script = readFileSync(resolve(process.cwd(), 'public/assets/theme-init.js'), 'utf8')
  it('applies the saved dark preference before Vue starts', () => {
    localStorage.setItem(THEME_KEY, 'dark')
    runInNewContext(script, {localStorage, window, document})
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(document.documentElement.style.colorScheme).toBe('dark')
  })
  it('uses system preference when storage is blocked or invalid', () => {
    systemDark(true)
    runInNewContext(script, {localStorage: {getItem() {throw new Error('Blocked')}}, window, document})
    expect(document.documentElement.dataset.theme).toBe('dark')
    localStorage.setItem(THEME_KEY, 'invalid')
    runInNewContext(script, {localStorage, window, document})
    expect(document.documentElement.dataset.theme).toBe('dark')
  })
})
