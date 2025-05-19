import json
from django.test import TestCase
from django.urls import reverse
from sitesettings.models import SitesettingsModels

class SitesettingsTestCase(TestCase):

    def test_sitesettings_api(self):
        print("*****Sitesettings TEST*****")
        SitesettingsModels.objects.create(aws_access_key='bQsUnx0wus7LCgSr', aws_secret='ykeceGcCBhRkTACo42dimk423lM7q8Hs', aws_url='https://image.kintshop.com')
        self.assertTrue(SitesettingsModels.objects.exists())
        