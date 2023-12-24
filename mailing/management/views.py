from datetime import timedelta
import requests
from django.contrib.auth import logout
from django.shortcuts import render
from rest_framework import generics, viewsets, permissions
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsOwnerOrReadOnly, MessageIsOwnerOrReadOnly
from .models import *
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .serializers import ClientAPISerializer, MessageAPISerializer, MailingAPISerializer
from .services import send_message


def index(request, *args, **kwargs):
    """ Function rendering the main page """
    staff = False
    if request.user.is_staff:
        staff = True
    return render(request, 'index.html', {'staff': staff})


def add_users(request, *args, **kwargs):
    """ Function that adds users to test functionality. Works only under admin account """
    if request.user and request.user.is_staff:
        for tz in range(24):
            for i in range(10, 100):
                client = Client.objects.create(phone_number=f'79{i}00000{i}', tag=f'tag{i}', time_zone=tz)
                client.save()
        return HttpResponse('Все клиенты добавлены!')
    return HttpResponse('Нет доступа!')


def logout_user(request):
    """ Function that unlogs the user """
    logout(request)
    return redirect('/api/v1/auth-rest/login/?next=/auth/token/login/')


def del_users(request, *args, **kwargs):
    """ Function that deletes all users. Works only under admin account """
    if request.user and request.user.is_staff:
        Client.objects.all().delete()
        return HttpResponse('Все клиенты удалены!')
    return HttpResponse('Нет доступа!')


def add_mailings(request, *args, **kwargs):
    if request.user and request.user.is_staff:
        for i in range(100):
            mailing = Mailing.objects.create(text=str(i))
            mailing.save()
        return HttpResponse('Готово!')
    return HttpResponse('Нет доступа!')


class ClientViewSet(viewsets.ModelViewSet):
    """ Class serving api request to the "Client" model """
    queryset = Client.objects.all()
    serializer_class = ClientAPISerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.user_id:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No access'})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if request.user and request.user.is_staff:
            count = queryset.count()
            serializer = self.get_serializer(queryset, many=True)
            final_response = {'count': count, 'all_clients': serializer.data.copy()}
            return Response(final_response)
        elif str(request.user) != 'AnonymousUser':
            queryset = queryset.filter(user=request.user.id)
            count = queryset.count()
            serializer = self.get_serializer(queryset, many=True)
            final_response = {'count': count, 'all_clients': serializer.data.copy()}
            return Response(final_response)
        else:
            return Response({'error': 'No access'})


class MessageViewSet(viewsets.ModelViewSet):
    """ Message serving api request to the "Client" model """
    queryset = Message.objects.all().order_by('-id')
    serializer_class = MessageAPISerializer
    permission_classes = (MessageIsOwnerOrReadOnly,)

    def list(self, request, *args, **kwargs):
        if str(request.user) == 'AnonymousUser':
            return redirect('/api/v1/authlogin/?next=/api/v1/', permanent=False)
        queryset = self.filter_queryset(self.get_queryset())

        if request.user and not request.user.is_staff:
            mailings_user = Mailing.objects.filter(user=request.user.id)
            mailings_user = list(mailings_user)
            queryset = queryset.filter(mailing_id__in=mailings_user)
        if 'status' in request.GET and 'no_grouping' in request.GET:
            queryset = queryset.filter(status=request.GET['status'])
        if 'order' in request.GET:
            queryset = queryset.order_by(request.GET['order'])
        count = queryset.count()
        if 'no_grouping' in request.GET:
            serializer = self.get_serializer(queryset, many=True)
            final_response = {'count': count, 'all_messages': serializer.data.copy()}
            return Response(final_response)

        wait_send = self.get_serializer(queryset.filter(status=0), many=True)
        wait_send_count = queryset.filter(status=0).count()
        sent = self.get_serializer(queryset.filter(status=1), many=True)
        sent_count = queryset.filter(status=1).count()
        late = self.get_serializer(queryset.filter(status=2), many=True)
        late_count = queryset.filter(status=2).count()
        receiving_error = self.get_serializer(queryset.filter(status=3), many=True)
        receiving_error_count = queryset.filter(status=3).count()

        final_response = {'count': count, 'wait_send': {'count': wait_send_count, 'messages': wait_send.data.copy()},
                          'sent': {'count': sent_count, 'messages': sent.data.copy()},
                          'late': {'count': late_count, 'messages': late.data.copy()},
                          'receiving_error': {'count': receiving_error_count, 'messages': receiving_error.data.copy()},
                          }
        return Response(final_response)


class MailingViewSet(viewsets.ModelViewSet):
    """ Mailing serving api request to the "Client" model """
    queryset = Mailing.objects.all()
    serializer_class = MailingAPISerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.user_id:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No access'})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if request.user and request.user.is_staff:
            count_mailings = queryset.count()
            count_messages = Message.objects.all().count()
            serializer = self.get_serializer(queryset, many=True)
            final_response = {'count_mailings': count_mailings, 'count_messages': count_messages,
                              'all_mailings': serializer.data.copy()}
            return Response(final_response)
        elif str(request.user) != 'AnonymousUser':
            queryset = queryset.filter(user=request.user.id)
            count_mailings = queryset.count()
            mailings_user = list(queryset)
            count_messages =  Message.objects.filter(mailing_id__in=mailings_user).count()
            serializer = self.get_serializer(queryset, many=True)
            final_response = {'count_mailings': count_mailings, 'count_messages': count_messages,
                              'all_mailings': serializer.data.copy()}
            return Response(final_response)
        else:
            return Response({'error': 'No access'})


class MessagesInMailingAPIView(APIView):
    """ Class showing messages sent in a particular mailing list """

    def get(self, request, **kwargs):
        if 'mailing_id' in kwargs:
            mailing_id = kwargs['mailing_id']
            if request.user.is_staff:
                mailing = Mailing.objects.filter(id=mailing_id).values()
            elif str(request.user) != 'AnonymousUser':
                mailing = Mailing.objects.filter(id=mailing_id, user_id=request.user.id).values()
                if mailing.count() == 0:
                    return Response({'error': 'No access'})
            else:
                return Response({'error': 'No access'})
            messages = Message.objects.filter(mailing_id=mailing_id).values()
            count = messages.count()
            return Response({'mailing': MailingAPISerializer(mailing, many=True).data, 'count': count,
                             'messages': messages})


class StatisticMessagesAPIView(APIView):
    """ Class showing statistics of messages by status """

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            mailings = Mailing.objects.filter(user=request.user.id)
            mailings_user = list(mailings)
            all_messages = Message.objects.filter(mailing_id__in=mailings_user).values()
        else:
            all_messages = Message.objects.values()
        if 'status' in kwargs:
            status = kwargs['status']
        else:
            return Response({'all_messages': all_messages})
        wait_send_messages = all_messages.filter(status=0)
        sent_messages = all_messages.filter(status=1)
        late_messages = all_messages.filter(status=2)
        error_messages = all_messages.filter(status=3)

        if status == 0:
            return Response({'wait_send_messages': wait_send_messages})
        elif status == 1:
            return Response({'sent_messages': sent_messages})
        elif status == 2:
            return Response({'late_messages': late_messages})
        elif status == 3:
            return Response({'error_messages': error_messages})
        elif status == 4:
            return Response({'wait_send_messages': wait_send_messages, 'sent_messages': sent_messages,
                             'late_messages': late_messages, 'error_messages': error_messages})
        else:
            return Response({'error': 'The specified status does not exist'})