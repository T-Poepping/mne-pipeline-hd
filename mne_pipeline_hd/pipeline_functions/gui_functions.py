import os
import sys
from functools import partial
from os.path import exists, isdir, isfile, join
from subprocess import run

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDesktopWidget, QDialog, QFileDialog, QGridLayout,
                             QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
                             QPushButton, QStyleFactory, QTabWidget, QToolTip, QVBoxLayout, QWidget)

from pipeline_functions import operations_dict as opd, subject_organisation as suborg, utilities as ut
from basic_functions import io_functions as io


def sub_dict_selected(inst1, inst2, dict_path):
    choice = inst1.currentItem().text()
    existing_dict = suborg.read_sub_dict(dict_path)
    if choice in existing_dict:
        if existing_dict[choice] == 'None':
            # Kind of bulky, improvable
            enable_none_insert = True
            for i in range(inst2.count()):
                if inst2.item(i).text() == 'None':
                    enable_none_insert = False
            if enable_none_insert:
                inst2.addItem('None')
        try:
            it2 = inst2.findItems(existing_dict[choice], Qt.MatchExactly)[0]
            inst2.setCurrentItem(it2)
        except IndexError:
            pass


def sub_dict_assign(dict_path, list_widget1, list_widget2):
    choice1 = list_widget1.currentItem().text()
    choice2 = list_widget2.currentItem().text()
    if not isfile(dict_path):
        with open(dict_path, 'w') as sd:
            sd.write(f'{choice1}:{choice2}\n')
        print(f'{dict_path} created')

    else:
        existing_dict = suborg.read_sub_dict(dict_path)
        if choice1 in existing_dict:
            existing_dict[choice1] = choice2
        else:
            existing_dict.update({choice1: choice2})
        with open(dict_path, 'w') as sd:
            for key, value in existing_dict.items():
                sd.write(f'{key}:{value}\n')


def sub_dict_assign_none(dict_path, list_widget1):
    choice = list_widget1.currentItem().text()
    if not isfile(dict_path):
        with open(dict_path, 'w') as sd:
            sd.write(f'{choice}:None\n')
        print(f'{dict_path} created')

    else:
        existing_dict = suborg.read_sub_dict(dict_path)
        if choice in existing_dict:
            existing_dict[choice] = None
        else:
            existing_dict.update({choice: None})
        with open(dict_path, 'w') as sd:
            for key, value in existing_dict.items():
                sd.write(f'{key}:{value}\n')


def sub_dict_assign_all_none(inst, dict_path, list_widget1):
    reply = QMessageBox.question(inst, 'Assign None to All?', 'Do you really want to assign none to all?',
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
        all_items = dict()
        for i in range(list_widget1.count()):
            all_items.update({list_widget1.item(i).text(): None})
        if not isfile(dict_path):
            with open(dict_path, 'w') as sd:
                for key, value in all_items.items():
                    sd.write(f'{key}:{value}\n')
        else:
            with open(dict_path, 'w') as sd:
                for key, value in all_items.items():
                    sd.write(f'{key}:{value}\n')
    else:
        print('Puh, pig haved')


def delete_last(dict_path):
    with open(dict_path, 'r') as dl:
        dlist = (dl.readlines())

    with open(dict_path, 'w') as dl:
        for listitem in dlist[:-1]:
            dl.write(str(listitem))


def read(dict_path):
    try:
        with open(dict_path, 'r') as rl:
            print(rl.read())
    except FileNotFoundError:
        print('file not yet created, assign some files')


# General Function for Assignment of MRI-Subject and ERM-File
class SubDictDialog(QDialog):
    def __init__(self, main_win, mode):
        super().__init__(main_win)
        self.main_win = main_win
        self.layout = QGridLayout()
        self.mode = mode
        if mode == 'mri':
            self.setWindowTitle('Assign files to their MRI-Subject')
            self.path2 = main_win.mri_sub_list_path
            self.dict_path = main_win.sub_dict_path
            self.label2 = 'Choose a mri-subject'
        elif mode == 'erm':
            self.setWindowTitle('Assign files to their ERM-File')
            self.path2 = main_win.erm_list_path
            self.dict_path = main_win.erm_dict_path
            self.label2 = 'Choose a erm-file'

        self.init_ui()
        self.show()
        self.activateWindow()
        self.exec_()

    def init_ui(self):
        file_label = QLabel('Choose a file', self)
        second_label = QLabel(self.label2, self)

        self.layout.addWidget(file_label, 0, 0)
        self.layout.addWidget(second_label, 0, 1)
        # ListWidgets
        list_widget1 = QListWidget(self)
        list_widget2 = QListWidget(self)
        with open(self.main_win.file_list_path, 'r') as sl:
            for idx, line in enumerate(sl):
                list_widget1.insertItem(idx, line[:-1])
        with open(self.path2, 'r') as msl:
            for idx, line in enumerate(msl):
                list_widget2.insertItem(idx, line[:-1])

        # Response to Clicking
        list_widget1.itemClicked.connect(partial(sub_dict_selected, list_widget1, list_widget2, self.dict_path))

        self.layout.addWidget(list_widget1, 1, 0)
        self.layout.addWidget(list_widget2, 1, 1)
        # Add buttons
        bt_layout = QVBoxLayout()
        assign_bt = QPushButton('Assign', self)
        assign_bt.clicked.connect(partial(sub_dict_assign, self.dict_path, list_widget1, list_widget2))
        bt_layout.addWidget(assign_bt)

        none_bt = QPushButton('Assign None', self)
        none_bt.clicked.connect(partial(sub_dict_assign_none, self.dict_path, list_widget1))
        bt_layout.addWidget(none_bt)

        all_none_bt = QPushButton('Assign None to all')
        all_none_bt.clicked.connect(partial(sub_dict_assign_all_none, self, self.dict_path, list_widget1))
        bt_layout.addWidget(all_none_bt)

        read_bt = QPushButton('Read', self)
        read_bt.clicked.connect(partial(read, self.dict_path))
        bt_layout.addWidget(read_bt)

        delete_bt = QPushButton('Delete Last', self)
        delete_bt.clicked.connect(partial(delete_last, self.dict_path))
        bt_layout.addWidget(delete_bt)

        ok_bt = QPushButton('OK', self)
        ok_bt.clicked.connect(self.close)
        bt_layout.addWidget(ok_bt)

        self.layout.addLayout(bt_layout, 0, 2, 2, 1)
        self.setLayout(self.layout)


# Todo: Create BadChannelsSelect
class BadChannelsSelect(QDialog):
    def __init__(self, main_win):
        super().__init__(main_win)
        self.main_win = main_win
        self.file_list_path = main_win.file_list_path
        self.bad_dict = suborg.read_bad_channels_dict(self.main_win.bad_channels_dict_path)
        self.layout = QGridLayout()
        self.channel_count = 122
        self.bad_chkbts = {}

        self.initui()
        self.show()
        self.activateWindow()
        self.exec_()

    def initui(self):
        listwidget = QListWidget(self)
        self.layout.addWidget(listwidget, 0, 0, self.channel_count // 10, 1)
        with open(self.file_list_path, 'r') as sl:
            for idx, line in enumerate(sl):
                listwidget.insertItem(idx, line[:-1])
                if line[:-1] in self.bad_dict:
                    listwidget.item(idx).setBackground(QColor('green'))
                    listwidget.item(idx).setForeground(QColor('white'))
                else:
                    listwidget.item(idx).setBackground(QColor('red'))
                    listwidget.item(idx).setForeground(QColor('white'))

        # Make Checkboxes for channels
        for x in range(1, self.channel_count + 1):
            ch_name = f'MEG {x:03}'
            chkbt = QCheckBox(ch_name, self)
            self.bad_chkbts.update({ch_name: chkbt})
            r = 0 + (x - 1) // 10
            c = 1 + (x - 1) % 10
            self.layout.addWidget(chkbt, r, c)

        # Response to Clicking
        listwidget.itemClicked.connect(partial(self.bad_dict_selected, listwidget))

        # Add Buttons
        bt_layout = QVBoxLayout()
        assign_bt = QPushButton('Assign', self)
        assign_bt.clicked.connect(partial(self.bad_dict_assign, listwidget))
        bt_layout.addWidget(assign_bt)

        plot_bt = QPushButton('Plot Raw')
        plot_bt.clicked.connect(partial(self.plot_raw_bad, listwidget))
        bt_layout.addWidget(plot_bt)

        ok_bt = QPushButton('OK', self)
        ok_bt.clicked.connect(self.close)
        bt_layout.addWidget(ok_bt)

        self.layout.addLayout(bt_layout, 0, 11, self.channel_count // 10, 1)
        self.setLayout(self.layout)

    def bad_dict_selected(self, listwidget):
        # First clear all entries
        for bt in self.bad_chkbts:
            self.bad_chkbts[bt].setChecked(False)
        # Then load existing bads for choice
        name = listwidget.currentItem().text()
        if name in self.bad_dict:
            for bad in self.bad_dict[name]:
                self.bad_chkbts[bad].setChecked(True)

    def bad_dict_assign(self, listwidget):
        name = listwidget.currentItem().text()
        listwidget.currentItem().setBackground(QColor('green'))
        listwidget.currentItem().setForeground(QColor('white'))
        bad_channels = []
        second_list = []
        for ch in self.bad_chkbts:
            if self.bad_chkbts[ch].isChecked():
                bad_channels.append(ch)
                second_list.append(int(ch[-3:]))
        self.bad_dict.update({name: bad_channels})
        ut.dict_filehandler(name, 'bad_channels_dict', self.main_win.pscripts_path, values=second_list)

    def plot_raw_bad(self, listwidget):
        name = listwidget.currentItem().text()
        raw = io.read_raw(name, join(self.main_win.data_path, name))
        print(f'first: {raw.info["bads"]}')
        # Todo: Make online bad-channel-selection work (mnelab-solution?)
        raw.plot(n_channels=30, bad_color='red',
                 scalings=dict(mag=1e-12, grad=4e-11, eeg=20e-5, stim=1), title=name)
        print(f'second: {raw.info["bads"]}')
        self.bad_dict.update({name: raw.info['bads']})
        for ch in self.bad_dict[name]:
            self.bad_chkbts[ch].setChecked(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        self.settings = QSettings()
        self.platform = sys.platform

        self.app.setFont(QFont('Calibri', 10))

        self.setWindowTitle('MNE-Pipeline HD')
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self.general_layout = QGridLayout()
        self.centralWidget().setLayout(self.general_layout)
        QToolTip.setFont(QFont('SansSerif', 9))

        # Workaround for MAC menu-bar-focusing issue
        self.menuBar().setNativeMenuBar(False)

        # Attributes for class-methods
        # self.actions = dict()
        self.func_dict = dict()
        self.bt_dict = dict()
        self.make_it_stop = False
        self.lines = dict()
        self.project_box = None
        self.subsel_layout = QHBoxLayout()
        sub_sel_example = "Examples:\n" \
                          "'5' (One File)\n" \
                          "'1,7,28' (Several Files)\n" \
                          "'1-5' (From File x to File y)\n" \
                          "'1-4,7,20-26' (The last two combined)\n" \
                          "'1-20,!4-6' (1-20 except 4-6)\n" \
                          "'all' (All files in file_list.py)\n" \
                          "'all,!4-6' (All files except 4-6)"

        self.sub_sel_tips = {'which_file': f'Choose files to process!\n{sub_sel_example}',
                             'quality': f'Choose the quality!\n{sub_sel_example}',
                             'modality': f'Pinprick-specific\n{sub_sel_example}',
                             'which_mri_subject': f'Choose mri_files to process\n{sub_sel_example}',
                             'which_erm_file': f'Choose erm_files to process\n{sub_sel_example}',
                             'which_motor_erm_file': f'Pinprick-specific\n{sub_sel_example}'}

        # Call methods
        self.get_paths()
        self.make_paths()
        self.create_menu()
        self.make_project_box()
        self.subject_selection()
        self.make_func_bts()
        self.add_main_bts()
        self.change_style('Fusion')

        # Center Window
        # Necessary because frameGeometry is dependent on number of function-buttons
        newh = self.sizeHint().height()
        neww = self.sizeHint().width()
        self.setGeometry(0, 0, neww, newh)

        # Causes almost full-screen on mac
        # if 'darwin' in self.platform:
        #     self.setGeometry(0, 0, self.width() * self.devicePixelRatio(), self.height() * self.devicePixelRatio())

        # This is also possible but does not center a widget with height < 480
        # self.layout().update()
        # self.layout().activate()
        self.center()

        self.which_file = self.lines['which_file'].text()
        self.quality = self.lines['quality'].text()
        self.modality = self.lines['modality'].text()
        self.which_mri_subject = self.lines['which_mri_subject'].text()
        self.which_erm_file = self.lines['which_erm_file'].text()
        self.which_motor_erm_file = self.lines['which_motor_erm_file'].text()

    def get_paths(self):
        # Get home_path
        self.home_path = self.settings.value('home_path')
        if self.home_path is None:
            hp = QFileDialog.getExistingDirectory(self, 'Select a folder to store your Pipeline-Projects')
            if hp == '':
                self.close()
                raise RuntimeError('You canceled an important step, start over')
            else:
                self.home_path = str(hp)
                self.settings.setValue('home_path', self.home_path)
        else:
            if not isdir(self.home_path):
                hp = QFileDialog.getExistingDirectory(self, f'{self.home_path} not found!\n'
                                                            f'Select the folder where '
                                                            f'you store your Pipeline-Projects')
                if hp == '':
                    self.close()
                    raise RuntimeError('You canceled an important step, start over')
                else:
                    self.home_path = str(hp)
                    self.settings.setValue('home_path', self.home_path)
            else:
                pass

        # Get project_name
        self.project_name = self.settings.value('project_name')
        self.projects = [p for p in os.listdir(self.home_path) if isdir(join(self.home_path, p, 'data'))]
        if len(self.projects) == 0:
            self.project_name, ok = QInputDialog.getText(self, 'Project-Selection',
                                                         f'No projects in {self.home_path} found\n'
                                                         'Enter a project-name for your first project')
            if ok:
                self.projects.append(self.project_name)
                self.settings.setValue('project_name', self.project_name)
                self.make_paths()
            else:
                # Problem in Python Console, QInputDialog somehow stays in memory
                self.close()
                raise RuntimeError('You canceled an important step, start over')
        elif self.project_name is None or self.project_name not in self.projects:
            self.project_name = self.projects[0]
            self.settings.setValue('project_name', self.project_name)

        print(f'Home-Path: {self.home_path}')
        print(f'Project-Name: {self.project_name}')
        print(f'Projects-found: {self.projects}')

    def make_paths(self):
        # Initiate other paths
        self.project_path = join(self.home_path, self.project_name)
        self.orig_data_path = join(self.project_path, 'meg')
        self.data_path = join(self.project_path, 'data')
        self.erm_path = join(self.data_path, 'empty_room_data')
        self.subjects_dir = join(self.home_path, 'Freesurfer')
        self.pscripts_path = join(self.project_path, '_pipeline_scripts')
        self.file_list_path = join(self.pscripts_path, 'file_list.py')
        self.erm_list_path = join(self.pscripts_path, 'erm_list.py')
        self.motor_erm_list_path = join(self.pscripts_path, 'motor_erm_list.py')
        self.mri_sub_list_path = join(self.pscripts_path, 'mri_sub_list.py')
        self.sub_dict_path = join(self.pscripts_path, 'sub_dict.py')
        self.erm_dict_path = join(self.pscripts_path, 'erm_dict.py')
        self.bad_channels_dict_path = join(self.pscripts_path, 'bad_channels_dict.py')
        self.quality_dict_path = join(self.pscripts_path, 'quality.py')

        path_lists = [self.subjects_dir, self.orig_data_path, self.data_path, self.erm_path, self.pscripts_path]
        file_lists = [self.file_list_path, self.erm_list_path, self.motor_erm_list_path, self.mri_sub_list_path,
                      self.sub_dict_path, self.erm_dict_path, self.bad_channels_dict_path, self.quality_dict_path]

        for path in path_lists:
            if not exists(path):
                os.makedirs(path)
                print(f'{path} created')

        for file in file_lists:
            if not isfile(file):
                with open(file, 'w') as fl:
                    fl.write('')
                print(f'{file} created')

    def change_home_path(self):
        new_home_path = QFileDialog.getExistingDirectory(self, 'Change folder to store your Pipeline-Projects')
        if new_home_path is '':
            pass
        else:
            self.home_path = new_home_path
            self.settings.setValue('home_path', self.home_path)
            self.get_paths()
            self.update_project_box()

    def add_project(self):
        project, ok = QInputDialog.getText(self, 'Project-Selection',
                                           'Enter a project-name for a new project')
        if ok:
            self.project_name = project
            self.settings.setValue('project_name', self.project_name)
            self.project_box.addItem(project)
            self.project_box.setCurrentText(project)
            self.make_paths()
        else:
            pass

    def make_project_box(self):
        proj_layout = QVBoxLayout()
        self.project_box = QComboBox()
        for project in self.projects:
            self.project_box.addItem(project)
        self.project_box.currentTextChanged.connect(self.change_project)
        self.project_box.setCurrentText(self.project_name)
        proj_box_label = QLabel('<b>Project:<b>')
        proj_layout.addWidget(proj_box_label)
        proj_layout.addWidget(self.project_box)
        self.subsel_layout.addLayout(proj_layout)

    def change_project(self, project):
        self.project_name = project
        self.settings.setValue('project_name', self.project_name)
        print(self.project_name)
        self.make_paths()

    def update_project_box(self):
        self.project_box.clear()
        for project in self.projects:
            self.project_box.addItem(project)

    # Todo Mac-Bug Menu not selectable
    def create_menu(self):
        # # Project
        # project_menu = QMenu('Project')
        # project_group = QActionGroup(self)
        # self.menuBar().addMenu(project_menu)
        #
        # for project in self.projects:
        #     action = QAction(project, self)
        #     action.setCheckable(True)
        #     action.triggered.connect(partial(self.change_project, project))
        #     project_group.addAction(action)
        #     print(f'Added {project}-action')
        #     project_menu.addAction(action)
        #     if project == self.project_name:
        #         action.toggle()
        # setting_menu.addAction('Add Project', self.add_project)
        # # Todo: Separator Issue
        # # project_menu.insertSeparator(self.actions['Add_Project'])

        # Input
        input_menu = self.menuBar().addMenu('Input')

        input_menu.addAction('Add Files', partial(suborg.add_files, self.file_list_path,
                                                  self.erm_list_path,
                                                  self.motor_erm_list_path,
                                                  self.data_path, self.orig_data_path))
        input_menu.addAction('Add MRI-Subject',
                             partial(suborg.add_mri_subjects, self.subjects_dir,
                                     self.mri_sub_list_path, self.data_path))
        input_menu.addAction('Assign File --> MRI-Subject',
                             partial(SubDictDialog, self, 'mri'))
        input_menu.addAction('Assign File --> ERM-File',
                             partial(SubDictDialog, self, 'erm'))
        input_menu.addAction('Assign Bad-Channels --> File',
                             partial(BadChannelsSelect, self))
        # Setting
        setting_menu = self.menuBar().addMenu('Settings')
        setting_menu.addAction('Dark-Mode', self.dark_mode).setCheckable(True)
        setting_menu.addAction('Full-Screen', self.full_screen).setCheckable(True)
        setting_menu.addAction('Change Home-Path', self.change_home_path)
        setting_menu.addAction('Add Project', self.add_project)
        # About
        about_menu = self.menuBar().addMenu('About')
        about_menu.addAction('Update Pipeline', self.update_pipeline)
        about_menu.addAction('Update MNE-Python', self.update_mne)
        about_menu.addAction('About QT', self.about_qt)

    # Todo: Fix Dark-Mode
    def dark_mode(self, state):
        if state:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)
            self.app.setPalette(dark_palette)
            self.app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
        else:
            white_palette = QPalette()
            white_palette.setColor(QPalette.Window, QColor(255, 255, 255))
            white_palette.setColor(QPalette.WindowText, Qt.black)
            white_palette.setColor(QPalette.Base, QColor(255, 255, 255))
            white_palette.setColor(QPalette.AlternateBase, QColor(255, 255, 255))
            white_palette.setColor(QPalette.ToolTipBase, Qt.black)
            white_palette.setColor(QPalette.ToolTipText, Qt.black)
            white_palette.setColor(QPalette.Text, Qt.black)
            white_palette.setColor(QPalette.Button, QColor(255, 255, 255))
            white_palette.setColor(QPalette.ButtonText, Qt.black)
            white_palette.setColor(QPalette.BrightText, Qt.red)
            white_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            white_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            white_palette.setColor(QPalette.HighlightedText, Qt.white)
            self.app.setPalette(white_palette)
            self.app.setStyleSheet("QToolTip { color: #000000; background-color: #2a82da; border: 1px solid black; }")

    def full_screen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def subject_selection(self):
        # Todo: Default Selection for Lines, Tooltips for explanation, GUI-Button
        for t in self.sub_sel_tips:
            subsub_layout = QVBoxLayout()
            self.lines[t] = QLineEdit()
            self.lines[t].setPlaceholderText(t)
            self.lines[t].textChanged.connect(partial(self.update_subsel, t))
            self.lines[t].setToolTip(self.sub_sel_tips[t])
            label = QLabel(f'<b>{t}</b>')
            label.setTextFormat(Qt.RichText)
            subsub_layout.addWidget(label)
            subsub_layout.addWidget(self.lines[t])
            self.subsel_layout.addLayout(subsub_layout)
            # Get Selection from last run
            self.lines[t].setText(self.settings.value(t))

        self.general_layout.addLayout(self.subsel_layout, 0, 0)

    def update_subsel(self, t):
        setattr(self, t, self.lines[t].text())

    def change_style(self, style_name):
        self.app.setStyle(QStyleFactory.create(style_name))
        self.app.setPalette(QApplication.style().standardPalette())
        self.center()

    # Todo: Make Buttons more appealing
    def make_func_bts(self):
        tab_func_widget = QTabWidget()
        for f, v in opd.all_fs.items():
            self.func_dict.update({f: v})

        pre_func_dict = self.settings.value('func_checked')
        del_list = []
        if pre_func_dict is not None:
            for k in pre_func_dict:
                if k not in opd.all_fs:
                    del_list.append(k)
            if len(del_list) > 0:
                for d in del_list:
                    del pre_func_dict[d]
                    print(f'{d} from func_cache deleted')

            # Default selection from opd overwrites cache
            for f in self.func_dict:
                if f in pre_func_dict:
                    if not self.func_dict[f]:
                        self.func_dict[f] = pre_func_dict[f]
        for tab_name in opd.calcplot_fs:
            tab = QWidget()
            tab_func_layout = QGridLayout()
            r_cnt = 0
            c_cnt = 0
            r_max = 15
            for function_group in opd.calcplot_fs[tab_name]:
                if r_cnt > r_max:
                    r_cnt = 0
                label = QLabel(f'<b>{function_group}</b>', self)
                label.setTextFormat(Qt.RichText)
                tab_func_layout.addWidget(label, r_cnt, c_cnt)
                r_cnt += 1

                for function in opd.calcplot_fs[tab_name][function_group]:
                    pb = QPushButton(function, tab)
                    pb.setCheckable(True)
                    self.bt_dict[function] = pb
                    if self.func_dict[function]:
                        pb.setChecked(True)
                        self.func_dict[function] = 1
                    pb.toggled.connect(partial(self.select_func, function))
                    tab_func_layout.addWidget(pb, r_cnt, c_cnt)
                    r_cnt += 1
                    if r_cnt >= r_max:
                        c_cnt += 1
                        r_cnt = 0
            tab.setLayout(tab_func_layout)
            tab_func_widget.addTab(tab, tab_name)
        self.general_layout.addWidget(tab_func_widget, 1, 0)

    def select_func(self, function):
        if self.bt_dict[function].isChecked():
            self.func_dict[function] = 1
            print(f'{function} selected')
        else:
            print(f'{function} deselected')
            self.func_dict[function] = 0

    def add_main_bts(self):
        main_bt_layout = QHBoxLayout()

        clear_bt = QPushButton('Clear', self)
        start_bt = QPushButton('Start', self)
        stop_bt = QPushButton('Stop', self)

        main_bt_layout.addWidget(clear_bt)
        main_bt_layout.addWidget(start_bt)
        main_bt_layout.addWidget(stop_bt)

        clear_bt.clicked.connect(self.clear)
        start_bt.clicked.connect(self.start)
        # start_bt.clicked.connect(plot_test)
        stop_bt.clicked.connect(self.stop)

        self.general_layout.addLayout(main_bt_layout, 2, 0)

    def clear(self):
        for x in self.bt_dict:
            self.bt_dict[x].setChecked(False)
            self.func_dict[x] = 0

    def start(self):
        self.close()

    def stop(self):
        self.close()
        self.make_it_stop = True

    def update_pipeline(self):
        command = f"pip install --upgrade git+https://github.com/marsipu/mne_pipeline_hd.git#egg=mne_pipeline_hd"
        run(command, shell=True)

        msg = QMessageBox(self)
        msg.setText('Please restart the Pipeline-Program/Close the Console')
        msg.setInformativeText('Do you want to restart?')
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.exec_()

        if msg.Yes:
            sys.exit()
        else:
            pass

    def update_mne(self):
        msg = QMessageBox(self)
        msg.setText('You are going to update your conda-environment called mne, if none is found, one will be created')
        msg.setInformativeText('Do you want to proceed? (May take a while, watch your console)')
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.exec_()

        command_upd = "curl --remote-name " \
                      "https://raw.githubusercontent.com/mne-tools/mne-python/master/environment.yml; " \
                      "conda activate mne; " \
                      "conda env update --file environment.yml; pip install -r requirements.txt; " \
                      "conda install -c conda-forge pyqt=5.12"

        command_upd_win = "curl --remote-name " \
                          "https://raw.githubusercontent.com/mne-tools/mne-python/master/environment.yml & " \
                          "conda activate mne & " \
                          "conda env update --file environment.yml & pip install -r requirements.txt & " \
                          "conda install -c conda-forge pyqt=5.12"

        command_new = "curl --remote-name " \
                      "https://raw.githubusercontent.com/mne-tools/mne-python/master/environment.yml; " \
                      "conda env create --name mne --file environment.yml;" \
                      "conda activate mne; pip install -r requirements.txt; " \
                      "conda install -c conda-forge pyqt=5.12"

        command_new_win = "curl --remote-name " \
                          "https://raw.githubusercontent.com/mne-tools/mne-python/master/environment.yml & " \
                          "conda env create --name mne_test --file environment.yml & " \
                          "conda activate mne & pip install -r requirements.txt & " \
                          "conda install -c conda-forge pyqt=5.12"

        if msg.Yes:
            result = run('conda env list', shell=True, capture_output=True, text=True)
            if 'buba' in result.stdout:
                if sys.platform == 'win32':
                    command = command_upd_win
                else:
                    command = command_upd
                result2 = run(command, shell=True, capture_output=True, text=True)
                if result2.stderr != '':
                    print(result2.stderr)
                    if sys.platform == 'win32':
                        command = command_new_win
                    else:
                        command = command_new
                    result3 = run(command, shell=True, capture_output=True, text=True)
                    print(result3.stdout)
                else:
                    print(result2.stdout)
            else:
                print('yeah')
                if sys.platform == 'win32':
                    command = command_new_win
                else:
                    command = command_new
                result4 = run(command, shell=True)
                print(result4.stdout)
        else:
            pass

    def about_qt(self):
        QMessageBox.aboutQt(self, 'About Qt')

    def closeEvent(self, event):
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('home_path', self.home_path)
        self.settings.setValue('project_name', self.project_name)
        self.settings.setValue('func_checked', self.func_dict)
        for ln in self.lines:
            self.settings.setValue(ln, self.lines[ln].text())

        event.accept()


def plot_test():
    name = 'pp1a_256_b'
    save_dir = 'Z:/Promotion/Pin-Prick-Projekt/Daten/pp1a_256_b'
    r = io.read_raw(name, save_dir)
    r.plot()


# for testing
if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    # not working in PyCharm, needed for Spyder
    # app.lastWindowClosed.connect(app.quit)
    app.exec_()
    # win.close()
    make_it_stop = win.make_it_stop
    del app, win
    if make_it_stop:
        raise SystemExit(0)
    # sys.exit(app.exec_())
    # Proper way would be sys.exit(app.exec_()), but this ends the console with exit code 0
    # This is the way, when FunctionWindow acts as main window for the Pipeline and all functions
    # are executed within. Need to resolve plot-problem (memory error 1073741819 (0xC0000005)) before
