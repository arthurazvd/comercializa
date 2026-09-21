"""Operações de produtos isoladas para facilitar testes unitários."""

from .models import Product


def listar_produtos():
    return Product.objects.all()


def criar_produto(**dados):
    return Product.objects.create(**dados)


def atualizar_produto(produto, **dados):
    for campo, valor in dados.items():
        setattr(produto, campo, valor)
    produto.save()
    return produto


def excluir_produto(produto):
    produto.delete()

