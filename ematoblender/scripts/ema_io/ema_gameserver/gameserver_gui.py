__author__ = 'Kristy'

import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd


def main():
    root = tk.Tk()
    root.geometry("900x500")
    root.title("Ematoblender Gameserver")
    icon = 'images/ti.ico'
    if os.path.isfile(icon):
        root.wm_iconbitmap(bitmap=icon)
    app = Application(master=root)
    app.mainloop()


def example_command():
    print('weeee!!!')


class Application(tk.Frame):
    """ GUI class for the gameserver application. """
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.root = master

        self.shownetworking = tk.IntVar()

        self.createMenuBar()

        # create frame areas
        self.createTopFrame()
        self.createMiddleFrame()
        self.createStatusLabel()

    def createMenuBar(self):
        """Create a manubar with pulldown menus"""
        # create a menubar
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)

        # create the filemenu
        filemenu.add_command(label="Clear Cache", command=example_command)
        filemenu.add_command(label="Pause Sending/Receiving", command=example_command)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # create the Edit menu
        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label="Show/Hide Networking", command=example_command)
        editmenu.add_separator()
        editmenu.add_command(label="User Preferences", command=example_command)
        menubar.add_cascade(label="Edit", menu=editmenu)

        # create the Help menu
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Go to documentation", command=example_command)
        helpmenu.add_command(label="About", command=example_command)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)



    def createTopFrame(self):
        """Put widgets in the top frame"""
        self.topframe = tk.Frame(self.root, relief='raised', bd=2)
        self.topframe.pack(fill=tk.X)
        lbl = tk.Label(self.topframe, text='This is the top frame\n\nIt will have useful buttons for all environments')
        lbl.pack()

    def createMiddleFrame(self):
        self.middleframe = tk.Frame(self.root)
        self.middleframe.pack(expand=True, fill=tk.BOTH)
        self.createLeftFrame()
        self.createRightFrame()

    def createLeftFrame(self):
        """Put widgets in the left frame"""
        self.leftframe = tk.Frame(self.middleframe, relief='raised', bd=2)
        self.leftframe.pack(side=tk.LEFT, fill=tk.BOTH)
        lbl = tk.Label(self.leftframe, text='Incoming data:')
        lbl.pack()

        # saving locations
        saveframe = tk.Frame(self.leftframe, relief='groove', bd=2)
        saveframe.pack(fill=tk.X)

        # manual server calls
        callsframe = tk.Frame(self.leftframe, relief='groove', bd=2)
        callsframe.pack(fill=tk.X)
        self.allow_man_calls = tk.BooleanVar()
        manallow = tk.Checkbutton(callsframe, text="Allow manual calls to the data server",
                                  variable=self.allow_man_calls,
                                  onvalue=1, offvalue=0,
                                  command=self.update_disabled_buttons)
        manallow.pack(fill=tk.X)

        ipad, expad=3,1
        manbtn1 = tk.Button(callsframe, text='Single', state=tk.DISABLED)
        manbtn1.pack(side=tk.LEFT, ipadx=ipad, padx=expad)
        manbtn2 = tk.Button(callsframe, text='Stream', state=tk.DISABLED)
        manbtn2.pack(side=tk.LEFT, ipadx=ipad, padx=expad)
        manbtn3 = tk.Button(callsframe, text='Status', state=tk.DISABLED)
        manbtn3.pack(side=tk.LEFT, ipadx=ipad, padx=expad)
        self.manual_buttons = [manbtn1, manbtn2, manbtn3]

    def update_disabled_buttons(self):
        for btn in self.manual_buttons:
            btn.configure(state=tk.NORMAL if self.allow_man_calls.get() == 1 else tk.DISABLED)

    def createRightFrame(self):
        """Put widgets in the right frame"""
        self.rightframe = tk.Frame(self.middleframe, relief='raised', bd=2)
        self.rightframe.pack(side=tk.LEFT, fill=tk.BOTH)
        lbl = tk.Label(self.rightframe, text='Outgoing data:')
        lbl.pack()

        # options for data smoothing/delay
        smoothframe = tk.Frame(self.rightframe, relief='groove')
        smoothframe.pack(side=tk.TOP, fill=tk.X)
        lbl = tk.Label(smoothframe, text='Data filtering options')
        lbl.pack()

        # options for head-correction
        corrframe = tk.Frame(self.rightframe, relief='groove')
        corrframe.pack(side=tk.TOP, fill=tk.X)
        lbl = tk.Label(corrframe, text='Head-correction options')
        lbl.pack()

        # communication lists
        if self.shownetworking:
            netmsgframe = tk.Label(self.rightframe, text='Networkmsgframe goes here')#NetworkMessagesFrame()
            netmsgframe.pack()


    def createStatusLabel(self):
        """Put a label with some configurable text along the bottom"""
        self.bottomframe = tk.Frame(self.root, relief='sunken', bd=3)
        self.bottomframe.pack(side=tk.BOTTOM, fill=tk.X)
        labeltext = 'Example label'
        self.bottomlabel = tk.Label(self.bottomframe, text=labeltext)
        self.bottomlabel.pack(side=tk.RIGHT, fill=tk.X)

if __name__ == "__main__":
    main()
