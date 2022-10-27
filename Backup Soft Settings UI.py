"""Backup soft settings

Made by Leonid (https://github.com/G4m3-80ft)
"""

import os
import json
from time import sleep, strptime
from threading import Thread
from tkinter import StringVar, IntVar
from tkinter import Tk, Toplevel, Frame, Menu, Label, Checkbutton, OptionMenu, Entry, Button, Spinbox
from tkinter import messagebox as msgbox
from tkinter import filedialog
from tkinter.font import Font, families
from tkinter.colorchooser import askcolor

ACTION_TYPES: dict = {
    "archive": 'Archive',
    "archive_and_del": 'Archive & delete',
    "sync": 'Synchronize'
}
INV_ACTION_TYPES: dict = dict(
    (v, k) for k, v in ACTION_TYPES.items()
)
MONTHS: list = [
    "Jan", "Feb",
    "Mar", "Apr", "May",
    "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov",
    "Dec"
]

ui_config_path: str = 'UI/ui_config.json'
ui_settings: dict

if os.path.exists(ui_config_path):
    with open(ui_config_path) as f:
        ui_settings = json.load(f)
else:
    temp = Tk()
    ui_settings = {
        "Background color": '#d9d9d9',
        "Elements color": '#d9d9d9',
        "Text color": '#000',
        "Flash color": 'pink',
        "Font": families()[0]
    }
    temp.destroy()


def get_font(size: int = 14) -> Font:
    return Font(font=(ui_settings["Font"], size))


def flash(element, color: str = ui_settings["Flash color"], *, delay: float = 0.25, count: int = 2) -> None:
    def _flash(element, color: str, delay: float, count: int):
        default_color = element["bg"]
        for _ in range(count):
            element["bg"] = color
            sleep(delay)
            element["bg"] = default_color
            sleep(delay)

    Thread(target=_flash, args=(element, color, delay, count)).start()

    return None


def change_frame_state(frame, *, state: str) -> None:
    for i in frame.children:
        if any(j in i for j in ('label', 'entry', 'checkbutton', 'optionmenu', 'button')):
            frame.nametowidget(i)["state"] = state
        elif 'frame' in i:
            change_frame_state(frame.nametowidget(i), state=state)

    return None


class BoolVar(IntVar):
    def set(self, value):
        super().set(int(value))

    def get(self):
        return bool(super().get())


class ConfigureDialog:
    def __init__(self, *a, **kw):
        self.root = Toplevel(*a, **kw)
        self.root.title('Appearance settings')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry('500x250')

        main = Frame(self.root)
        main.grid(column=0, row=0, sticky='nesw')

        for i in range(3):
            main.columnconfigure(i, weight=1)
        for i in range(5):
            main.rowconfigure(i, weight=1)

        global ui_settings
        self.setting = StringVar()
        self.setting_menu = OptionMenu(
            main,
            self.setting,
            *tuple(ui_settings)[:-1]
        )
        self.setting_menu.grid(column=1, row=1, sticky='sew')

        self.setting_menu["font"] = get_font(6)
        menu = self.setting_menu["menu"]
        menu["font"] = get_font(6)
        for k, v in tuple(ui_settings.items())[:-1]:
            menu.entryconfigure(k, accelerator=v)

        font_menu = Menu(
            menu,
            font=get_font(6),
            fg=ui_settings["Text color"]
        )

        def get_font_menu(menu):
            font_tree = {}
            for f in sorted(families()):
                create_branch(font_tree, f.split())
            font = Menu(menu)
            add_font_tree(font, font_tree)
        
            return font
        
        def create_branch(d, keys):
            for k in keys:
                if k not in d:
                    d[k] = {}
                d = d[k]
        
            return dict
        
        def add_font_tree(menu, tree, font_name: list = None):
            if font_name is None:
                font_name = []
            for k, v in tree.items():
                font_name.append(k)
                if v:
                    m = Menu(menu)
                    menu.add_cascade(label=k, menu=m, font=get_font(6))
                    add_font_tree(m, tree[k], font_name)
                else:
                    f = ' '.join(font_name)
                    print(f)
                    menu.add_command(
                        label=k,
                        font=Font(
                            font=(
                                f,
                                6
                            )
                        ),
                        command=lambda f=f: ui_settings.update({"Font": f})
                    )
                    if k == tuple(tree.keys())[-1]:
                        font_name.clear()
                    else:
                        font_name.pop(-1)
        
        menu.add_cascade(label='Font', menu=get_font_menu(menu))

        Button(
            main,
            text='Choose color',
            font=get_font(6),
            command=self.change_color
        ).grid(column=1, row=2, sticky='new')

        Button(
            main,
            text='Ok',
            font=get_font(6),
            command=self.ok
        ).grid(column=1, row=3, sticky='e')

    def change_color(self) -> None:
        global ui_settings

        setting: str = self.setting.get()
        if not setting:
            flash(self.setting_menu)
            return None

        color: str = askcolor(
            parent=self.root,
            color=ui_settings[setting]
        )[1]
        if color is None:
            return None

        ui_settings[setting] = color

        self.setting_menu["menu"].entryconfigure(setting, accelerator=color)

    def ok(self):
        with open(ui_config_path, 'w') as f:
            json.dump(ui_settings, f)
        msgbox.showinfo('Info', 'Please, restart application to apply new settings.', parent=self.root)
        self.root.destroy()


class AddNewActionDialog:
    def __init__(self, *a, **kw):
        self.is_working: bool = True
        self.root = Toplevel(*a, **kw)
        self.root["bg"] = ui_settings["Background color"]
        self.root.title('Add new action')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry('600x300')

        main = Frame(
            self.root,
            bg=ui_settings["Background color"]
        )
        main.grid(column=0, row=0, sticky='nesw')

        col_conf: tuple = (
            # minsize, weight
            (10, 1),
            (0, 2),
            (0, 2),
            (10, 1)
        )
        for column, (minsize, weight) in enumerate(col_conf):
            main.columnconfigure(column, minsize=minsize, weight=weight)
        for i in range(4):
            main.rowconfigure(i, weight=1)

        self.settings = Frame(
            main,
            bg=ui_settings["Background color"]
        )
        self.settings.grid(column=0, row=0, columnspan=4, rowspan=2, sticky='nesw')

        for i in range(4):
            self.settings.columnconfigure(i, weight=1)
        for i in range(2):
            self.settings.rowconfigure(i, weight=1)

        Label(
            self.settings,
            text='Name',
            font=get_font(12),
            justify='left',
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"]
        ).grid(column=1, row=0, sticky='sw')

        self.name = StringVar()
        self.name_entry = Entry(
            self.settings,
            textvariable=self.name,
            font=get_font(10),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        )
        self.name_entry.grid(column=1, row=1, sticky='new')

        self.type = StringVar()
        self.type_menu = OptionMenu(
            self.settings,
            self.type,
            *ACTION_TYPES.values()
        )
        self.type_menu.grid(column=2, row=1, sticky='nw')

        self.type_menu.configure(
            font=get_font(5),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            width=max(len(i) for i in ACTION_TYPES.values())
        )
        menu = self.type_menu["menu"]
        menu.configure(
            font=get_font(5),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        )

        Button(
            main,
            text='Create',
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            command=self.validate
        ).grid(column=2, row=3, sticky='ne')

        Button(
            main,
            text='Cancel',
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            command=self.erase_and_destroy
        ).grid(column=3, row=3, padx=5, sticky='nw')

        self.root.bind_all('<Return>', self.validate)
        self.root.bind_all('<Escape>', self.erase_and_destroy)

    def get(self):
        return self.name.get(), self.type.get()

    def validate(self):
        name: str = self.name.get()
        type_: str = self.type.get()

        if name and type_:
            self.root.destroy()
            self.is_working = False

        if not name:
            flash(self.name_entry)
        if not type_:
            flash(self.type_menu)

        return None

    def erase_and_destroy(self):
        self.name.set('')
        self.type.set('')
        self.root.destroy()
        self.is_working = False


class Root:
    def __init__(self, *a, **kw):
        self.root = Tk(*a, **kw)
        self.root["bg"] = ui_settings["Background color"]
        self.title = 'Backup Soft Settings'
        self.root.title(f'{self.title} - config.json')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.option_add('*Dialog.msg.font', f'"{ui_settings["Font"]}" 8')

        self.setup_menu()
        
        self.setup_main()

        Label(
            self.root,
            text='Made by Leonid (github.com/G4m3_80ft)',
            fg='grey',
            bg=ui_settings["Background color"],
            font=get_font(4),
            justify='right'
        ).grid(column=0, row=1, sticky='se')

    def setup_menu(self):
        menubar = Menu(
            self.root,
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"]
        )
        self.root["menu"] = menubar

        self.setup_file(menubar)
        self.setup_options(menubar)
        self.setup_about(menubar)

    def setup_file(self, menubar):
        self.file = File()

        file_menu = Menu(
            menubar,
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"]
        )
        menubar.add_cascade(menu=file_menu, label='File', font=get_font(8))

        menu: tuple = (
            # label, command, accelerator, event
            ('New', lambda: self.file_wrapper(self.file.new), 'Ctrl+N', '<Control-n>'),
            ('sep', None, None, None),
            ('Open...', lambda: self.file_wrapper(self.file.open), 'Ctrl+O', '<Control-o>'),
            ('Save', lambda: self.file_wrapper(self.file.save), 'Ctrl+S', '<Control-s>'),
            ('Save as..', lambda: self.file_wrapper(self.file.save_as), 'Ctrl+Shift+S', '<Control-Shift-s>'), 
        )
        for label, command, accelerator, event in menu:
            if label == 'sep':
                file_menu.add_separator()
                continue
            file_menu.add_command(label=label, command=command, accelerator=accelerator)
            self.root.bind_all(event, command)

    def setup_options(self, menubar) -> None:
        options_menu = Menu(
            menubar,
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"]
        )
        menubar.add_cascade(menu=options_menu, label='Options', font=get_font(8))
        options_menu.add_command(label='Configure...', command=self.configure)

    @staticmethod
    def setup_about(menubar) -> None:
        help_menu = Menu(
            menubar,
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"]
        )
        menubar.add_cascade(menu=help_menu, label='Help', font=get_font(8))
        help_menu.add_command(
            label='About',
            command=lambda: msgbox.showinfo('About', 'Made by Leonid\n(github.com/G4m3_80ft)')
        )

    def setup_main(self) -> None:
        self.main = Frame(
            self.root,
            borderwidth=5,
            relief='ridge',
            bg=ui_settings["Background color"]
        )
        self.main.grid(column=0, row=0, sticky='nesw')

        for i in range(11):
            self.main.rowconfigure(i, weight=1)
        for column in range(4):
            self.main.columnconfigure(column, weight=1)

        names: list = []
        types: list = []
        for action in self.file.data["config"]:
            action_type = tuple(action)[0]
            action_name = action[action_type]["name"]
            names.append(f'{action_name}')
            types.append(f'{ACTION_TYPES[action_type]}')

        self.selected_action = StringVar()
        self.action_menu = OptionMenu(
            self.main,
            self.selected_action,
            *names,
            command=self.update_info
        )
        self.action_menu.grid(column=1, row=1,
                              columnspan=2,
                              sticky='w')

        self.action_menu.configure(
            font=get_font(6),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        )
        menu = self.action_menu["menu"]
        menu.configure(
            font=get_font(6),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        )
        for name, t in zip(names, types):
            menu.entryconfigure(name, accelerator=t)
        menu.add_command(
            label='New',
            accelerator='...',
            command=self.add_action
        )

        action_settings = Frame(
            self.main,
            bg=ui_settings["Background color"]
        )
        action_settings.grid(column=0, row=2,
                             columnspan=4, rowspan=2,
                             sticky='nesw')

        for i in range(4):
            action_settings.columnconfigure(i, weight=1)
        for i in range(2):
            action_settings.rowconfigure(i, weight=1)

        Label(
            action_settings,
            text='Name',
            font=get_font(12),
            justify='left',
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"]
        ).grid(column=1, row=0, sticky='sw')

        self.action_name = StringVar()
        Entry(
            action_settings,
            textvariable=self.action_name,
            font=get_font(10),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            width=11,
            validate='key',
            validatecommand=self.update_ui
        ).grid(column=1, row=1, sticky='new')

        self.action_type = StringVar()
        action_type_menu = OptionMenu(
            action_settings,
            self.action_type,
            *ACTION_TYPES.values(),
            command=self.update_ui
        )
        action_type_menu.grid(column=2, row=1, sticky='new')
        action_type_menu.configure(
            font=get_font(5),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            width=max(len(i) for i in ACTION_TYPES.values())
        )
        action_type_menu["menu"].configure(
            font=get_font(5),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        )

        datetime_settings = Frame(
            self.main,
            bg=ui_settings["Background color"]
        )
        datetime_settings.grid(column=0, row=4,
                               columnspan=4, rowspan=2,
                               sticky='nesw')

        for i in range(3):
            datetime_settings.rowconfigure(i, weight=1)
        for i in range(4):
            datetime_settings.columnconfigure(i, weight=1)

        Label(
            datetime_settings,
            text='Date & Time',
            font=get_font(12),
            justify='left',
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"]
        ).grid(column=1, row=0, sticky='sw')

        date_settings = Frame(
            datetime_settings,
            bg=ui_settings["Background color"]
        )
        date_settings.grid(column=1, row=1,
                           sticky='nw')

        date_settings.rowconfigure(0, weight=1)
        for i in range(5):
            date_settings.columnconfigure(i, weight=1)

        day = StringVar()
        Spinbox(
            date_settings,
            width=2,
            textvariable=day,
            state='readonly',
            values=['--'] + list(range(31, 0, -1)),
            wrap=True,
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            repeatinterval=50
        ).grid(column=0, row=0)

        Label(
            date_settings,
            text='/',
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        ).grid(column=1, row=0)

        months: list = ['---'] + list(
            reversed(MONTHS)
        )
        month = StringVar()
        Spinbox(
            date_settings,
            width=3,
            textvariable=month,
            state='readonly',
            values=months,
            wrap=True,
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            repeatinterval=50
        ).grid(column=2, row=0)

        Label(
            date_settings,
            text='/',
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        ).grid(column=3, row=0)

        year = StringVar()
        Spinbox(
            date_settings,
            width=4,
            textvariable=year,
            state='readonly',
            values=['----'] + list(range(3000, 2000, -1)),
            wrap=True,
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            repeatinterval=50
        ).grid(column=4, row=0)

        time_settings = Frame(
            datetime_settings,
            bg=ui_settings["Background color"]
        )
        time_settings.grid(column=2, row=1,
                           sticky='ne')

        time_settings.rowconfigure(0, weight=1)
        for i in range(5):
            time_settings.columnconfigure(i, weight=1)

        hour = StringVar()
        Spinbox(
            time_settings,
            width=2,
            textvariable=hour,
            state='readonly',
            values=['--'] + list(range(23, -1, -1)),
            wrap=True,
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            repeatinterval=50
        ).grid(column=0, row=0)

        Label(
            time_settings,
            text=':',
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"]
        ).grid(column=1, row=0)

        minute = StringVar()
        Spinbox(
            time_settings,
            width=2,
            textvariable=minute,
            state='readonly',
            values=['--'] + list(range(59, -1, -1)),
            wrap=True,
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            repeatinterval=50
        ).grid(column=2, row=0)

        Label(
            time_settings,
            text=':',
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"]
        ).grid(column=3, row=0)

        sec = StringVar()
        Spinbox(
            time_settings,
            width=2,
            textvariable=sec,
            state='readonly',
            values=['--'] + list(range(59, -1, -1)),
            wrap=True,
            font=get_font(8),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            repeatinterval=50
        ).grid(column=4, row=0)

        self.time_variables: dict = dict(
            zip(
                "%d %b %Y %H %M %S".split(),
                (
                    day, month, year,
                    hour, minute, sec
                )
            )
        )

        path_settings = Frame(
            self.main,
            bg=ui_settings["Background color"]
        )
        path_settings.grid(column=0, row=6,
                           columnspan=4, rowspan=2,
                           sticky='nesw')

        for i in range(4):
            path_settings.columnconfigure(i, weight=1)
        for i in range(4):
            path_settings.rowconfigure(i, weight=1)

        Label(
            path_settings,
            text='From',
            font=get_font(12),
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"],
            justify='left'
        ).grid(column=1, row=0, sticky='sw')

        self.from_ = StringVar()
        self.from_entry = Entry(
            path_settings,
            textvariable=self.from_,
            font=get_font(10),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            width=18,
            validate='key',
            validatecommand=self.update_ui
        )
        self.from_entry.grid(column=1, row=1,
                             sticky='new')

        Button(
            path_settings,
            text='Browse',
            font=get_font(5),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            command=lambda: self.from_.set(
                d
                if (d := filedialog.askdirectory())
                else self.from_.get())
        ).grid(column=2, row=1, sticky='nw')

        Label(
            path_settings,
            text='To',
            font=get_font(12),
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"],
            justify='left'
        ).grid(column=1, row=2, sticky='sw')

        self.to = StringVar()
        self.to_entry = Entry(
            path_settings,
            textvariable=self.to,
            font=get_font(10),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            width=18,
            validate='key',
            validatecommand=self.update_ui
        )
        self.to_entry.grid(column=1, row=3,
                           sticky='new')

        Button(
            path_settings,
            text='Browse',
            font=get_font(5),
            bg=ui_settings["Elements color"],
            fg=ui_settings["Text color"],
            command=lambda: self.to.set(
                d
                if (d := filedialog.askdirectory())
                else self.to.get()
            )
        ).grid(column=2, row=3, sticky='nw')

        self.on_start = BoolVar()
        Checkbutton(
            self.main,
            text='Do on start',
            variable=self.on_start,
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Background color"],
            command=self.update_ui
        ).grid(column=1, row=8, sticky='sw')

        buttons = Frame(
            self.main,
            bg=ui_settings["Background color"]
        )
        buttons.grid(column=2, row=9,
                     sticky='nesw')

        buttons.rowconfigure(0, weight=1)
        for i in range(2):
            buttons.columnconfigure(i, weight=1)

        self.apply_button = Button(
            buttons,
            text='Apply',
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            command=self.apply
        )
        self.apply_button.grid(column=0, row=0,
                               sticky='se')

        Button(
            buttons,
            text='Remove',
            font=get_font(8),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"],
            command=self.remove
        ).grid(column=1, row=0,
               sticky='sw')

        self.root.bind_all('<Return>', self.apply)

        change_frame_state(self.main, state='disabled')
        self.action_menu["state"] = 'normal'

    def file_wrapper(self, operation) -> None:
        operation()
        self.root.title(f'{self.title} - {self.file.filename}')

    def update_info(self, action_name) -> None:
        change_frame_state(self.main, state='normal')
        self.action_name.set(action_name)

        for action in self.file.data["config"]:
            action_type = tuple(action)[0]
            action_settings = action[action_type]
            if action_settings["name"] == action_name:
                self.action_type.set(ACTION_TYPES[action_type])
                
                self.on_start.set(action_settings["on_start"])

                time_settings = action_settings["time"]

                format_: str = tuple(time_settings.keys())[0]
                time_string: str = tuple(time_settings.values())[0]
                year, month, day, hour, minute, sec, _, _, _ = strptime(time_string, format_)

                for (f, var), val in zip(self.time_variables.items(), (day, float(month), year, hour, minute, sec)):
                    if f not in format_:
                        var.set('-' * len(var.get()))
                        continue
                    if isinstance(val, float):
                        var.set(MONTHS[int(val-1)])
                        continue
                    var.set(val)

                setup = action_settings["setup"]
                if action_type != 'sync':
                    self.from_.set(setup["from_path"])
                    self.to.set(setup["to_path"])
                else:
                    paths = setup["paths_to_sync"]
                    self.from_.set(paths[0])
                    self.to.set(paths[1])
                break

        self.apply_button["state"] = 'disabled'

        return None

    def update_action(self, *a) -> None:
        selected_action: str = self.selected_action.get()
        action_name: str = self.action_name.get()
        action_type: str = self.action_type.get()

        for action in self.file.data["config"]:
            selected_type: str = tuple(action)[0]
            if selected_action != action[selected_type]["name"]:
                continue

            action[selected_type]["name"] = action_name
            
            format_: list = []
            time: list = []
            for k, v in self.time_variables.items():
                if '-' in v.get():
                    continue
                format_.append(k)
                time.append(v.get())
            action[selected_type]["name"] = {
                " ".join(format_): ' '.join(time)
            }

            if action_name != 'sync':
                action[selected_type]["setup"] = {
                    "from_path": self.from_.get(),
                    "to_path": self.to.get()
                }
            else:
                action[selected_type]["setup"]["paths_to_sync"] = [
                    self.from_.get(),
                    self.to.get()
                ]
            action[selected_type]["on_start"] = self.on_start.get()
            if selected_type != INV_ACTION_TYPES[action_type]:
                self.file.data["config"].append(
                    {
                        INV_ACTION_TYPES[action_type]: action[selected_type].copy()
                    }
                )
                self.file.data["config"].remove(action[selected_action])

            break

        self.update_ui()
        menu = self.action_menu["menu"]
        menu.entryconfigure(selected_action, label=action_name, accelerator=action_type)
        self.selected_action.set(action_name)

        return None

    def update_ui(self, *a) -> True:
        self.apply_button["state"] = 'normal'
        self.root.title(f'{self.title} - {self.file.filename}*')

        if os.path.exists(self.to.get()):
            self.to_entry["bg"] = ui_settings["Elements color"]
        else:
            self.to_entry["bg"] = 'red'

        if os.path.exists(self.from_.get()):
            self.from_entry["bg"] = ui_settings["Elements color"]
        else:
            self.from_entry["bg"] = 'red'

        return True

    def add_action(self) -> None:
        Thread(target=self._add_action).start()

        return None

    def _add_action(self) -> None:
        dialog = AddNewActionDialog()

        while dialog.is_working:
            pass

        action_name, action_type = dialog.get()
        if not action_name:
            return None

        json_action_type: str = INV_ACTION_TYPES[action_type]
        action: dict = {
            json_action_type: {
                "name": action_name,
                "on_start": False,
                "time": {
                    "%d %b %H:%M:%S": '01 Jan 00:00:00'
                }
            }
        }

        if json_action_type in tuple(ACTION_TYPES)[:-1]:
            action[json_action_type]["setup"] = {
                "from_path": 'PATH',
                "to_path": 'PATH'
            }
        else:
            action[json_action_type]["setup"] = {
                "paths_to_sync": [
                     'PATH1',
                     'PATH2'
                ]
            }

        self.file.data["config"].append(action)

        menu = self.action_menu["menu"]
        names: list[str, ...] = []
        types: list[str, ...] = []
        for i in range(menu.index('end')):
            names.append(menu.entrycget(i, 'label'))
            types.append(menu.entrycget(i, 'accelerator'))
        names.append(action_name)
        types.append(action_type)

        self.action_menu.destroy()
        self.action_menu = OptionMenu(
            self.main,
            self.selected_action,
            *names,
            command=self.update_info
        )
        self.action_menu.grid(column=1, row=1, columnspan=2, sticky='w')
        self.action_menu.configure(
            font=get_font(6),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        )
        menu = self.action_menu["menu"]
        menu.configure(
            font=get_font(6),
            fg=ui_settings["Text color"],
            bg=ui_settings["Elements color"]
        )
        for name, t in zip(names, types):
            menu.entryconfigure(name, accelerator=t)
        menu.add_command(
            label='New',
            accelerator='...',
            command=Thread(target=self.add_action).start
        )
        self.selected_action.set(action_name)
        self.update_info(action_name)

        return None

    @staticmethod
    def configure() -> None:
        ConfigureDialog()

        return None

    def apply(self) -> None:
        self.update_action()
        msgbox.showinfo('Info', 'Settings applied succesfully.')
        self.apply_button["state"] = 'disabled'

        return None

    def remove(self) -> None:
        for action in self.file.data["config"]:
            if tuple(action.values())[0]["name"] != self.selected_action.get():
                continue

            self.file.data["config"].remove(action)
            self.action_menu["menu"].delete(self.selected_action.get())
            self.selected_action.set('')
            change_frame_state(self.main, state='disabled')
            self.action_menu["state"] = 'normal'

            break

        return None


class File:
    def __init__(self) -> None:
        self.msgbox_title: str = 'File operation'
        self.clear()

        return None

    def clear(self) -> None:
        self.dirname: str = os.getcwd()
        self.filename: str = 'config.json'
        self.data: dict = {
            "config": [
                {
                    "archive": {
                        "name": "archive",
                        "on_start": False,
                        "time": {
                                "%d %b %Y %H:%M:%S": "01 Jan 2000 00:00:00"
                        },
                        "setup": {
                            "from_path": "PATH",
                            "to_path": "PATH"
                        }
                    }
                },
                {
                    "archive_and_del": {
                        "name": "archive_and_del",
                        "on_start": True,
                        "time": {
                                "%d %b %Y %H:%M:%S": "01 Jan 2000 00:00:00"
                        },
                        "setup": {
                            "from_path": "PATH",
                            "to_path": "PATH"
                        }
                    }
                },
                {
                    "sync": {
                        "name": "sync",
                        "on_start": False,
                        "time": {
                                "%d %b %Y %H:%M:%S": "01 Jan 2000 00:00:00"
                        },
                        "setup": {
                            "paths_to_sync": [
                                "PATH1",
                                "PATH2"
                            ]
                        }
                    }
                }
            ]
        }

        return None

    def new(self) -> None:
        r = msgbox.askyesnocancel(self.msgbox_title, 'Do you want to save file before closing?')
        if r is None:
            return None
        elif r:
            self.save()

        self.clear()

        return None

    def open(self) -> None:
        path: str = filedialog.askopenfilename(
            defaultextension='.json',
            filetypes=[('JSON file', '.json')]
        )

        if not path:
            return None

        filename = os.path.basename(path)
        data_old = self.data

        try:
            with open(path) as file:
                self.data = json.load(file)
        except:
            msgbox.showerror(self.msgbox_title, f'Failed to open file "{filename}"!')
            raise

        if not self.is_valid():
            msgbox.showerror(self.msgbox_title, f'File "{filename}" is not valid!')
            self.data = data_old

        self.dirname, self.filename = os.path.split(path)

        return None

    def is_valid(self) -> bool:
        types: tuple = ("archive", "archive_and_del", "sync")
        setting_names: tuple = ("name", "on_start", "time", "setup")

        if not isinstance(self.data, dict):
            msgbox.showerror(self.msgbox_title, 'Invalid config: dict (JS object) expected!')
            return False
        elif "config" not in self.data.keys():
            msgbox.showerror(self.msgbox_title, 'Invalid config: no "config" key!')
            return False

        for action in self.data["config"]:
            if not isinstance(action, dict):
                msgbox.showerror(self.msgbox_title, 'Invalid action: dict (JS object) expected!')
                return False
            elif len(action) != 1:
                msgbox.showerror(self.msgbox_title, 'Invalid action: unexpected length!')
                return False
            elif action_type := tuple(action)[0] not in ACTION_TYPES:
                msgbox.showerror(self.msgbox_title, f'Invalid action: unknown action ({action_type})!')
                return False
            for action_type in types:
                if action_type not in action:
                    continue
                action_settings: dict = action[action_type]
                if not isinstance(action_settings, dict):
                    msgbox.showerror(self.msgbox_title, f'Invalid action "{action_type}" settings: '
                                     'dict (JS object) expected')
                    return False
                elif len(action_settings) != 4:
                    msgbox.showerror(self.msgbox_title, f'Invalid action "{action_type}" settings: '
                                     'unexpected length')
                    return False
                elif set(action_settings) != set(setting_names):
                    msgbox.showerror(self.msgbox_title, f'Invalid action "{action_type}" settings: '
                                     f'wrong keys: {tuple(action_settings)}')
                    return False

        return True

    def save(self) -> None:
        if not os.path.exists(self.dirname + os.sep + self.filename):
            self.save_as()

        try:
            with open(self.dirname + os.sep + self.filename, 'w') as file:
                json.dump(self.data, file)
        except:
            msgbox.showerror(self.msgbox_title, f'Failed to save file "{self.filename}"!')
            raise

        msgbox.showinfo(self.msgbox_title, f'File "{self.filename}" saved succesfully.')

        return None

    def save_as(self) -> None:
        path: str = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON file', '.json')],
            initialfile=self.filename,
            initialdir=self.dirname
        )

        if not path:
            return None

        self.dirname, self.filename = os.path.split(path)

        self.save()

        return None


Root().root.mainloop()
