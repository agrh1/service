from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from api.models import Ticket


class AuthenticatedApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='apiuser', password='pass123', is_staff=True)
        self.client.force_authenticate(self.user)

    def test_create_ticket(self):
        url = reverse('ticket-list')
        response = self.client.post(url, {'ticket_id': 999, 'status': 'open'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_health_public(self):
        self.client.logout()
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')

    def test_jwt_token_pair(self):
        response = self.client.post('/api/token/', {'username': 'apiuser', 'password': 'pass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
