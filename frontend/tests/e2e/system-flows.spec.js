import { test, expect } from '@playwright/test';

test.describe('P3 - Testes de Sistema (Fluxos Críticos End-to-End)', () => {
  test('Fluxo completo: Cadastro de Produto -> Entrada de Lote -> Venda PDV -> Atualização SAD', async ({ page }) => {
    await page.goto('/');

    // 1. Autenticação (ajuste conforme credenciais de seed/admin do seu ambiente)
    const loginInput = page.locator('input[type="text"], input[name="username"]').first();
    if (await loginInput.isVisible()) {
      await loginInput.fill('admin');
      await page.locator('input[type="password"]').fill('admin123');
      await page.getByRole('button', { name: /entrar|login/i }).click();
    }

    // 2. Navegar para Catálogo/Produtos e criar item de teste E2E
    await page.getByRole('link', { name: /produtos|catálogo/i }).click();
    await page.getByRole('button', { name: /novo produto|adicionar/i }).click();

    const prodName = `Produto E2E ${Date.now()}`;
    await page.getByLabel(/nome/i).fill(prodName);
    await page.getByLabel(/preço de venda|preço/i).fill('25.00');
    await page.getByRole('button', { name: /salvar/i }).click();

    await expect(page.getByText(prodName)).toBeVisible();

    // 3. Registrar Entrada de Estoque (Lote FEFO)
    await page.getByRole('link', { name: /estoque|lotes/i }).click();
    await page.getByRole('button', { name: /nova entrada|adicionar lote/i }).click();
    await page.getByLabel(/produto/i).selectOption({ label: prodName });
    await page.getByLabel(/quantidade/i).fill('10');
    await page.getByLabel(/custo/i).fill('12.00');
    await page.getByRole('button', { name: /confirmar|salvar/i }).click();

    // 4. Realizar Venda no PDV
    await page.getByRole('link', { name: /pdv|vendas/i }).click();
    await page.getByPlaceholder(/buscar produto/i).fill(prodName);
    await page.getByText(prodName).first().click();
    await page.getByRole('button', { name: /finalizar venda/i }).click();

    await expect(page.getByText(/venda realizada|sucesso/i)).toBeVisible();

    // 5. Verificar impacto financeiro e estoque no Dashboard / SAD
    await page.getByRole('link', { name: /dashboard|início|sad/i }).click();
    await expect(page.locator('main')).toContainText(/faturamento|lucro|vendas/i);
  });
});