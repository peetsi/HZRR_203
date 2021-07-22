from guizero import App, PushButton, Text
import threading
import time


# Action you would like to perform
def counter0():
    global s0
    text0.value = int(text0.value) + 1  # works
    text1.value = s0                    # works


def run_command():
    time.sleep(1)          # originally a subprocess is called here; works
    text1.value = "ready"  # only diplays this after a delay


def counter1():
    global s0
    text1.value = "Running command..."
    threading.Thread(target=run_command).start()


s0 = "start something after pressing butt1"

app = App("Hello world", layout="grid")

text0 = Text(app, text="1", align="left", grid=[0, 1])
text1 = Text(app, text=s0, align="left", grid=[0, 8])
butt1 = PushButton(app, text="Button", command=counter1,
                   align="left", grid=[0, 2])
text0.repeat(10000, counter0)

app.display()