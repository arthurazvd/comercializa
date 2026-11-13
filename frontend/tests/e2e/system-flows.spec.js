import { test, expect } from '@playwright/test';

test.describe('P3 - Testes de Sistema (Fluxos Críticos End-to-End)', () => {
  test('Fluxo completo: Cadastro de Produto -> Entrada de Lote -> Venda PDV -> Atualização SAD', async ({ page }) => {
    await page.goto('/');

    // 1. Autenticação (caso o ambiente exija login)
    const loginInput = page.locator('input[name="username"]');
    if (await loginInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await loginInput.fill('admin');
      await page.locator('input[name="password"]').fill('admin123');
      await page.getByRole('button', { name: /entrar no sistema/i }).click();
    }

    // Aguarda o menu lateral carregar
    const nav = page.getByRole('navigation', { name: 'Navegação principal' });
    await expect(nav).toBeVisible({ timeout: 15000 });

    const prodName = `Produto E2E ${Date.now()}`;
    const prodSku = `SKU-${Date.now()}`;

    // 2. Navegar para Produtos e cadastrar novo item
    await nav.getByRole('button', { name: /produtos/i }).click();

    await page.getByLabel('Nome do produto').fill(prodName);
    await page.getByLabel('SKU').fill(prodSku);
    await page.getByRole('spinbutton', { name: 'preço de compra' }).fill('10');
    await page.getByRole('spinbutton', { name: 'preço de venda' }).fill('25');
    await page.getByRole('spinbutton', { name: 'saldo de estoque' }).fill('0');
    await page.getByRole('spinbutton', { name: 'estoque mínimo' }).fill('2');

    await page.getByRole('button', { name: /cadastrar produto/i }).click();
    await expect(page.getByText(/produto cadastrado com sucesso/i)).toBeVisible();
    await expect(page.getByText(prodName)).toBeVisible();

    // 3. Navegar para Movimentações e registrar entrada de lote (+10 unidades)
    await nav.getByRole('button', { name: /movimentações/i }).click();

    await page.getByLabel('Produto', { exact: true }).selectOption({ label: `${prodName} · 0 un.` });
    await page.getByRole('spinbutton', { name: 'ajuste de estoque' }).fill('10');
    await page.getByRole('spinbutton', { name: 'custo unitário do novo lote' }).fill('10');

    await page.getByRole('button', { name: /registrar movimentação/i }).click();
    await expect(page.getByText(/movimentação registrada com sucesso/i)).toBeVisible();

    // 4. Realizar Venda no PDV (2 unidades x R$ 25,00 = R$ 50,00)
    await nav.getByRole('button', { name: /vendas/i }).click();

    const searchInput = page.locator('#sale-search');
    await searchInput.fill(prodName);
    await page.getByRole('option', { name: new RegExp(prodName) }).click();

    await page.getByRole('spinbutton', { name: 'quantidade do produto' }).fill('2');
    await page.getByRole('button', { name: /incluir/i }).click();

    await page.getByRole('button', { name: /finalizar venda/i }).click();
    await expect(page.getByText(/venda registrada/i)).toBeVisible();

    // 5. Validar baixa de estoque (10 - 2 = 8 unidades) em Ver estoque
    await nav.getByRole('button', { name: /ver estoque/i }).click();
    const row = page.locator('tr', { hasText: prodName });
    await expect(row).toContainText('8');

    // 6. Verificar impacto financeiro e estoque no Dashboard / SAD
    await nav.getByRole('button', { name: /visão geral/i }).click();
    await expect(page.getByRole('heading', { name: /visão geral/i })).toBeVisible();
    await expect(page.locator('main')).toContainText(/receita|vendas/i);
    await expect(page.getByText(/50,00/).first()).toBeVisible();
  });
});