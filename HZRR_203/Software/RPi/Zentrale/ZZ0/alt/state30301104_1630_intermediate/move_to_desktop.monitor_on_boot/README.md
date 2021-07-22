*******************
*****[README]******
*******************

**[PREREQUIREMENTS]
- THE USB STICK HAS TO HAVE THE NAME "PYTHONUSB" - EXACTLY LIKE THIS WRITTEN! 
- THE FOLDER WHICH WILL BE COPIED TO THE RAM EACH BOOT, HAS TO HAVE THE NAME "move_to_desktop.monitor_on_boot" EXACTLY!!
* (both settings can be changed in the script "move_files_from_usb_and_boot_them.py")
* (IMPORTANT: IF CHANGED - CHANGE IN STEP 2 ASWELL!)

**[INSTALL]
#BOOT ON THE PI WITHOUT OVFS ACTIVATED. THIS STEP COMES LATER

**[1. CREATE SYSTEMD SERVICE FILE]
sudo systemctl edit --force --full starthzrr.service

**[2. INSERT THIS INTO THE SYSTEMD FILE]
[Unit]

Description=copy files from usb
After=local-fs.target systemd-longid.service systemd-user-sessions.service
RequiresMountsFor=/media/pi/PYTHONUSB /var/log /var/run /var/lib /boot
#StartLimitIntervalSec=140
#StartLimitBurst=5

[Service]
User=root
RemainAfterExit=yes
ExecStart=/usr/bin/python3 /media/pi/PYTHONUSB/move_to_desktop.monitor_on_boot/move_files_from_usb_and_boot_them.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

PRESS "CTRL" + "X"
PRESS "J" ("Y" on english installation)
PRESS "ENTER"

**[3. ACTIVATE SYSTEMD SERVICE]
sudo systemctl start starthzrr.service

**[4. EXTEND FILESYSTEM - !!! IMPORTANT !!!]
# if this is not done, the OVFL will have 0 space, therefore no data can be send to the live system!
sudo raspi-config
MOVE TO "7. ADVANCED CONFIG"
MOVE TO "A1 EXPAND FILESYSTEM"
PRESS "ENTER"

**[5. ACTIVATE OVFL]
sudo raspi-config
MOVE TO "7. ADVANCED CONFIG"
MOVE TO "AB OVERLAY FS"
PRESS "ENTER"
PRESS "YES"
# WAIT UNTIL THIS PROCESS IS DONE, COULD TAKE SOME TIME.
PRESS "OK"
PRESS "NO"

**[6. NOW REBOOT THE PI AND HOPE FOR THE BEST.]
(but i do some GIT PUSHup's before ;)




----------------------------------------------------------------------
----------------------------------------------------------------------
------EVERYTHING BEYOND THOSE LINES, ONLY THE DEVS CARE ABOUT.--------
----------------------------------------------------------------------
----------------------------------------------------------------------

eventually another fix for tkinter...
export MPLBACKEND='Agg'

important!
sudo cp ~/.Xauthority ~root/
if tkinter fails - but it should not anymore as it has been integrated into movefilesfromusbandbootthem.py.

create a service
sudo systemctl edit --force --full starthzrr.service

include this (seems to work)...:

[Unit]
Description=copy files from usb
After=local-fs.target systemd-longid.service systemd-user-sessions.service
RequiresMountsFor=/media/pi/pythonUSB /var/log /var/run /var/lib /boot
StartLimitIntervalSec=140
StartLimitBurst=5
[Service]
User=root
RemainAfterExit=yes
ExecStart=/media/pi/pythonUSB/move_to_desktop.monitor_on_boot/move_files_from_usb_and_boot_them.py
Restart=on-failure
RestartSec=10
[Install]
WantedBy=multi-user.target


save file and run this line:
/media/pi/pythonUSB/move_to_desktop.monitor_on_boot/move_files_from_usb_and_boot_them.py

reboot and test.
if does work - test with overlayfilesystem

*USB PORT BOTTOM LEFT*
	 [-][-]
[ETH][X][-]

serPort = "/dev/serial/by-path/platform-3f980000.usb-usb-0:1.1.3:1.0-port0" 




