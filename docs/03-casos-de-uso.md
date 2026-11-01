# Casos de Uso

## UC01 — Cadastrar produto

**Ator:** Comerciante  
**Pré-condição:** sistema disponível.  
**Fluxo principal:**
1. Usuário acessa Produtos.
2. Informa dados do produto.
3. Informa estoque e estoque mínimo.
4. Opcionalmente informa validade.
5. Confirma.
6. Sistema valida e salva.

## UC02 — Registrar venda

**Ator:** Comerciante  
**Pré-condição:** produto ativo e com estoque.  
**Fluxo principal:**
1. Usuário acessa Registrar venda.
2. Seleciona produto e quantidade.
3. Informa desconto, se houver.
4. Confirma a venda.
5. Sistema valida estoque.
6. Sistema registra venda.
7. Sistema reduz estoque.
8. Venda passa a alimentar as análises.

**Fluxo alternativo:** se a quantidade for superior ao estoque, a venda é recusada.

## UC03 — Consultar visão gerencial

**Ator:** Comerciante  
**Fluxo principal:**
1. Usuário abre o dashboard.
2. Sistema analisa dados recentes.
3. Sistema apresenta faturamento, vendas e alertas.
4. Sistema apresenta ranking.
5. Sistema apresenta recomendações priorizadas.

## UC04 — Avaliar reposição

1. SAD identifica estoque crítico.
2. SAD consulta movimentação recente.
3. SAD calcula sugestão inicial de reposição.
4. SAD atribui prioridade.
5. Usuário avalia a recomendação e decide se realizará a compra.

## UC05 — Avaliar produto próximo do vencimento

1. SAD encontra produto dentro da janela de validade.
2. SAD verifica estoque e movimentação.
3. SAD gera alerta.
4. SAD sugere avaliação de promoção/desconto.
5. Comerciante decide a ação.

## Casos de uso operacionais acrescentados — V1.2.0

### UC10 — Cadastrar produto com foto

**Ator:** operador autenticado. **Pré:** permissão de cadastro.

1. Operador abre Produtos, informa nome, preços, saldo, categoria e SKU (opcional).
2. Clica em **Escolher da galeria** ou **Tirar foto**; navegador solicita arquivo ou câmera, conforme disponibilidade do dispositivo.
3. A aplicação converte e enquadra a foto localmente como JPEG de até 100 KB, sem mudar a proporção.
4. Operador visualiza prévia e salva produto. O sistema registra os dados e depois envia a fotografia ao endpoint do produto criado.
5. No catálogo, o produto aparece com miniatura; a lista contém apenas metadados, não bytes de imagem.

**Alternativas:** se não for possível reduzir a imagem, informa-se o motivo sem enviar o arquivo. Se o cadastro concluir mas o upload falhar, o produto permanece salvo e a tela mantém seu ID para reenvio, evitando duplicação. SKU ausente gera nome de foto com ID.

### UC11 — Editar, substituir ou remover foto

**Ator:** operador. **Pré:** produto existente.

1. Seleciona **Editar** no catálogo.
2. Visualiza a imagem atual (quando houver), escolhe outra ou aciona **Remover foto**.
3. Salva as alterações; o sistema substitui ou apaga a imagem, sem mexer no estoque.
4. A nova miniatura é atualizada pela data `image_updated_at`.

**Alternativas:** sem foto, exibir ícone padrão; se imagem nova estiver inválida, não substitui a anterior.

### UC12 — Adicionar item repetido ao PDV

**Ator:** operador. Ao selecionar produto já presente no carrinho e tocar em Incluir, o sistema soma as quantidades na mesma linha; se o limite de estoque for excedido, bloqueia e informa a razão.

### UC13 — Estornar venda integralmente

**Ator:** operador autenticado. Abre histórico, seleciona venda válida, informa justificativa, confirma. O sistema marca a venda estornada, recompõe estoque/lotes e atualiza indicadores. **Não realiza reembolso bancário**; dinheiro é devolvido externamente.

### UC14 — Receber notificações transitórias

Após gravação ou validação, a mensagem e a barra de progresso aparecem por até 1,5 s, desaparecendo automaticamente quando a barra termina; o usuário também pode dispensá-la pelo botão. Um alerta novo substitui o antigo com novo prazo.
