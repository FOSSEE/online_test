import json
from channels import Group
from channels.sessions import channel_session
from datetime import datetime
import pytz

#Local Imports
from yaksh.models import Room, User


@channel_session
def ws_connect(message):
    try:
        path = message['path'].split('/')[1:]
        prefix, label, course_id = path[0], path[1], path[2]
        msg_data = {}
        if prefix != 'chat':
            msg_data['error'] = 'invalid ws path={0}'.format(message['path'])
            Group('chat-'+label, channel_layer=message.channel_layer).send(
                {'text': json.dumps(msg_data)}
            )
            message.reply_channel.send({'close': True})
            return
        room = Room.objects.get(
            label=label, course_id=course_id
        )
    except ValueError:
        msg_data['error'] = 'invalid ws path=%s', message['path']
        Group('chat-'+label, channel_layer=message.channel_layer).send(
            {'text': json.dumps(msg_data)}
        )
        message.reply_channel.send({'close': True})
        return
    except Room.DoesNotExist:
        msg_data['error'] = 'ws room does not exist label=%s', label
        Group('chat-'+label, channel_layer=message.channel_layer).send(
            {'text': json.dumps(msg_data)}
        )
        message.reply_channel.send({'close': True})
        return

    print(
        'chat connect room={0} client={1}:{2}'.format(
        room.label, message['client'][0], message['client'][1]
        )
    )

    Group('chat-'+label).add(message.reply_channel)
    message.channel_session['room'] = room.label
    message.reply_channel.send({'accept': True})


@channel_session
def ws_receive(message):
    # Look up the room from the channel session, bailing if it doesn't exist
    try:
        label = message.channel_session['room']
        room = Room.objects.get(label=label)
    except KeyError:
        print('no room in channel_session')
        return
    except Room.DoesNotExist:
        print('received message, buy room does not exist label=%s', label)
        return

    # Parse out a chat message from the content text, bailing if it doesn't
    # conform to the expected message format.
    try:
        print(message['text'])
        data = json.loads(message['text'])
    except ValueError:
        print("ws message isn't json text=%s", message['text'])
        return

    if set(data.keys()) != set(('sender_id', 'message')):
        print("ws message unexpected format data=%s", data)
        return

    if data:
        context = {}
        chat_dict = {}
        print('chat message room={0} handle={1} message={1}'.format(
            room.label, data['sender_id'], data['message']))
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
