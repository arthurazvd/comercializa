"""Cenários de aceitação: foto, galeria/câmera, limite, autenticação e ciclo de edição."""
from io import BytesIO
from PIL import Image
from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Product, ProductImage


class ProductImageTests(APITestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Boné', sku='ABC-321', sale_price='25.00', stock=7)
        self.url = f'/api/products/{self.product.pk}/image/'

    def jpeg(self):
        content = BytesIO()
        Image.new('RGB', (75, 75), '#20a878').save(content, 'JPEG', quality=65)
        return content.getvalue()

    def send_jpeg(self, data=None, filename='foto.jpg'):
        payload = self.jpeg() if data is None else data
        return self.client.put(self.url, {'image': SimpleUploadedFile(filename, payload, content_type='image/jpeg')}, format='multipart')

    def test_upload_then_read_persists_bytes_and_updates_catalog(self):
        data = self.jpeg()
        response = self.send_jpeg(data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['filename'], 'ABC-321.jpg')
        self.assertEqual(response.data['size'], len(data))
        self.assertEqual(bytes(ProductImage.objects.get(product=self.product).data), data)
        catalog = self.client.get('/api/products/').data
        item = next(row for row in catalog if row['id'] == self.product.pk)
        self.assertTrue(item['has_image'])
        self.assertIsNotNone(item['image_updated_at'])
        self.assertNotIn('data', item)
        self.assertNotIn('image', item)
        photo = self.client.get(self.url)
        self.assertEqual(photo.status_code, 200)
        self.assertEqual(photo['Content-Type'], 'image/jpeg')
        self.assertEqual(photo.content, data)
        self.assertIn('private', photo['Cache-Control'])

    def test_replacement_updates_one_row_without_changing_stock(self):
        self.assertEqual(self.send_jpeg().status_code, 200)
        self.assertEqual(self.send_jpeg().status_code, 200)
        self.assertEqual(ProductImage.objects.filter(product=self.product).count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_remove_photo_and_remove_again_is_safe(self):
        self.assertEqual(self.send_jpeg().status_code, 200)
        for _ in range(2):
            response = self.client.delete(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.data['has_image'])
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.product.refresh_from_db()
        self.assertIsNone(self.product.image_updated_at)

    def test_upload_requires_valid_image_and_100kb_limit(self):
        for content in [b'not-a-jpeg', b'\xff\xd8\xffgarbage', b'\xff\xd8\xff' + b'0' * 102400]:
            self.assertEqual(self.send_jpeg(content).status_code, 400)
        self.assertFalse(ProductImage.objects.filter(product=self.product).exists())

    def test_upload_rejects_unsupported_dimensions(self):
        content = BytesIO()
        Image.new('RGB', (4097, 1), 'white').save(content, 'JPEG')
        self.assertEqual(self.send_jpeg(content.getvalue()).status_code, 400)

    def test_changing_sku_renames_stored_file_without_losing_image(self):
        data = self.jpeg()
        self.assertEqual(self.send_jpeg(data).status_code, 200)
        response = self.client.patch(f'/api/products/{self.product.pk}/', {'sku': 'NOVO-777'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductImage.objects.get(product=self.product).filename, 'NOVO-777.jpg')
        self.assertEqual(self.client.get(self.url).content, data)

    def test_product_without_sku_uses_numeric_id_in_filename(self):
        self.product.sku = None
        self.product.save(update_fields=['sku'])
        self.assertEqual(self.send_jpeg().data['filename'], f'{self.product.pk}.jpg')

    def test_missing_upload_is_rejected(self):
        self.assertEqual(self.client.put(self.url, {}, format='multipart').status_code, 400)

    @override_settings(REQUIRE_AUTH=True)
    def test_private_images_cannot_be_read_or_changed_anonymously(self):
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
        self.assertIn(self.send_jpeg().status_code, (401, 403))
        self.assertIn(self.client.delete(self.url).status_code, (401, 403))
        user = get_user_model().objects.create_user(username='foto', password='senha-forte-123')
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(self.send_jpeg().status_code, 200)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_deleting_product_removes_image_row(self):
        self.send_jpeg()
        self.assertEqual(self.client.delete(f'/api/products/{self.product.pk}/').status_code, 204)
        self.assertFalse(ProductImage.objects.exists())
