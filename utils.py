# utils.py
import tkinter as tk

class TextLineNumbers(tk.Canvas):
    """
    Canvas que muestra los números de línea junto a un widget Text.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        """
        Asocia el widget Text para mostrar sus líneas.
        """
        self.textwidget = text_widget

    def redraw(self, *args):
        """
        Redibuja los números de línea al desplazarse o escribir.
        """
        self.delete("all")
        if not self.textwidget:
            return
        i = self.textwidget.index("@0,0")
        while True:
            dline = self.textwidget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=linenum)
            i = self.textwidget.index(f"{i}+1line")
