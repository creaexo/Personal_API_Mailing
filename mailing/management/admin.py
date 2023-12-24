from django.contrib import admin
from .models import *


class ClientAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone_number', 'operator_code', 'tag',  'time_zone']
    readonly_fields = ('operator_code',)

    def render_change_form(self, request, context, *args, **kwargs):
        form_instance = context['adminform'].form
        form_instance.fields['phone_number'].widget.attrs['placeholder'] = '79XXXXXXXXX'
        form_instance.fields['tag'].widget.attrs['placeholder'] = 'tag...'
        return super().render_change_form(request, context, *args, **kwargs)


class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'date_time_of_dispatch_formatter', 'status', 'mailing',  'client_id']

    def client_id(self, obj):
        return obj.client.id
    client_id.short_description = 'id клиента'

    def date_time_of_dispatch_formatter(self, obj):
        return str(obj.date_time_of_dispatch)[:-6]
    date_time_of_dispatch_formatter.short_description = 'Дата и время отправки'


class MailingAdmin(admin.ModelAdmin):
    date_time_start_sending = 1
    list_display = ['id', 'text_formatter', 'all_messages', 'date_time_start_sending_formatter',  'date_time_end_sending_formatter',
                    'active_formatter',]
    exclude = ('task_id', 'stopped')
    readonly_fields = ('all_messages', 'wait_messages', 'sent_messages', 'lost_messages',
                       'error_messages',)

    def active_formatter(self, obj):
        """ Changes the output of the field in the admin panel """
        if obj.active:
            return 'Запущена'
        return 'Остановлена'

    def text_formatter(self, obj):
        """ Changes the output of the field in the admin panel """
        return obj.text[:30]

    def date_time_start_sending_formatter(self, obj):
        """ Changes the output of the field in the admin panel """
        return str(obj.date_time_start_sending)[:-6]

    def date_time_end_sending_formatter(self, obj):
        """ Changes the output of the field in the admin panel """
        return str(obj.date_time_end_sending)[:-6]

    def all_messages(self, obj):
        """ Changes the output of the field in the admin panel """
        return obj.all_messages()
    all_messages.short_description = 'Все сообщения'

    def wait_messages(self, obj):
        """ Changes the output of the field in the admin panel """
        return obj.wait_messages()
    wait_messages.short_description = 'Ожидающе отправки сообщения'

    def sent_messages(self, obj):
        """ Changes the output of the field in the admin panel """
        return obj.sent_messages()
    sent_messages.short_description = 'Успешно отправленные сообщения'

    def lost_messages(self, obj):
        """ Changes the output of the field in the admin panel """
        return obj.lost_messages()
    lost_messages.short_description = 'Опаздавшие сообщения'

    def error_messages(self, obj):
        """ Changes the output of the field in the admin panel """
        return obj.error_messages()
    error_messages.short_description = 'Не принятые сообщения'

    def render_change_form(self, request, context, *args, **kwargs):
        """ Changes the output of the field in the admin panel """
        form_instance = context['adminform'].form
        # print(form_instance)
        form_instance.fields['filter_operator_code'].widget.attrs['placeholder'] = '900;901;902...'
        form_instance.fields['filter_tag'].widget.attrs['placeholder'] = 'tag1;tag2;tag3...'
        return super().render_change_form(request, context, *args, **kwargs)


admin.site.register(Mailing, MailingAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Message, MessageAdmin)