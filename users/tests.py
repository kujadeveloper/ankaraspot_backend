import json
from django.test import TestCase
from django.urls import reverse

class UserTestCase(TestCase):

    def test_user_api(self):
        print("*****Users TEST*****")
        response = self.client.get(reverse('users'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        response = self.client.get(reverse('users')+'?id=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        response = self.client.get(reverse('users')+'?page_size=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        response = self.client.get(reverse('users')+'?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        response = self.client.get(reverse('users')+'?page=1&page_size=10')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

        data = {
		  "email": "string@string.com",
		  "username": "string",
		  "first_name": "string",
		  "last_name": "string",
		  "phone": "string",
		  "password": "string",
		  "repassword": "string"
		}
        response = self.client.post(reverse('users'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        data = {
        	'id':1
        }
        response = self.client.delete(reverse('users'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 204)
        print("*****Users COMPLENT*****")
        
