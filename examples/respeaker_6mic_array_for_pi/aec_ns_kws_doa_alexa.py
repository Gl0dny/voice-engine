"""
Record audio from a 6 microphone array, and then search the keyword "snowboy".
After finding the keyword, Direction Of Arrival (DOA) is estimated.

The hardware is respeaker 6 mic array for raspberry pi.

Hands-free Voice Assistant with Snowboy and Alexa Voice Service. The wake-up keyword is "alexa"

Requirement:
    pip install avs
"""

import signal
import time
from voice_engine.source import Source
from voice_engine.ec import EC
from voice_engine.ns import NS
from voice_engine.kws import KWS
from voice_engine.doa_respeaker_6mic_array import DOA
from pixel_ring import pixel_ring
from gpiozero import LED
from avs.alexa import Alexa

power = LED(5)
power.on()


def main():
    src = Source(rate=16000, frames_size=320, channels=8)
    ec = EC(channels=src.channels, capture=0, playback=7)
    ns = NS(rate=src.rate, channels=1)
    kws = KWS(model='snowboy', sensitivity=0.6, verbose=True)
    doa = DOA(rate=16000, chunks=20)
    alexa = Alexa()

    alexa.state_listener.on_listening = pixel_ring.listen
    alexa.state_listener.on_thinking = pixel_ring.think
    alexa.state_listener.on_speaking = pixel_ring.speak
    alexa.state_listener.on_finished = pixel_ring.off

    src.pipeline(ec, ns, kws, alexa)

    src.link(doa)

    def on_detected(keyword):
        direction = doa.get_direction()
        print('detected {} at direction {}'.format(keyword, direction))
        alexa.listen()
        pixel_ring.wakeup((direction + 0) % 360)

    kws.on_detected = on_detected

    is_quit = []
    def signal_handler(sig, frame):
        is_quit.append(True)
        print('quit')
    signal.signal(signal.SIGINT, signal_handler)

    src.pipeline_start()
    while not is_quit:
        time.sleep(1)

    src.pipeline_stop()
    pixel_ring.off()

    # wait a second to allow other threads to exit
    time.sleep(1)

if __name__ == '__main__':
    main()
