import json
from django.test import TestCase
from django.urls import reverse
from sitesettings.models import SitesettingsModels

class AttachmentTestCase(TestCase):

	def test_atachment_api(self):
		print("*****Attachment TEST*****")
		response = self.client.get(reverse('attachement'))
		self.assertEqual(response.status_code, 200)

