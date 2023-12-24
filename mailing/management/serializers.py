from rest_framework import serializers

from management.models import Client, Mailing, Message

class ClientAPISerializer(serializers.ModelSerializer):
    """ Client serializer """
    operator_code = serializers.CharField(read_only=True)

    class Meta:
        model = Client
        fields = ('__all__')


class MessageAPISerializer(serializers.ModelSerializer):
    """ Message serializer """
    class Meta:
        model = Message
        fields = ('__all__')


class MailingAPISerializer(serializers.ModelSerializer):
    """ Mailing serializer """
    all_messages = serializers.IntegerField(read_only=True)
    wait_messages = serializers.IntegerField(read_only=True)
    sent_messages = serializers.IntegerField(read_only=True)
    lost_messages = serializers.IntegerField(read_only=True)
    error_messages = serializers.IntegerField(read_only=True)

    class Meta:
        model = Mailing
        fields = ('id', 'date_time_start_sending', 'text', 'filter_operator_code', 'filter_tag', 'date_time_end_sending',
                  'active', 'all_messages', 'wait_messages', 'sent_messages', 'lost_messages', 'error_messages')
