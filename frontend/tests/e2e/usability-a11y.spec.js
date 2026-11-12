import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const ROUTES = ['/', '/produtos', '/estoque', '/vendas', '/financeiro', '/sad'];

test.describe('P3 - Usabilidade e Acessibilidade (WCAG 2.1 AA + Heurísticas)', () => {
  for (const route of ROUTES) {
    test(`Auditoria WCAG e Usabilidade na rota ${route}`, async ({ page }) => {
      const startTime = Date.now();
      await page.goto(route, { waitUntil: 'networkidle' });
      const loadTime = Date.now() - startTime;

      // Heurística de Usabilidade 1: Tempo de resposta perceptível (< 3s)
      expect(loadTime).toBeLessThan(3000);

      // Heurística de Usabilidade 2: Zero scroll horizontal indesejado (responsividade)
      const hasHorizontalOverflow = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalOverflow).toBeFalsy();

      // Acessibilidade: Análise automatizada axe-core (WCAG 2.1 A/AA)
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      // Filtra apenas violações críticas ou sérias para gate de qualidade
      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);
    });
  }

  test('Usabilidade: Navegação por teclado (Tab) e alternância de Tema Claro/Escuro', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('Tab');
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(['A', 'BUTTON', 'INPUT']).toContain(focusedTag);

    // Testa alternância de tema e contraste
    const themeToggle = page.getByRole('button', { name: /tema|escuro|claro|dark|light/i });
    if (await themeToggle.isVisible()) {
      await themeToggle.click();
      const darkScan = await new AxeBuilder({ page }).withTags(['wcag2aa']).analyze();
      const contrastErrors = darkScan.violations.filter((v) => v.id === 'color-contrast');
      expect(contrastErrors).toEqual([]);
    }
  });
});