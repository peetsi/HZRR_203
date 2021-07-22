from guizero import App, PushButton, Text

app = App(layout="grid")

def scanAll():
    textAction.value = "Zeige alle Module an ..."
    pass

def uebersicht():
    textAction.value = "Erstelle Übersicht ..."
    pass

def diagram_all():
    textAction.value = "Erstelle alle Diagramme ..."
    pass



buttScan     = PushButton(app, text="Scanne alle Module", command=scanAll, align="left", grid=[0,0])
buttUeb      = PushButton(app, text="Übersicht erstellen", command=uebersicht, align="left", grid=[0,1])
buttDiagAll  = PushButton(app, text="Alle Diagramme der letzten 2 Tage", command=diagram_all, align="left", grid=[0,2])

textAction = Text(app, text="---", align="left",grid=[0,9] )

app.display()

