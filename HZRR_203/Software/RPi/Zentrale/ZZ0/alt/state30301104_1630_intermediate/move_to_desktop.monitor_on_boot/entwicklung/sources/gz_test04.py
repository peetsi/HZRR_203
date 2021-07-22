from guizero import App, ListBox
app = App()
list_box = ListBox(app, items=["a list",1,2,3,4,5,"Zeilen"], height="fill", align="left")
app.display()

