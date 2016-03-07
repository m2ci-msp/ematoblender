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
        self.tsvfilelocation = tk.StringVar()
        self.savetsv = tk.BooleanVar()
        self.wavfilelocation = tk.StringVar()
        self.savewav = tk.BooleanVar()

        saveframe = tk.Frame(self.leftframe, relief='groove', bd=2)
        saveframe.pack(fill=tk.X,)

        def set_tsvdir():
            self.tsvfilelocation.set(fd.askdirectory())

        def set_wavdir():
            self.wavfilelocation.set(fd.askdirectory())

        def set_tsvbtn():
            self.tsvbtn.config(state=tk.ACTIVE if self.savetsv.get() else tk.DISABLED)
            self.tsvlab.config(state=tk.ACTIVE if self.savetsv.get() else tk.DISABLED)

        def set_wavbtn():
            self.wavbtn.config(state=tk.ACTIVE if self.savewav.get() else tk.DISABLED)
            self.wavlab.config(state=tk.ACTIVE if self.savewav.get() else tk.DISABLED)

        tk.Label(saveframe, text="Save received TSV").grid(row=1, column=1)
        btn = tk.Checkbutton(saveframe, variable=self.savetsv, command=set_tsvbtn)
        btn.grid(row=1, column=2)

        self.tsvbtn = tk.Button(saveframe, text="Choose location", command=set_tsvdir, state=tk.DISABLED)
        self.tsvbtn.grid(row=1, column=3)
        self.tsvlab = tk.Label(saveframe, textvariable=self.tsvfilelocation)
        self.tsvlab.grid(row=1,column=4)

        tk.Label(saveframe, text="Record audio while streaming").grid(row=2, column=1)
        btn = tk.Checkbutton(saveframe, variable=self.savewav, command=set_wavbtn)
        btn.grid(row=2, column=2)

        self.wavbtn = tk.Button(saveframe, text="Choose location", command=set_wavdir, state=tk.DISABLED)
        self.wavbtn.grid(row=2, column=3)
        self.wavlab = tk.Label(saveframe, textvariable=self.wavfilelocation)
        self.wavlab.grid(row=2, column=4)

        # TODO: Choose which audio input


        # manual server calls
        callsframe = tk.Frame(self.leftframe, relief='groove', bd=2)
        callsframe.pack(fill=tk.X)
        self.allow_man_calls = tk.BooleanVar()
        manallow = tk.Checkbutton(callsframe, text="Allow manual calls to the data server",
                                  variable=self.allow_man_calls,
                                  command=self.update_disabled_buttons)
        manallow.grid(row=1, column=1) # TODO: Set overflow

        manbtn1 = tk.Button(callsframe, text='Single', state=tk.DISABLED)
        manbtn1.grid(row=2, column=1)
        manbtn2 = tk.Button(callsframe, text='Stream', state=tk.DISABLED)
        manbtn2.grid(row=2, column=2)
        manbtn3 = tk.Button(callsframe, text='Status', state=tk.DISABLED)
        manbtn3.grid(row=2, column=3)
        self.manual_buttons = [manbtn1, manbtn2, manbtn3]

        nt = NetworkTrafficFrame(self.leftframe)
        nt.pack()

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
        smoothframe = tk.Frame(self.rightframe, relief='groove', bd=2)
        smoothframe.pack()
        lbl = tk.Label(smoothframe, text='Apply rolling average by:')
        lbl.grid(row=1, column=1)
        lbl=tk.Checkbutton(smoothframe, text='ms')
        lbl.grid(row=2, column=1)
        e = tk.Entry(smoothframe)
        e.grid(row=2, column=2)
        lbl=tk.Checkbutton(smoothframe, text='frames')
        lbl.grid(row=2, column=3)
        e = tk.Entry(smoothframe)
        e.grid(row=2, column=4)


        # options for head-correction
        corrframe = tk.Frame(self.rightframe, relief='groove', bd=2)
        corrframe.pack(side=tk.TOP, fill=tk.X)
        self.hcmethod = tk.IntVar()

        hc1frame = tk.Frame(corrframe)
        hc1frame.grid(row=3, column=1)
        btn= tk.Button(hc1frame, text='Choose file', command=fd.askopenfile)
        btn.grid(row=1, column=1)
        btn= tk.Button(hc1frame, text='Choose file', command=fd.askopenfile)
        btn.grid(row=2, column=1)
        hc1frame.grid_remove()

        hc2frame = tk.Frame(corrframe)
        hc2frame.grid(row=3, column=1)
        btn= tk.Button(hc2frame, text='Choose file', command=fd.askopenfile)
        btn.grid(row=3, column=1)

        hc1frame.grid_remove()

        hc3frame = tk.Frame(corrframe)
        hc3frame.grid(row=3, column=1)
        btn= tk.Button(hc3frame, text='Start streaming', command=fd.askopenfile)
        btn.grid(row=3, column=2)
        hc3frame.grid_remove()

        def show_hcmethod():
            """What to show in the head-correction area based on the chosen head-correction method"""
            print('Trigger hcmethod', self.hcmethod.get())
            hc1frame.grid_remove()
            hc2frame.grid_remove()
            hc3frame.grid_remove()
            if self.hcmethod.get() == 1:
                hc1frame.grid()
            elif self.hcmethod.get() ==2:
                hc2frame.grid()
            else:
                hc3frame.grid()

        lbl = tk.Label(corrframe, text='Head-correction options')
        lbl.grid(row=1, column=1)
        c = tk.Radiobutton(corrframe, text="Pre-calculated", variable=self.hcmethod, value=1, command=show_hcmethod)
        c.grid(row=2, column=1)
        c = tk.Radiobutton(corrframe, text="Calculate from TSV file", variable=self.hcmethod, value=2, command=show_hcmethod)
        c.grid(row=2, column=2)
        c = tk.Radiobutton(corrframe, text="Record live", variable=self.hcmethod, value=3, command=show_hcmethod)
        c.grid(row=2, column=3)




        # TODO: Choose to perfoorm head correction
        # If yes, choose file with matrices
        # OR choose TSV file with recording
        # OR choose to do some live streaming

        # SHOW orientation


        nt = NetworkTrafficFrame(self.rightframe)
        nt.pack(expand=False)


    def createStatusLabel(self):
        """Put a label with some configurable text along the bottom"""
        self.bottomframe = tk.Frame(self.root, relief='sunken', bd=3)
        self.bottomframe.pack(side=tk.BOTTOM, fill=tk.X)
        labeltext = 'Example label'
        self.bottomlabel = tk.Label(self.bottomframe, text=labeltext)
        self.bottomlabel.pack(side=tk.RIGHT, fill=tk.X)


class NetworkTrafficFrame(tk.Frame):
    """Class that makes a frame with two side-by-side scrolling lists,
    Text that shows the content.
    Whole thing can be hidden on checkbox
    """
    def __init__(self, master=None):
        super().__init__(master)
        upperframe = tk.Frame(self)
        upperframe.pack(side=tk.TOP, fill=tk.X)
        leftframe = tk.Frame(upperframe)
        leftframe.pack(side=tk.LEFT)
        self.scrollbarleft = tk.Scrollbar(leftframe, orient='vertical')
        self.listboxleft = tk.Listbox(leftframe, selectmode='single', yscrollcommand=self.scrollbarleft.set)
        self.listboxleft.select_set(0)
        self.scrollbarleft.config(command=self.listboxleft.yview)
        self.scrollbarleft.pack(side='right', fill=tk.BOTH, expand=True)
        self.listboxleft.pack()

        rightframe = tk.Frame(upperframe)
        rightframe.pack(side=tk.LEFT, fill=tk.X)
        self.scrollbarright = tk.Scrollbar(rightframe, orient='vertical')
        self.listboxright = tk.Listbox(rightframe, selectmode='single', yscrollcommand=self.scrollbarright.set)
        self.listboxright.select_set(0)
        self.scrollbarright.config(command=self.listboxright.yview)
        self.scrollbarright.pack(side='right', fill=tk.BOTH, expand=True)
        self.listboxright.pack()

        lowerframe = tk.Frame(self)
        lowerframe.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.cantext = tk.StringVar().set('lblablajn')
        canvas = tk.Text(lowerframe, width=leftframe.winfo_width(), text=self.cantext)
        canvas.pack(side='left', fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    main()
