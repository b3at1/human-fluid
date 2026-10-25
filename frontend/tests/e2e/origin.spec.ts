import {test, expect} from '@playwright/test'

for (const origin of ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:8000', 'http://127.0.0.1:8000']) {
  test(`guest bootstrap works at ${origin}`, async ({page}) => {
    const bootstrap = page.waitForResponse(response => response.url().endsWith('/api/v1/guest') && response.request().method() === 'POST')
    await page.goto(origin)
    expect((await bootstrap).status()).toBe(200)
    await expect(page.getByRole('heading', {name: /A little practice/})).toBeVisible()
    await expect(page.getByRole('alert')).toHaveCount(0)
    // An authenticated, CSRF-protected mutation also works on this origin.
    const status = await page.evaluate(async () => {
      const me = await (await fetch('/api/v1/me')).json()
      const response = await fetch('/api/v1/export', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRF-Token': me.csrf_token},
        body: '{}',
      })
      return response.status
    })
    expect(status).toBe(200)
  })
}
