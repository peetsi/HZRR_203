
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
hr2_net_status10_UI.py

User Interface (commandline)

select and save orders to a file which are carried out by
a python execute module

hr2_net_status10_exec.py

Both modules use a common part for variable definition and functions:

hr2_net_status10_common.py


This frontend may be replaced by a graphical user interace (GUI) in the future

2021 03 03  pl  initial release developed from another, eralier version
'''

# *** import common part with some other imports

from hr2_net_status10_common import *

# ******************************************
# initialization and general functions

# *** check for key input

def curses_main(stdscr):
    """checking for keypress"""
    stdscr.nodelay(True)  # do not wait for input when calling getch
    return stdscr.getch()

def getch():
    """ get order of character pressed, -1 if not"""
    # '97' for 'a' pressed
    # '-1' on no presses
    key=curses.wrapper(curses_main)
    return int(key)

# ******************************************
# local functions

def save_settings(mode):
    ''' save current settings, mode 0=default, for recovery after new start'''
    ''' mode:  0 - set default values '''
    config = configparser.ConfigParser(allow_no_value=True)
    if mode == 0:
        hd = {
            "modules"    : [],
            "regulators" : [],
            "command"    : 0,
            "repeat"     : 0,
            "statistics" : True,
        }
    else:
            hd = {
            "modules"    : str(stu.order["modules"]),
            "regulators" : str(stu.order["regulators"]),
            "command"    : str(stu.order["command"]),
            "repeat"     : str(stu.order["repeat"]),
            "statistics" : str(stu.order["statistics"]),
        }
    config["order"] = hd

    with open(stu.fnSettings,"w") as configfile:
        config.write(configfile)
        # is closed on leaving with-statement

def read_settings():
    config = configparser.ConfigParser(allow_no_value=True)
    
    # check if settings-file exists
    if not os.path.exists(stu.fnSettings):
        os.system("mkdir "+stu.parPath)
        save_settings(0)   # generate default (empty) settings

    config.read(stu.fnSettings)
    # *** check settings for plausible values
    check=0
    try:
        a=config["order"]   # read last order to preset order values
    except:
        # no section from last order
        check|=0x0001
    else:
        try:
            b=stu.order
            b["modules"]    = ast.literal_eval(a["modules"])
            b["regulators"] = ast.literal_eval(a["regulators"])
            b["command"]    = a["command"]
            b["repeat"]     = int(a["repeat"])
            b["statistics"] = a["statistics"]=="True"
        except Exception as e:
            # something could not be read
            check|=0x0002
        else:
            # check for proper types
            if not type(b["modules"]) is list:
                check|=0x0004
            elif not type(b["regulators"]) is list:
                check|=0x0008
            elif not type(b["command"]) is str:
                check|=0x0010

            elif not type(b["repeat"])is int:
                check|=0x0020
            elif not type(b["statistics"]) is bool:
                check|=0x0040
            # check for proper contents:
            else:
                for m in b["modules"]:
                    if not m in stu.modules:
                        check|=0x0080
                for r in b["regulators"]:
                    if r not in [0,1,2,3]:
                        check|=0x0100
                if not b["command"] in stu.cmdsAllow:
                    check |= 0x0200
    if check!=0:
        save_settings(0)  # reset settings-file to default




# ******************************************
# transmit/recive commands to/from main program

def send_order_to_exe( mode=0, start = False, confirmed = False):
    ''' write an order for exec-task to an ini-file '''
    ''' mode:  0:set default values '''
    config = configparser.ConfigParser(allow_no_value=True)
    if mode==0:
        hd = {
            "modules"    : [],
            "regulators" : [],
            "command"    : "-",
            "repeat"     : 0,
            "statistics" : "True",
        }
    else:
        hd = {
            "modules"    : str(stu.order["modules"]),
            "regulators" : str(stu.order["regulators"]),
            "command"    : stu.order["command"],
            "repeat"     : str(stu.order["repeat"]),
            "statistics" : str(stu.order["statistics"]),
        }
    config["order"] = hd

    hd = {
        "startOrder"  : start,
        "orderTime"   : str(time.time()),
        "confirmed"   : confirmed,
    }
    config["start"] = hd

    with open(stu.fnPipe2exec,"w") as configfile:
        config.write(configfile)
        # is closed on leaving with-statement

def copy_reply_2_status(config,st):
    ''' copy reply pipe/file contents to status'''
    d = config["reply"]
    stu.reply["ack"]   = int(d["ack"])
    stu.reply["busy"]  = int(d["busy"])
    stu.reply["msg"]   = d["msg"]
    stu.reply["proc"]  = d["proc"]
    stu.reply["bar"]   = int(d["bar"])
    stu.reply["reset"] = int(d["reset"])

def make_bar( pos=0.0, min=0.0, max=100.0, barLen=50 ):
    ''' print a status-bar with progression'''
    symb=[' ','.',',',':','-','=','o','x','U']
    pos0 = (float(pos)-min)/(max-min)  # e [0..1]
    if pos0 < 0:
        s = "<" + (barLen-1) * "-"
    elif pos0 > 1:
        s = (barLen-1) * "+" + ">"
    else:
        nbar = int( pos0 * barLen )
        rem  = pos0*barLen - nbar  # remainder e [0,1]
        nsym = len(symb)
        ridx = int( rem * nsym )
        hs = symb[ridx]
        if pos==max:
            hs=""
        s = "%s%s%s"%((nbar-1)*"X",hs,(barLen-nbar-1)*(" "))
    s = "I"+s+"I"
    return s

def test_bar():
    ''' test make_bar() function '''
    s=make_bar( -1,  0,100,20)
    print("too low: ",s)
    s=make_bar(100, 10, 20,10)
    print("too high:",s)
    s=make_bar(  0,  0,100,10)
    print("  0/100: ",s)
    s=make_bar(100,  0,100,10)
    print("100/100: ",s)
    for x in range(0,101,1):
        s=make_bar(x,0,100,10)
        print("0 %4d  100:"%(x), s)

def start_exe():
    '''user interface -> exec: command to pipe'''
    config = configparser.ConfigParser(allow_no_value=True)
    tEnd = time.time() + stu.cmdtimeout
    print("wait for exec-task ready")
    while(True):
        time.sleep(0.5)
        config.read(stu.fnPipeFromExec)
        d = config["reply"]
        stu.reply["busy"]=int(d["busy"])
        print(".",end="")
        if stu.reply["busy"]==0:
            print()
            break
        if time.time() > tEnd:
            print("exec-task not ready: exit / try again")
            print("t -> terminate, e -> empty answer pipe, other continue")
            a = input("else exit >")
            if a == "e":
                write_answer_file(0)
                return 1
            elif a =="t":
                return 2
            else:
                tEnd = time.time() + stu.cmdtimeout

    print("sending order to exec-task")
    send_order_to_exe(1,start=True,confirmed=False)
    
    # *** wait for confirmation
    print("waiting for order confirmation")
    tEnd = time.time() + stu.cmdtimeout
    timeout = False
    conf    = False
    while True:
        # TODO timeout einbauen; falls timeout -> 
        #      write default values to reply - pipe/file
        time.sleep(0.5)
        print(">",end="")
        if time.time() > tEnd:
            timeout=True
            print("\nno confirmation->timeout")
            conf = "timeout"
            print("exec-task not ready: exit / try again")
            print("t -> terminate, e -> empty answer pipe, other continue")
            a = input("else exit >")
            if a == "e":
                write_answer_file(0)
                return 3
            elif a == "t":
                return 4
                break
            else:
                tEnd = time.time() + stu.cmdtimeout

        if os.path.exists(stu.fnPipeFromExec):
            config.read(stu.fnPipeFromExec)
            copy_reply_2_status(config, stu)

            if  stu.reply["ack"] == 1:
                # command was accepted and execution started
                print("\nfrom exec: ack=%d"%(stu.reply["ack"]))
                print("           msg=%s"%(stu.reply["msg"]))
                conf="confirmed"
                break

    # *** actualize pipe-file, remove start-flag
    #     last order and status stay visible
    print("stop order, let order information in file")
    send_order_to_exe(1,start=False,confirmed=conf)  # 
    
    # *** read and display messages form exe-task
    #     until it has finished - nolonger busy
    # TODO: exec task sends changed information at 
    #     least every 10 seconds. If this message is not
    #     obtained a timeout is activated
    msgOld=""
    procOld=""
    barOld=""

    tEnd = time.time() + stu.cmdtimeout
    while True:
        time.sleep(0.2)
        config.read(stu.fnPipeFromExec)
        d = config["reply"]
        dBusy = d["busy"]
        iBusy = int(dBusy)
        if iBusy==0:
            conf="performed"
            break
        iReset= int(d["reset"])
        if iReset > 0:
            conf="terminated by exec-task"
            break
        dMsg  = d["msg"]
        dProc = d["proc"]
        dBar  = d["bar"]

        if dMsg!=msgOld or dProc!=procOld or dBar!=barOld:
            tEnd = time.time() + stu.cmdtimeout  # extend timeout
            print("msg=%s; process=%s"%(dMsg,dProc))
            iBar = float(dBar)
            bar=make_bar(pos=iBar, min=0, max=100, barLen=50)
            print(bar)
        
        # *** NOTE 
        #     In a GUI place check an interrupt button here
        # simulation for test purposes using 'curses' class
        #print("to stop press q")
        #key=getch()
        #if key == ord("q"):
        #    conf="user terminated"
        #    break
        msgOld=dMsg
        procOld=dProc
        barOld=dBar
    # *** actualize command-file for watching
    #     exec-task can decide if command is
    #     nolonger valid and send an appropriate
    #     signal to reset communication
    send_order_to_exe(1,start=False,confirmed=conf)  # 

def read_answer_from_exe():
    config = configparser.ConfigParser(allow_no_value=True)
    if not os.path.exists(stu.fnPipeFromExec):
        write_answer_file(0)
    config.read(stu.fnPipeFromExec)
    stu.reply = config["reply"]

# ******************************************
# menu functions    

def show_selectlist( cl,mGroups ) :
    '''show a list of selections from list cl,
       meeting mGroups bit set
    '''
    for x in cl:
        ka=""
        kz=""
        if x[3]==0:
            ka="("
            kz=")"
        if x[1] & mGroups :
            print("%s  %s%s%s"%(x[0],ka,x[4],kz),end=" ")
            hs=x[6]
            if hs=="":
                print("")
            else:
                print("; %s)"%(hs))

def input_mrcr(w):
    ''' input modules, regulators, command and repeat 
        w           width of menu text
    '''
    # *** header
    txt="enter / change modules, regulators, command, repeats"
    print(w * "=")
    n = int( ( w - len(txt) ) / 2 )
    print(n * " ", txt)
    show_order_vars()
    while True:
        print(w * "-")
        cnt=1
        for key in stu.order:
            print("%d  %s (%s) "%(cnt,key,stu.order[key]))
            cnt += 1
        print("0  -Return-")
        a = input("change value Nr. ?")
        if a=="0" :
            save_settings(1)
            break
        if a=="1" :
            print("select modules : ")
            print("allowed modules: ",stu.modules)
            a = input("  ->")
            if a != "":
                li = make_list(a)
                a6=[]
                for a9 in li:
                    if not a9 in stu.modules:
                        print("ERROR: nr.%d not available"%(a9))    
                    else:
                        a6.append(a9)
                stu.order["modules"] = a6

        if a=="2" :
            print("select regulators : ", end="")
            a = input("(e.g. 0,1,2,3) ->")
            if a != "":
                li = make_list(a)
                a6=[]
                for a9 in li:
                    if not a9 in stu.regulators:
                        print("ERROR: nr.%d not available"%(a9))    
                    else:
                        a6.append(a9)
                stu.order["regulators"]  = a6

            pass
        if a=="3" :
            print("n = allowed / (n) not allowed (hex notation)):")
            for i in range(len(stu.cmdsAll)):
                x=stu.cmdsAll[i]
                if hr2Menu[i][1] & 0x07:
                    # only direct commands, no sequences
                    if hr2Menu[i][3] > 0:
                        print("%s "%(x),end="")
                    else:
                        print("(%s) "%(x),end="")
            print()
            print("*  for command-list;  ", end="")
            print("select command (%sx) "%(stu.order["command"]),end="")
            a = input(" ?")
            if a=="*":
                show_selectlist(hr2Commands,0xFF)
            elif a not in stu.cmdsAllow:
                print("ERROR: cmd %s not allowed!"%(a))
            else:
                stu.order["command"]=a
                idx = a.index(a)
                cnr = hr2Commands[idx][0]
                txt = hr2Commands[idx][4]
                rem = hr2Commands[idx][6]
                if rem !="":
                    rem ="("+rem+")"
                print("selected: %s - %s %s"%(cnr,txt,rem))

        if a=="4" :
            a = input("repeat how many times ? ")
            try:
                stu.order["repeat"] = int(a)
            except:
                stu.order["repeat"] = 1
            pass

def show_order_vars():
    d = stu.order
    for key in d :
        print("%s: %s, "%(key,d[key]),end="")
    print()

def select_menu( menuData, mGroup, txtHead, w ):
    ''' show menu from parameter list 
        menuData   list with menu information
        txtHead    text for menu header
        w          width of menu
    '''
    # *** header
    print(w * "=")
    n = int( ( w - len(txtHead) ) / 2 )
    print(n * " ", txtHead)
    show_order_vars()
    print(w * "-")
        
    # *** print menu and find allowed answers
    allowed = []
    for m in menuData:
        if  m[1] and mGroup : # belongs to menu group
            if m[3] >  0:     # item is implemented
                allowed.append(m[0])
    show_selectlist(menuData,mGroup)
    print(" 0    -End-")
    allowed.append("0")
    print(w*"-")
    
    # *** select until answer is allowed
    while True:
        a = input("--> ")
        if a in allowed:
            break
        print("<%s> not allowed, try again, 0=Ende"%(a),end="")
    return a    

def init():
    init_common()
    # set back order file to default
    send_order_to_exe(0,start=False,confirmed="-")  # clear order
    # set allowed/implemented commands list
    stu.cmdsAll  =[x[0] for x in hr2Menu]
    # init curses:
    if not os.path.exists("/home/pi/.terminfo"):
        os.system("mkdir /home/pi/.terminfo")
        os.system("export TERM=linux")
        os.system("export TERMINFO=/home/pi/.terminfo")
    # read settings from last run of the user interface program
    read_settings()


def net_menu():
    ''' menu for test commands or comand sequences 
    '''
    width= 79
    init()

    while True:
        stu.menuGroup = 64
        a0 = select_menu(hr2Menu,64,"main menu",width)
        if a0 == "0":
            break
        elif a0 == "1":  # read variables from modules
            while True:
                a1 = select_menu(hr2Menu,1,"read variables from modules",width)
                if a1=="0":
                    break
                else:
                    stu.cmd = int(a1,16)
        elif a0 == "2":  # parameter handling
            while True:
                a1 = select_menu(hr2Menu,2,"parameter handling",width)
                if a1=="0":
                    break
                else:
                    stu.cmd = int(a1,16)
        elif a0 == "3":  # module and valve commands
            while True:
                a1 = select_menu(hr2Menu,4,"module and valve commands",width)
                if a1=="0":
                    break
                else:
                    stu.cmd = int(a1,16)
        elif a0 == "4":  # function sequences
            while True:
                a1 = select_menu(hr2Menu,8,"function sequences",width)
                if a1=="0":
                    break
                else:
                    stu.cmd = int(a1,16)
        elif a0 == "88":  # select modules, regs, command, repeat
            input_mrcr(width)
            pass
        elif a0 == "99":  # turn statistics on/off
            stu.order["statistics"] = not stu.order["statistics"]
            print("statistics is now ", stu.order["statistics"])
        elif a0 == "F0":  # test UI communication
            stu.order["command"] = "F0"
        elif a0 == "st":  # start execution
            start_exe()  # store selection and start execution from ini-file
        save_settings(1)

# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# -------------------------------------------------------------------

if __name__ == "__main__" :
    #test_bar()
    net_menu()

