from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.profile_url = reverse('auth_profile')

        self.user_data = {
            'username': 'testcustomer',
            'email': 'customer@test.com',
            'password': 'testpassword123',
            'role': 'customer'
        }

    def test_user_registration(self):
        """Test registering a new customer account."""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'testcustomer')
        self.assertEqual(response.data['role'], 'customer')
        self.assertNotIn('password', response.data)

        # Check in DB
        self.assertTrue(User.objects.filter(username='testcustomer').exists())

    def test_user_login(self):
        """Test obtaining JWT tokens on login."""
        # Create user first
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            role=self.user_data['role']
        )

        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'testcustomer')
        self.assertEqual(response.data['user']['role'], 'customer')

    def test_profile_access_unauthorized(self):
        """Test profile access without a token."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_access_authorized(self):
        """Test profile access with a valid token."""
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            role=self.user_data['role']
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testcustomer')
        self.assertEqual(response.data['email'], 'customer@test.com')
