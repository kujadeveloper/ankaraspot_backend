from django.db import models


# Create your models here.
class Status(models.IntegerChoices):
    PROGRESS = 0, 'Progress'
    COMPLETE = 1, 'Complete'

class TasksModel(models.Model):
    class Meta:
        ordering = ['-id']
        db_table = 'tasks'
        verbose_name_plural = 'Tasks'

    name = models.CharField(max_length=255, blank=True, null=True)
    page = models.IntegerField(default=0)
    status = models.IntegerField(default=Status.PROGRESS)
    total_page = models.IntegerField(default=0)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
