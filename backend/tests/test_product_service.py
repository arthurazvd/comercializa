"""Testes unitários do CRUD de produtos usando objetos mock."""

from unittest.mock import Mock, patch

from core.product_service import (
    atualizar_produto,
    criar_produto,
    excluir_produto,
    listar_produtos,
)


@patch("core.product_service.Product.objects")
def teste_unitario_listar_produtos(mock_objects):
    produtos_esperados = [Mock(name="produto_1"), Mock(name="produto_2")]
    mock_objects.all.return_value = produtos_esperados

    resultado = listar_produtos()

    mock_objects.all.assert_called_once_with()
    assert resultado == produtos_esperados


@patch("core.product_service.Product.objects")
def teste_unitario_criar_produto(mock_objects):
    produto_criado = Mock(name="produto_criado")
    mock_objects.create.return_value = produto_criado
    dados = {"name": "Arroz", "stock": 10}

    resultado = criar_produto(**dados)

    mock_objects.create.assert_called_once_with(**dados)
    assert resultado is produto_criado


def teste_unitario_atualizar_produto():
    produto = Mock(name="produto", name_original="Arroz", stock=10)

    resultado = atualizar_produto(produto, name="Arroz Integral", stock=20)

    assert produto.name == "Arroz Integral"
    assert produto.stock == 20
    produto.save.assert_called_once_with()
    assert resultado is produto


def teste_unitario_excluir_produto():
    produto = Mock(name="produto")

    excluir_produto(produto)

    produto.delete.assert_called_once_with()

