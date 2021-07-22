from guizero import App, TextBox

def highlight():
    text_box.bg = "lightblue"

def lowlight():
    text_box.bg = "white"

app = App()
text_box = TextBox(app)

# When the mouse enters the TextBox
text_box.when_mouse_enters = highlight
# When the mouse leaves the TextBox
text_box.when_mouse_leaves = lowlight

app.display()
