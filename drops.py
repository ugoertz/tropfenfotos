from time import sleep

from flask import Flask, render_template, request
import RPi.GPIO as GPIO


app = Flask(__name__)


# gpio pin layout
CAM1 = 14  # focus
CAM2 = 15  # pic
FLASH1 = 2
VALVEPINS = [None, 5, 26, 6 ]  # valves numbered starting from 1


def default_values():
    data = {}

    # flashes
    for f in FLASHES:
        data['flash%d' % f] = True
        data['flashtime%d' % f] = 80

    return data


def init_gpio():
    GPIO.setmode(GPIO.BCM)
    for pin in [CAM1, CAM2, FLASH1, ] + VALVEPINS[1:]:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)


def shoot(mode, data):
    print('shoot', mode, data)

    # wake up camera
    GPIO.output(CAM1, True)
    sleep(.6)
    GPIO.output(CAM1, False)

    if mode == 'C':
        valid_pins = [CAM1, CAM2, ]
    elif mode == 'CF':
        valid_pins = [CAM1, CAM2, FLASH1, ]
    elif mode == 'all':
        valid_pins = [CAM1, CAM2, FLASH1, ] + VALVEPINS
    else:
        return

    timeline = [(-1, -1, -1), ]  # dummy first entry

    # camera
    try:
        ct = max(0, int(data['camtime']))
        timeline.append((ct, CAM1, True))
        timeline.append((ct + 1, CAM2, True))
        timeline.append((ct + 100, CAM2, False))
        timeline.append((ct + 101, CAM1, False))
    except ImportError:
        return

    # flash  # FIXME currently one flash only
    if data['flash1']:
        try:
            ft1 = max(0, int(data['flashtime1']))
            timeline.append((ct + ft1, FLASH1, True))
            timeline.append((ct + ft1 + 5, FLASH1, False))
        except:
            pass

    # valves
    for v, pin in enumerate(VALVEPINS):
        if not pin:
            continue  # discard first "dummy" entry
        topen = 0
        tclose = 0
        for i in range(3):
            if data['waitV%dX%d' % (v, i)] and data['openV%dX%d' % (v, i)]:
                try:
                    topen = tclose + max(0, int(data['waitV%dX%d' % (v, i)]))
                    # +1: make sure this comes after topen even if data['openV1Xi'] == 0
                    tclose = topen + 1 + max(0, int(data['openV%dX%d' % (v, i)]))

                    timeline.append((topen, pin, True))
                    timeline.append((tclose, pin, False))
                except:
                    pass
            else:
                break

    timeline = sorted(timeline)
    print(timeline)

    sleep(1)
    for i in range(1, len(timeline)):
        prev_t, _, _ = timeline[i-1]
        now_t, pin, value = timeline[i]
        sleep((now_t - prev_t)/1000)
        if pin in valid_pins:
            GPIO.output(pin, value)


def flash(fl, data=None):
    if fl == 1:
        GPIO.output(CAM1, True)
        sleep(1)
        GPIO.output(CAM1, False)


def valve(v, mode, data=None):
    pin = VALVEPINS[v]
    if mode == 'openclose':
        VALVES[v] = not VALVES[v]
        GPIO.output(pin, VALVES[v])
    elif mode == 'test':
        for i in range(3):
            if data['waitV%dX%d' % (v, i)] and data['openV%dX%d' % (v, i)]:
                try:
                    wt = int(data['waitV%dX%d' % (v, i)])
                    ot = int(data['openV%dX%d' % (v, i)])
                    GPIO.output(pin, False)
                    sleep(wt/1000)
                    GPIO.output(pin, True)
                    sleep(ot/1000)
                    GPIO.output(pin, False)
                except:
                    pass
                finally:
                    GPIO.output(pin, False)
        

FLASHES = [1, 2, 3, ]
VALVES = {i: False for i in range(1, 4)}
INPUT = ['camtime', ]
CHECKBUTTONS = []
ACTIONS = [
        ('shoot', shoot, ('all', )),
        ('submitC', shoot, ('C', )),
        ('submitCF', shoot, ('CF', )),
        ]


for f in FLASHES:
    CHECKBUTTONS.append('flash%d' % f)
    INPUT.append('flashtime%d' % f)
    ACTIONS.append(('submitF%d' % f, flash, (f, )))

for v in VALVES.keys():
    ACTIONS.append(('submitV%d' % v, valve, (v, 'test', )))
    ACTIONS.append(('submitV%dOC' % v, valve, (v, 'openclose', )))
    for i in range(3):
        INPUT.append('waitV%dX%d' % (v, i))
        INPUT.append('openV%dX%d' % (v, i))



@app.route('/', methods=['GET', 'POST', ])
def index():
    data = default_values()

    if request.method == 'POST':
        for k in CHECKBUTTONS:
            # print(k, request.form[k])
            data[k] = k in request.form
        for k in INPUT:
            # print(k, request.form.get(k, '-'))
            data[k] = request.form[k]

        for s, fct, args in ACTIONS:
            if s in request.form:
                fct(*args, data=data)

    return render_template('index.html', data=data)

if __name__ == '__main__':
    init_gpio()
    app.run(debug=True, host='0.0.0.0')

