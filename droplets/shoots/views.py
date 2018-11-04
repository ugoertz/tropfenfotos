import json
import os
import os.path

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.shortcuts import render


import requests

from .consumers import FlashairConsumer


NUM_VALVES = 3
NUM_ROUNDS = 5


def flashair(request):
    try:
        filelist = requests.get(
                'http://192.168.0.1/command.cgi?op=100&DIR=/DCIM/101OLYMP')
        filelist = str(filelist.text).splitlines()
        filelist = [f.split(',')[1] for f in filelist if 'JPG' in f]
        filename = filelist[-1]

        f = requests.get(
                'http://192.168.0.1/DCIM/101OLYMP/' + filename)
        with open(os.path.join(settings.MEDIA_ROOT, filename), 'wb') as fi:
            fi.write(f.content)
    except ImportError:  # FIXME
        filename = 'ERROR.JPG'

    layer = get_channel_layer()
    async_to_sync(layer.group_send)('group1', {
        'type': 'group1.alarm',
        'message': filename,
        })
    print('Sent message')
    return render(request, 'base/empty.html')


def valves(request):
    valvelist = []
    for n in range(NUM_VALVES):
        valvelist.append({
            'n': n,
            'rounds': [],
            })
        for i in range(NUM_ROUNDS):
            valvelist[-1]['rounds'].append({
                'id': '%dX%d' % (n, i),
                'wait': 0,
                'open': 0,
                })

    if request.POST:
        for n in range(NUM_VALVES):
            for i in range(NUM_ROUNDS):
                for t in ['wait', 'open', ]:
                    val = request.POST.get('%s%s' % (t, valvelist[n]['rounds'][i]['id']))
                    if val:
                        valvelist[n]['rounds'][i][t] = val

    print(request.POST)
    print(valvelist)
    return render(request, 'shoots/valves.html', context={'valvelist': valvelist, })

