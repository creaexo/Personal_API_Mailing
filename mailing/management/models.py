
from datetime import timedelta

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from celery_app import app

TIMEZONES = (
    (0, '(UTC)'),
    (1, '(UTC+1)'),
    (2, 'Калининградское (UTC+2)'),
    (3, 'Московское (UTC+3)'),
    (4, 'Самарское (UTC+4)'),
    (5, 'Екатеринбургское (UTC+5)'),
    (6, 'Омское (UTC+6)'),
    (7, 'Красноярское (UTC+7)'),
    (8, 'Иркутское (UTC+8)'),
    (9, 'Якутское (UTC+9)'),
    (10, 'Владивостокское (UTC+10)'),
    (11, 'Магаданское (UTC+11)'),
    (12, 'Камчатское (UTC+12)'),
    (13, '(UTC+13)'),
    (14, '(UTC+14)'),
    (15, '(UTC+15)'),
    (16, '(UTC+16)'),
    (17, '(UTC+17)'),
    (18, '(UTC+18)'),
    (19, '(UTC+19)'),
    (20, '(UTC+20)'),
    (21, '(UTC+21)'),
    (22, '(UTC+22)'),
    (23, '(UTC+23)')
)

MESSAGES_STATUSES = (
        (0, 'Ожидает отправки'),
        (1, 'Отправлено'),
        (2, 'Не отправлено. Дата и время клиента больше выбранного в рассылке'),
        (3, 'Не отправлено. Ошибка внешнего API')
        )


class Mailing(models.Model):
    """ Mailing model """
    date_time_start_sending = models.DateTimeField(verbose_name='Начало рассылки', default=timezone.now, blank=False)
    text = models.TextField(verbose_name='Текст сообщения', blank=False)
    filter_operator_code = models.CharField(verbose_name='Фильтр мобильных операторов', max_length=100, blank=True)
    filter_tag = models.CharField(verbose_name='Фильтр тегов', max_length=100, blank=True)
    date_time_end_sending = models.DateTimeField(verbose_name='Конец рассылки', default=timezone.now()+timedelta(days=1))
    active = models.BooleanField(verbose_name='Рассылать сообщения', default=True)
    task_id = models.CharField(blank=True, max_length=100)
    stopped = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'

    def __str__(self):
        return str(f'''id: {self.pk} text: {self.text[:10]}''')

    def all_messages(self):
        """ Get all messages """
        return Message.objects.filter(mailing_id=self.pk).count()

    def wait_messages(self):
        """ Get the number of messages waiting to be sent """
        return Message.objects.filter(mailing_id=self.pk, status=0).count()

    def sent_messages(self):
        """ Get the number of sent messages """
        return Message.objects.filter(mailing_id=self.pk, status=1).count()

    def lost_messages(self):
        """ Get the number of late messages """
        return Message.objects.filter(mailing_id=self.pk, status=2).count()

    def error_messages(self):
        """ Get the number of messages not received by the external server """
        return Message.objects.filter(mailing_id=self.pk, status=3).count()

    def save(self, *args, **kwargs):
        """ Logic after saving a model object """
        super().save(*args, **kwargs)
        if self.active:
            from management.services import start_mailing
            self.task_id = start_mailing.apply_async([self.pk, self.date_time_start_sending,
                                                       self.date_time_end_sending, self.text, self.filter_tag,
                                                       self.filter_operator_code, self.stopped],
                                                      eta=self.date_time_start_sending)
            try:
                super().save(*args, **kwargs)
            except Exception as e:
                print(e)
        else:
            if self.task_id is None:
                try:
                    super().save(*args, **kwargs)
                except Exception as e:
                    print(e)
            else:
                try:
                    app.control.revoke(self.task_id, terminate=True, signal='SIGKILL')
                except:
                    pass
                self.stopped = True
                try:
                    super().save(*args, **kwargs)
                except Exception as e:
                    print(e)


class Client(models.Model):
    """ Client model """
    phone_regex = RegexValidator(
        regex=r'^79[0-9]{9}$',
        message="Введите номер в формате: '79XXXXXXXXX'"
    )
    phone_number = models.CharField(verbose_name='Номер телефона', validators=[phone_regex], max_length=11)
    operator_code = models.CharField(verbose_name='Код оператора', max_length=3)
    tag = models.CharField(verbose_name='Тег', blank=True, max_length=100)
    time_zone = models.IntegerField(verbose_name='Время (Часовой пояс)', choices=TIMEZONES, default=0)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def save(self, *args, **kwargs):
        """ Logic after saving a model object """
        if not self.pk:  # only on creation
            self.operator_code = self.phone_number[1:4]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Клиент: {self.pk} {self.phone_number}"


# Сообщение
class Message(models.Model):
    """ Message model """
    date_time_of_dispatch = models.DateTimeField(verbose_name='Дата и время отправки', default=timezone.now)
    status = models.IntegerField(verbose_name='Статус', blank=True, choices=MESSAGES_STATUSES)
    mailing = models.ForeignKey(Mailing, verbose_name='Рассылка', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, verbose_name='Клиент', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return str(self.pk)
