__author__ = 'Kristy'

"""
GUI for the static RTServer.
"""


import tkinter as tk
from tkinter import filedialog as fd
from tkinter import messagebox as mb
import os, time

import ematoblender.scripts.ema_io.ema_staticserver.rtserver as rts
import ematoblender.scripts.ema_shared.properties as pps


def extract_files_from_collectionpath(abspath):
    files = []
    if os.path.isfile(abspath):  # open the abspath of the file list
        with open(abspath, 'r') as f:
            for line in f:
                line = line.rstrip('\t\r\n ')  # verbatim filepath
                # open the filepath relative to project directory, this is the parent of the dataserver file
                projdir = os.path.abspath('../')
                print('Searching for relative paths from', projdir)
                relpath = os.path.normpath(projdir + './' + line)
                if os.path.isfile(relpath):
                    files.append(relpath)
                elif os.path.isfile(line) and line != '':
                    files.append(os.path.abspath(line))
                else:
                    print('Warning: filepath {} cannot be found, and is not shown in the GUI.'.format(line))
    else:
        print('Warning - the file list {} could not be found.'.format(abspath))
        return False

    return files


def main():
    """Show the GUI, firstly loading the file list based on the properties file, starting the server."""
    # get the list of files

    files = extract_files_from_collectionpath(os.path.abspath(pps.mocap_list_of_files))

    # start the server
    server_thread, server = rts.initialise_server(datafile=files[0], loop=True)
    server_thread.start()

    # build the gui
    root = tk.Tk()
    root.geometry("720x400")
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

        self.collection_path = os.path.abspath(pps.mocap_list_of_files)  # default collection
        self.collection_changed = False
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

    def save_list_changes(self):
        """Overwrite the self.collection_path file with the current file list"""
        f = open(self.collection_path, 'w')
        for p in self.file_list:
            f.write(p)
        f.close()

    def prompt_overwrite(self):
        return mb.askyesno("Save collection?", "Save the collection file, overwriting the old contents?")


    @staticmethod
    def pretty_print_microseconds(microsecstring):
        pad = 7
        if type(microsecstring) == int:  # if input is integer
            return '{:7.2f}'.format(microsecstring / 1000000)

        elif microsecstring.is_digit():  # if input is string
            if len(microsecstring) < 6:  # string is an integer
                microsecstring = microsecstring.zfill(6)
            return '{:>7}.{:.2}'.format(microsecstring[:-6], microsecstring[-6:])
        else:
            return microsecstring

    def update_eof_status(self):
        """Show the status of the file."""
        self.statustext.config(text='File status: {}\nFile time: {}'
                                   .format(self.server_obj.rt_fns.status,
                                           self.pretty_print_microseconds(self.server_obj.rt_fns.static_data.latest_timestamp)))
        self.after(10, self.update_eof_status)

    def change_collection(self):
        if self.collection_changed and self.prompt_overwrite():
            self.save_list_changes()
        selectedfile = os.path.abspath(fd.askopenfilename())
        print(selectedfile)
        if os.path.exists(selectedfile):
            try:
                file_list = extract_files_from_collectionpath(selectedfile)
            except:
                mb.showerror("Error", "An error occurred while reading the collection file.")
            else:
                if not file_list:
                    return # no valid file selected, do nothing

                if len(file_list) > 0:
                    self.file_list = file_list
                    self.collection_path = selectedfile
                    self.populate_listbox()
                else:
                    mb.showwarning("No files in collection", "Your selected collection doesn't contain any EMA files.")


    def populate_listbox(self):
        """Clear the listbox, insert all the files found in the selected collection"""
        self.listbox.delete(0, tk.END)
        for i, fn in enumerate(self.file_list):
            self.listbox.insert(tk.END, fn)
        self.listbox.select_set(0)  # sets the first element
        self.collection_changed = False

    def createWidgets(self):
        """Create the widgets that display the file list, scrollbar, buttons, labels etc."""
        # collection choice
        colframe = tk.Frame(self)
        colframe.pack(side=tk.TOP, fill=tk.X, expand=True)
        lbl = tk.Label(colframe, text='Showing collection file: {:40}'.format(self.collection_path))
        lbl.grid(row=1, column=1, sticky=tk.W)
        btn = tk.Button(colframe, text='Switch collection', command=self.change_collection)
        btn.grid(row=1, column=2, sticky=tk.E)

        # lines of text with stats:
        var_i = tk.StringVar()
        label = tk.Label(self, textvariable=var_i,)
        var_i.set("Select the motion-capture file that the server streams from:")
        label.pack(side="top", anchor=tk.W, expand=1)

        # list of files
        fm = tk.Frame(self)
        self.scrollbar = tk.Scrollbar(fm, orient="vertical")
        self.listbox = tk.Listbox(fm, selectmode='single', yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side="right", fill=tk.BOTH, expand=False)
        self.listbox.pack(side="right", fill=tk.BOTH, expand=True)
        self.listbox.config(width=100)

        self.populate_listbox()

        fm.pack(anchor=tk.W, side="top",  fill=tk.BOTH, expand=1)

        # + and - buttons
        fm = tk.Frame(self)
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

        self.statustext = tk.Label(fm, text='File status: {}\nFile time: {}'
                                   .format(self.server_obj.rt_fns.status,
                                           self.pretty_print_microseconds(self.server_obj.rt_fns.static_data.latest_timestamp)))
        self.statustext.after(10, func=self.update_eof_status)
        self.statustext.pack(side='top', anchor=tk.W, fill=tk.X, expand=True)

        fm.pack(anchor=tk.W, side="top",  fill=tk.BOTH, expand=1)

        btnframe = tk.Frame(self)
        # load file button
        self.load_file = tk.Button(btnframe, text="Load file", command=self.load_next_file)
        self.load_file.grid(row=1, column=1)

        self.loop_button = tk.Button(btnframe, text="Toggle looping", command=self.toggle)
        self.loop_button.grid(row=1, column=2)

        # close server button
        self.QUIT = tk.Button(btnframe, text="Quit server", fg="red", command=self.quit_all)
        self.QUIT.grid(row=1, column=5, columnspan=5, sticky=tk.E, padx=5)
        btnframe.pack(side='bottom', anchor=tk.E,  fill=tk.BOTH, expand=1)

    def add_to_list(self):
        """Opens a dialog to select a file, adds the absolute filepath to the list."""
        new_fn = fd.askopenfilename()
        self.listbox.insert(tk.END, new_fn)
        self.file_list.append(new_fn)
        self.collection_changed = True

    def remove_from_list(self):
        """Remove the selected filename from the list."""
        file_ind = self.listbox.curselection()
        file_name = self.file_list[file_ind[0]]
        if file_name != self.running:
            self.listbox.delete(file_ind)
            self.collection_changed = True

    def quit_all(self):
        """Close the GUI and quit the server."""
        if self.collection_changed and self.prompt_overwrite():
            self.save_list_changes()
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
