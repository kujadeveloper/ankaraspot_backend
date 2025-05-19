import json
import os

from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from celery import shared_task
import ssl
from django.core.mail import get_connection, EmailMultiAlternatives


@shared_task
def mail():
    from mail.models import MailModel

    all_mail = MailModel.objects.filter(is_deleted=False, status=0, try_count__lt=10)[0:10]

    for mail in all_mail:
        try:
            if mail.mail_type == 0:
                render_html = render_to_string(os.path.join(settings.BASE_DIR, 'templates',
                                                            'confirm_mail.html'),
                                               json.loads(mail.content))
                sendmail = EmailMultiAlternatives(subject=mail.subject,
                                                  body=strip_tags(render_html),
                                                  from_email=f'FİYATOR - Hesap Aktivasyon <{settings.EMAIL_HOST_USER}>',
                                                  to=[mail.to])
                sendmail.attach_alternative(render_html, "text/html")
                sendmail.send()

            if mail.mail_type == 1:
                render_html = render_to_string(os.path.join(settings.BASE_DIR, 'templates',
                                                            'reset_password.html'),
                                               json.loads(mail.content))
                sendmail = EmailMultiAlternatives(subject=mail.subject,
                                                  body=strip_tags(render_html),
                                                  from_email=f'FİYATOR - Şifremi Unuttum <{settings.EMAIL_HOST_USER}>',
                                                  to=[mail.to])
                sendmail.attach_alternative(render_html, "text/html")
                sendmail.send()

            if mail.mail_type == 2:
                render_html = render_to_string(os.path.join(settings.BASE_DIR, 'templates',
                                                            'confirm_shop_product.html'),
                                               json.loads(mail.content))
                sendmail = EmailMultiAlternatives(subject=mail.subject,
                                                  body=strip_tags(render_html),
                                                  from_email=f'FİYATOR - Ürünleriniz Yayına Alındı <{settings.EMAIL_HOST_USER}>',
                                                  to=[mail.to])
                sendmail.attach_alternative(render_html, "text/html")
                sendmail.send()

            if mail.mail_type == 3:
                render_html = render_to_string(os.path.join(settings.BASE_DIR, 'templates', 'price_increase_notification.html'), json.loads(mail.content))
                sendmail = EmailMultiAlternatives(subject=mail.subject,
                                                  body=strip_tags(render_html),
                                                  from_email=f'FİYATOR - Fiyat Artışı <{settings.EMAIL_HOST_USER}>',
                                                  to=[mail.to])
                sendmail.attach_alternative(render_html, "text/html")
                sendmail.send()

            if mail.mail_type == 4:
                render_html = render_to_string(os.path.join(settings.BASE_DIR, 'templates', 'price_decrease_notification.html'), json.loads(mail.content))
                sendmail = EmailMultiAlternatives(subject=mail.subject,
                                                  body=strip_tags(render_html),
                                                  from_email=f'FİYATOR - Fiyat Düşüşü <{settings.EMAIL_HOST_USER}>',
                                                  to=[mail.to])
                sendmail.attach_alternative(render_html, "text/html")
                sendmail.send()

            mail.status = 1
            mail.save()
        except Exception as e:
            print(e)
            mail.try_count = mail.try_count + 1
            mail.status_message = e
            mail.save()
