__author__ = 'Kristy'

"""
GUI for the static RTServer.
"""

# TODO: Future Dev: the rtserverGUI should show the timestamp of the last DF streamed
import tkinter as tk
from tkinter import filedialog as fd
import os, time


def main():
    """Show the GUI, firstly loading the file list based on the properties file, starting the server."""
    # get the list of files
    import scripts.ema_io.ema_staticserver.rtserver as rts
    import scripts.ema_shared.properties as pps
    files = []
    abspath = os.path.abspath(pps.mocap_list_of_files)
    with open(abspath, 'r') as f:
        for line in f:
            line = line.rstrip('\t\r\n ')
            if os.path.isfile(line) and line != '':
                files.append(os.path.abspath(line))
            else:
                print('Warning: filepath {} cannot be found, and is not shown in the GUI.'.format(line))

    # start the server
    server_thread, server = rts.initialise_server(datafile=files[0], loop=True)
    server_thread.start()

    # build the gui
    root = tk.Tk()
    root.geometry("720x360")
    icon = 'images/ti.ico'
    if os.path.isfile(icon):
        root.wm_iconbitmap(bitmap=icon) # hard coded location, gui must run in same directory
    root.title("Static server file selector")
    app = Application(files, server.change_datafile, None, server.change_loop, server, master=root)
    app.setFilelist(files)
    app.mainloop()


class Application(tk.Frame):
    """GUI root class."""
    def __init__(self, filelist, on_load_fn, on_quit_fn, toggle_fn, server_obj, master=None):
        tk.Frame.__init__(self, master)
        self.root = master
        self.pack()

        self.file_list = filelist
        self.running = ''
        self.on_load_fn = on_load_fn
        self.on_quit_fn = on_quit_fn
        self.on_toggle_fn = toggle_fn
        self.server_obj = server_obj

        self.gs = lambda x: x.rt_fns.status
        self.createWidgets()

    def setFilelist(self, filelist):
        """Set self.file_list attribute."""
        self.file_list = filelist

    def update_eof_status(self):
        """Show the status of the file."""
        self.statustext.config(text="File status: {}".format(self.gs(self.server_obj)))
        self.after(100, self.update_eof_status)

    def createWidgets(self):
        """Create the widgets that display the file list, scrollbar, buttons, labels etc."""
        # lines of text with stats:
        var_i = tk.StringVar()
        label = tk.Label(self, textvariable=var_i,)
        var_i.set("Select the motion-capture file that the server streams from.")
        label.pack(side="top", anchor=tk.W, expand=1)

        # list of files
        fm = tk.Frame(self)
        self.scrollbar = tk.Scrollbar(fm, orient="vertical")
        self.listbox = tk.Listbox(fm, selectmode='single', yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill=tk.BOTH, expand=True)
        self.listbox.pack(side="right", fill=tk.BOTH, expand=True)
        self.listbox.config(width=100)
        for i, fn in enumerate(self.file_list):
            self.listbox.insert(tk.END, fn)
        self.listbox.select_set(0) # sets the first element
        #self.listbox.pack(side="top",padx=0, fill=tk.BOTH, expand=1)
        fm.pack(anchor=tk.W, side="top",  fill=tk.BOTH, expand=1)

        fm = tk.Frame(self)
        # + and - buttons
        self.plus = tk.Button(fm, text='Add file to list', command=self.add_to_list)
        self.minus = tk.Button(fm, text='Remove file from list', command=self.remove_from_list)
        self.plus.pack(side="top",fill='x')
        self.minus.pack(side="top",fill='x')
        fm.pack(anchor=tk.W, side="top",  fill=tk.BOTH, expand=1)

        fm = tk.Frame(self, relief=tk.RIDGE, borderwidth=2)
        # lines of text with stats:
        self.status = tk.Label(fm, text='Default file running')
        self.status.pack(side="top", anchor=tk.W, fill=tk.X, expand=True)

        self.looptext = tk.Label(fm, text='Looping: {}'.format(self.server_obj.rt_fns.emulator_loop))
        self.looptext.pack(side="top", anchor=tk.W, fill=tk.X, expand=True)

        self.statustext = tk.Label(fm, text='File status: {}'.format(self.server_obj.rt_fns.status))
        self.statustext.after(10, func=self.update_eof_status)
        self.statustext.pack(side='top', anchor=tk.W, fill=tk.X, expand=True)

        fm.pack(anchor=tk.W, side="top",  fill=tk.BOTH, expand=1)

        fm = tk.Frame(self)
        # load file button
        self.load_file = tk.Button(fm)
        self.load_file["text"] = "Load file"
        self.load_file["command"] = self.load_next_file
        self.load_file.pack(side="left",)

        self.loop_button = tk.Button(fm)
        self.loop_button["text"] = "Toggle looping"
        self.loop_button["command"] = self.toggle
        self.loop_button.pack(side="left")

        # close server button
        self.QUIT = tk.Button(fm, text="Quit server", fg="red", command=self.quit_all)
        self.QUIT.pack(padx=10, side="right",)
        fm.pack(anchor=tk.W, side="bottom",  fill=tk.BOTH, expand=1)

    def add_to_list(self):
        """Opens a dialog to select a file, adds the absolute filepath to the list."""
        new_fn = fd.askopenfilename()
        self.listbox.insert(tk.END, new_fn)
        self.file_list.append(new_fn)

    def remove_from_list(self):
        """Remove the selected filename from the list."""
        file_ind = self.listbox.curselection()
        file_name = self.file_list[file_ind[0]]
        if file_name != self.running:
            self.listbox.delete(file_ind)

    def quit_all(self):
        """Close the GUI and quit the server."""
        # todo: close server using cleaner methods, currently automatic
        print('Closing server')
        self.server_obj.server_close()
        print('Closing GUI')
        self.master.destroy()
        print('exiting')
        exit()

    def load_next_file(self):
        """Load the selected file as the one that is streamed from."""
        print('loading new file')
        file_ind = self.listbox.curselection()
        file_name = self.file_list[file_ind[0]]
        print('about to execute', self.on_load_fn, file_name)
        self.status.configure(text="Running file: {}".format(file_name))
        self.running = file_name
        return self.on_load_fn(file_name)

    def toggle(self):
        """Toggle looping behaviour for the streaming file."""
        looping = self.on_toggle_fn()
        self.looptext.configure(text="Looping: {}".format(looping))

if __name__ == "__main__":
    main()
