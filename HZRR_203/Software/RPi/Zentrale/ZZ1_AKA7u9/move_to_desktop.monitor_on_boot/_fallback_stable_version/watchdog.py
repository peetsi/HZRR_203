

import time, os


def run_cmd(cmd):
    print("executing:", cmd)
    return os.system(cmd)

# init watchdog in this file..
#otherwise if theres a problem the watchdog will be activated but with no further interaction..-> result: reboot
#print("!!!!starting watchdog!!!!", run_cmd("sudo /etc/init.d/watchdog start"))
print("!!!!enabling watchdog!!!!", run_cmd("sudo systemctl enable watchdog"))
print("!!!!starting watchdog!!!!", run_cmd("sudo systemctl start watchdog"))
run_cmd("sudo systemctl -l status watchdog")
# basic hang-up protection
while True:
    # this should be obsolete. leaving it inside just in case.
    print("!!!!sending keep alive to watchdog!!!!")
    run_cmd('sudo sh -c "echo . >> /dev/watchdog"')
    time.sleep(13) # give some playground
