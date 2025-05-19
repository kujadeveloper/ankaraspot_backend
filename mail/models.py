from django.db import models
from users.models import User


# Create your models here.
class MailModel(models.Model):
    class Meta:
        verbose_name_plural = "Mail Listesi"  # Plural name
        ordering = ['id']
        db_table = 'mail'

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='users_mail')
    mail_type = models.IntegerField(default=0)  #0 email confiration key - 1 welcome mail
    to = models.CharField(max_length=500)
    subject = models.CharField(max_length=500)
    content = models.CharField(max_length=5000)
    status = models.IntegerField(default=0)  #0 waiting - 1 sending - 2 error
    status_message = models.CharField(max_length=500, blank=True, null=True)
    try_count = models.IntegerField(default=0)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
