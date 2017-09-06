import json
from channels import Group
from channels.sessions import channel_session
from channels.auth import channel_session_user_from_http
from datetime import datetime
import pytz

#Local Imports
from yaksh.models import Room, User


@channel_session_user_from_http
def ws_connect(message):
    try:
        path = message['path'].split('/')[1:]
        user = message.user
        prefix, label, course_id = path
        if prefix != 'chat':
            message.reply_channel.send({'close': True})
            return

        room = Room.objects.get(
            label=label, course_id=course_id
        )
        result = [room.course.is_creator(user), room.course.is_teacher(user),
                  room.course.is_student(user)]
        if not any(result):
            message.reply_channel.send({'close': True})
            return
    except ValueError:
        message.reply_channel.send({'close': True})
        return
    except Room.DoesNotExist:
        message.reply_channel.send({'close': True})
        return

    Group('chat-'+label).add(message.reply_channel)
    message.channel_session['course'] = room.course_id
    message.channel_session['room'] = room.label
    message.reply_channel.send({'accept': True})


@channel_session
def ws_receive(message):
    # Try to find the room, disconnect if not found
    try:
        course = message.channel_session['course']
        room = Room.objects.get(course_id=course)
        label = message.channel_session['room']
    except (KeyError, Room.DoesNotExist):
        message.reply_channel.send({'close': True})
        return

    # Check for valid json message format
    try:
        data = json.loads(message['text'])
    except ValueError:
        message.reply_channel.send({'close': True})
        return

    if set(data.keys()) != set(('sender_id', 'message')):
        message.reply_channel.send({'close': True})
        return

    if data:
        context = {}
        chat_dict = {}
        message = room.messages.create(**data)
        sender_tz = User.objects.get(id=data['sender_id']).profile.timezone
        msg_date = message.timestamp.astimezone(pytz.timezone(sender_tz))
        chat_dict = {
            "sender": message.sender.id,
            "sender_name": message.sender.get_full_name().title(),
            "timestamp": datetime.strftime(msg_date, "%Y-%m-%d %H:%M:%S"),
            "message": message.message
        }
        context['messages'] = chat_dict
        context['success'] = True
        # See above for the note about Group
        Group('chat-'+label).send({'text': json.dumps(context)})


@channel_session
def ws_disconnect(message):
    try:
        label = message.channel_session['room']
        Room.objects.get(label=label)
        Group('chat-'+label).discard(message.reply_channel)
    except (KeyError, Room.DoesNotExist):
        pass
    message.reply_channel.send({'close': True})