from tkinter import TOP, BOTH, PhotoImage
from tkinter.ttk import Frame, Notebook

from ttkthemes import ThemedTk

from backup_util.icon import icon
from .action_frame import ActionFrame
from .destination_frame import DestinationFrame
from .exclusion_frame import ExclusionFrame
from .manage_action_frame import ManageActionFrame
from .source_frame import SourceFrame
from .tree_frame import TreeFrame
from .ui_model import ConfigUIModel, ManageUIModel
from ..utils.datautils import get_data_path

custom_theme_folder = "backup_util/ttktheme_custom"
custom_theme_name = "arc_custom"


class GUI:
    def __init__(self):
        self.root = None

    def _setup(self):
        self.root.title("Backup Utility")
        img = PhotoImage(data=icon)
        self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        config_model = ConfigUIModel()
        manage_model = ManageUIModel()

        note = Notebook(self.root)
        self._setup_backup_tab(note, config_model)
        self._setup_manage_tab(note, manage_model)
        note.pack(fill=BOTH, expand=True)

    def _setup_manage_tab(self, note: Notebook, model: ManageUIModel):
        frm_manage_tab = Frame(note, padding=10)
        frm_manage_tab.pack(fill=BOTH, expand=True)

        TreeFrame(frm_manage_tab, model)
        ManageActionFrame(frm_manage_tab, model)

        note.add(frm_manage_tab, text="Folder Manager")

    def _setup_backup_tab(self, note: Notebook, model: ConfigUIModel):
        frm_backup_tab = Frame(note, padding=10)
        frm_backup_tab.pack(fill=BOTH, expand=True)

        frm_config = Frame(frm_backup_tab, padding=10)
        frm_config.pack(side=TOP, fill=BOTH, expand=True)

        SourceFrame(frm_config, model)
        ExclusionFrame(frm_config, model)
        DestinationFrame(frm_config, model)
        ActionFrame(frm_backup_tab, model)

        frm_backup_tab.pack(fill=BOTH, expand=True)

        note.add(frm_backup_tab, text="Backup Configurer")

    def start(self):
        self.root = ThemedTk(themebg=True)
        self.root.tk.eval("source {}/pkgIndex.tcl".format(get_data_path(custom_theme_folder)))
        self.root.set_theme(custom_theme_name)
        # self.root.set_theme("arc")
        # self.root.set_theme_advanced("arc", brightness=1, saturation=1.0, hue=1,
        #     preserve_transparency=True, output_dir=custom_theme_folder, advanced_name=custom_theme_name
        # )
        self._setup()
        self.root.mainloop()
