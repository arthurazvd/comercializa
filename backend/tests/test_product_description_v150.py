"""V1.5.0: descrição de produto é opcional e não altera preços ou estoque."""
import pytest
from rest_framework.test import APIClient
from core.models import Product


@pytest.mark.django_db
def test_description_can_be_created_and_updated_without_changing_stock():
    client = APIClient()
    create = client.post('/api/products/', {
        'name': 'Estojo organizador', 'description': 'Plástico reforçado; cor azul.',
        'sale_price': '19.90', 'purchase_price': '10.00', 'stock': 6,
    }, format='json')
    assert create.status_code == 201, create.data
    product_id = create.data['id']
    assert create.data['description'] == 'Plástico reforçado; cor azul.'
    update = client.patch(f'/api/products/{product_id}/', {
        'description': 'Com tampa e fechamento rápido.',
    }, format='json')
    assert update.status_code == 200, update.data
    product = Product.objects.get(pk=product_id)
    assert product.description == 'Com tampa e fechamento rápido.'
    assert product.stock == 6
    assert str(product.sale_price) == '19.90'
    assert client.get(f'/api/products/{product_id}/').data['description'] == product.description


@pytest.mark.django_db
def test_description_is_optional_and_limited():
    client = APIClient()
    result = client.post('/api/products/', {'name': 'Boné', 'sale_price': '25.00'}, format='json')
    assert result.status_code == 201, result.data
    assert result.data['description'] == ''
    too_long = client.patch(f"/api/products/{result.data['id']}/", {
        'description': 'a' * 2001,
    }, format='json')
    assert too_long.status_code == 400
    assert Product.objects.get(pk=result.data['id']).description == ''
