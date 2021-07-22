from tkinter import *
win = Tk()
canvas = Canvas(win, width=800,height=500)
canvas.pack()


rw = 20  # width
rh = 20  # height
px = 30  # position x
py = 30  # position y
lm = 20
um = 20
abst = 50

col = ['red','blue','green','black','yellow','cyan','orange','brown','',]
for  i in range(2) :
  for j in range(2) :
    idx = i+j
    px = lm + i * ( rw + abst )
    py = um + j * ( rh + abst )
    print("zeichne Rechteck an x=%d y=%d w=%d h=%d"%(px,py,rw,rh))
    canvas.create_rectangle(rw,rh, px,py, fill=col[idx])
    canvas.create_rectangle(px,py, rw,rh, fill=col[idx])

  
linA = canvas.create_rectangle(20, 20, 40, 50, fill="red")
linB = canvas.create_rectangle(20, 150,  5,  6, fill="blue")
linC = canvas.create_rectangle(150, 120, 33, 33, fill="green")
linD = canvas.create_rectangle(150, 150, rw, rh, fill="yellow")

canvas.delete(linA)

mainloop()




  
