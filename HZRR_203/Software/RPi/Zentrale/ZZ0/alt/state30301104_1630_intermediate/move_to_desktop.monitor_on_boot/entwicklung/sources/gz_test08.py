from guizero import App, Combo, Text

def update_bg():
    app.bg = bg_combo.value

def update_text():
    app.text_color = text_combo.value

colors = ["black", "white", "red", "green", "blue"]

app = App()
app.bg = "black"
app.text_color = "white"

title1 = Text(app, text="Background color")
bg_combo = Combo(app, options=colors, selected=app.bg, command=update_bg)

title2 = Text(app, text="Text color")
text_combo = Combo(app, options=colors, selected=app.text_color, command=update_text)

app.display()