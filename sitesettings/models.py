from django.db import models
from users.models import User

# Create your models here.
class SitesettingsModels(models.Model):
	class Meta:
		verbose_name_plural = "Site Ayarları"
		ordering = ['id']
		db_table = 'sitesettings'

	cdn_systems = models.IntegerField(default=0) #aws 0 - 1 google cloud
	mail_systems = models.IntegerField(default=0) #default mail 0 - 1 yagmail
	
	aws_access_key = models.CharField(max_length=255)
	aws_secret = models.CharField(max_length=255)
	aws_url = models.CharField(max_length=255)
	bucket = models.CharField(max_length=100)
		
	is_deleted = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def delete(self, *args, **kwargs):
		self.is_deleted = True
		self.save()

	def undelete(self, *args, **kwargs):
		self.is_deleted = False
		self.save()