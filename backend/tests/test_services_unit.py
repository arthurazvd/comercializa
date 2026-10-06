from decimal import Decimal
from unittest.mock import patch

from core.services import (
    calculate_restock_quantity,
    calculate_revenue,
    dashboard_data,
)


class TesteCalculoFaturamento:
    """Testes unitários da regra de cálculo do faturamento."""

    def teste_receita_sem_desconto(self):
        resultado = calculate_revenue(
            Decimal("100.00"),
            Decimal("0.00"),
        )

        assert resultado == Decimal("100.00")

    def teste_receita_com_desconto(self):
        resultado = calculate_revenue(
            Decimal("100.00"),
            Decimal("25.00"),
        )

        assert resultado == Decimal("75.00")

    def teste_receita_nao_pode_ser_negativa(self):
        resultado = calculate_revenue(
            Decimal("50.00"),
            Decimal("100.00"),
        )

        assert resultado == Decimal("0")


class TesteCalculoReposicao:
    """Testes unitários da regra de sugestão de reposição."""

    def teste_reposicao_considera_estoque_minimo(self):
        resultado = calculate_restock_quantity(
            stock=5,
            minimum_stock=10,
            velocity=0,
        )

        assert resultado == 15

    def teste_reposicao_considera_velocidade_de_vendas(self):
        resultado = calculate_restock_quantity(
            stock=5,
            minimum_stock=10,
            velocity=2,
        )

        assert resultado == 25

    def teste_reposicao_sugere_pelo_menos_uma_unidade(self):
        resultado = calculate_restock_quantity(
            stock=20,
            minimum_stock=10,
            velocity=0,
        )

        assert resultado == 1


class TesteDashboardComMock:
    """Testa o isolamento de uma regra do serviço usando Mock Object."""

    @patch("core.services.calculate_revenue")
    def teste_dashboard_utiliza_regra_de_calculo_de_receita(
        self,
        mock_calculate_revenue,
        db,
    ):
        mock_calculate_revenue.return_value = Decimal("123.45")

        resultado = dashboard_data()

        mock_calculate_revenue.assert_called_once_with(
            Decimal("0"),
            Decimal("0"),
        )
        assert resultado["summary"]["revenue"] == Decimal("123.45")
