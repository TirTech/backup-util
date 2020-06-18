from tkinter import LabelFrame, LEFT, NW, BOTH, Entry, X, Checkbutton, Button, filedialog as filedialog
from ui.ui_model import UIModel


class DestinationFrame(LabelFrame):
    def __init__(self, root, model: UIModel):
        super().__init__(root, text="Destination", pady=10, padx=10)
        self.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)
        self.model = model

        self.txt_dest = Entry(self, textvariable=self.model.var_dest)
        self.txt_dest.pack(fill=X)

        self.chk_wrap = Checkbutton(self, text="Create Date Wrapper", variable=self.model.var_wrap, onvalue=True,
                                    offvalue=False)
        self.chk_wrap.pack()

        self.btn_dest_browse = Button(self, text="Browse", command=self.set_dest)
        self.btn_dest_browse.pack()

    def set_dest(self):
        dest = filedialog.askdirectory(title="Choose Destination")
        if dest is not None:
            self.model.var_dest.set(dest)
