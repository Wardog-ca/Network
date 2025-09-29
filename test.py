import tkinter as tk
from tkinter import scrolledtext

root = tk.Tk()
root.geometry("700x500")

log_text = scrolledtext.ScrolledText(root)
log_text.pack(fill=tk.BOTH, expand=True)

log_text.insert(tk.END, "Tkinter fonctionne !\n")
tk.Button(root, text="Test bouton").pack()

root.mainloop()
