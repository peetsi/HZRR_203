from guizero import App, Text, TextBox

app = App(layout="grid")

name_label = Text(app, text="Name", grid=[0,0], align="left")
name = TextBox(app, grid=[1,0])
surname_label = Text(app, text="Surname", grid=[0,1], align="left")
surname = TextBox(app, grid=[1,1])
dob_label = Text(app, text="Date of Birth", grid=[0,2], align="left")
dob = TextBox(app, grid=[1,2])

app.display()