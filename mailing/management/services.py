
import time
from datetime import timedelta, datetime
import requests, json
from django.utils import timezone

from celery_app import app
from management.models import Client, Message, Mailing
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('MAILING_API_KEY')
URL_MAILING = os.getenv('URL_MAILING')

@app.task()
def send_message(id_message: int, phone: int, text: str, url: str = URL_MAILING,
                 token: str = TOKEN):
    """
        A function that sends messages to an external server via API. Executed in the background due to app celery

        id_message - id of new message
        phone - client phone number
        text - message text
        url - url address to send the request. If you don't use the default value, don't forget to specify "/" at the end
        token - unique token for sending messages to external api

    """
    url = url + str(id_message)
    headers = {
        'accept': 'application/json',
        'Authorization': f'{token}',
        'Content-Type': 'application/json',
    }
    data = {
        "id": id_message,
        "phone": phone,
        "text": f"{text}"
    }
    json_data = json.dumps(data)
    try:
        response = requests.post(url, data=json_data, headers=headers).json()
        return response['message']
    except requests.exceptions.ConnectionError as e:
        return e


def get_filters(tag_filter: str, operator_code_filter: str, dt_end: str):
    response = []
    time_zone_filter = []
    for filter_name, filter_param in ('tag__in', tag_filter), ('operator_code__in', operator_code_filter):
        filter_param = filter_param.split(';')
        if filter_param != ['']:
            response.append((filter_name, filter_param))
    for i in range(24):
        """
            You need to filter out time zones that are definitely not in the sample.
            This will help not to load the database unnecessarily
        """
        if dt_end > (timezone.now()+timedelta(hours=i)):
            time_zone_filter.append(i)
    response.append(('time_zone__in', time_zone_filter))
    return response


@app.task()
def start_mailing(mailing_id: int, dt_start: str, dt_end: str, text: str, tag_filter: str,
                   operator_code_filter: str, stopped: bool):
    """
        Mailing start function. Executed in the background due to app celery

        mailing_id - id of new mailing
        dt_start - the date and time of the mailing start. The value takes into account the local client time
        dt_end - the date and time when the mailing ends. The value takes into account the local client time
        text - text of mailing
        tag_filter - tags of users to whom messages will be sent. Specify in the format "900;901;902...".
        If not specified, users with and without all tags will
        be selected
        operator_code_filter - operator codes of users to whom messages will be sent. Specify in the format
        "900;901;902...". If not specified, users with all codes will be selected
        stopped - A mark indicating whether the mailing has been stopped
    """
    # Filter for suitable time zones
    excluded_users_id = []
    if stopped:
        excluded_users_list = list(Message.objects.filter(mailing_id=mailing_id).values())
        for i in excluded_users_list:
            excluded_users_id.append(i['client_id'])
    # Creating a list by filters
    model = Client.objects.filter(**{key: value for key, value in get_filters(
        operator_code_filter=operator_code_filter,
        tag_filter=tag_filter,
        dt_end=dt_end) }).values().exclude(id__in=excluded_users_id).order_by('time_zone')
    model = list(model)
    for i in model:
        if dt_end + timedelta(hours=23) > timezone.now():
            # Creating a new message object
            new_message = Message.objects.create(status=0, mailing_id=mailing_id, client_id=int(i['id']))
            client_local_time = timezone.now() + timedelta(hours=int(i['time_zone']))
            new_message.save()
            if dt_start > client_local_time:
                send_message.apply_async([new_message.id, i['phone_number'], 'text'],
                                         eta=dt_start+timedelta(hours=int(i['time_zone']))
                                         )
            elif dt_end < client_local_time:
                new_message.status = 2
                new_message.save()
            else:
                response = send_message(id_message=new_message.id, phone=i['phone_number'], text=text)

                if response == 'OK':
                    new_message.status = 1
                    new_message.save()
                else:
                    new_message.status = 3
                    new_message.save()
                    model.append(i) # If the submission fails, the user is added to the end of the queue, to try again.
        else:
            break
    try:
        mailing = Mailing.objects.get(id=mailing_id)
        mailing.active = False
        mailing.stopped = True
        mailing.save()
    except Exception as e:
        print(e)
