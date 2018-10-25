#!/usr/bin/env python

from PyQt5 import QtWidgets, QtGui, QtCore
from diffted.tablemodel import DitTableModel
from diffted.tableview import DitTableView
from diffted.filter import FilterProxy
from diffted import gitsupport, urls
from collections import namedtuple
import yaml

class Main(QtWidgets.QMainWindow):
    def __init__(self, app):
        super(Main, self).__init__()
        self.app = app
        self.config = {}
        self.config_file = None
        self.resize(500, 500)
        self.actions = {}
        self.tableView = DitTableView()
        self.model = DitTableModel(self.tableView)
        self.proxy = FilterProxy()
        self.proxy.setSourceModel(self.model)
        self.tableView.setModel(self.proxy)
        self.model.modelReset.connect(self.tableView.resetModel)
        self.setCentralWidget(self.tableView)
        self.mainActions()
        self.createMenu()
        self.createToolBars()

    def newAction(self, name, menu, fn, icon=None, shortcut=None, statustip=None, checkable=False):
        if icon is not None:
            a = QtWidgets.QAction(QtGui.QIcon.fromTheme(icon), menu)
        else:
            a = QtWidgets.QAction(menu)
        if fn is not None:
            a.triggered.connect(fn)
        if shortcut is not None:
            a.setShortcut(shortcut)
        if statustip is not None:
            a.setStatusTip(statustip)
        if checkable:
            a.setCheckable(True)
        self.actions[name] = a

    def mainActions(self):
        self.newAction('File/Open', "&Open...", self.openfile, "document-open")
        self.newAction('File/Save', "&Save", self.savefile, "document-save")
        self.newAction('File/SaveAs', "Save&As...", self.saveasfile, "document-save-as")
        self.newAction('File/Quit', "&Quit", QtWidgets.qApp.quit, "application-exit")
        self.newAction('File/OpenDiff', "Open&Diff...", self.openDiffFile, "stock_shuffle")
        # self.newAction('View/Sorted', "&Sorted", self.sort_changed, "view-sort-ascending", checkable=True)
        self.newAction('View/Sorted', "&Sorted", self.sort_changed, None, checkable=True)
    
    def _addMenuItems(self, menu, prefix, *entries):
        for an in entries:
            if an == '|':
                menu.addSeparator()
            else:
                menu.addAction(self.actions[prefix+an])

    def createMenu(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        self._addMenuItems(fileMenu, 'File/', 'Open', 'Save', 'SaveAs', '|', 'OpenDiff', 'Quit')
        viewMenu = menuBar.addMenu('&View')
        self._addMenuItems(viewMenu, 'View/', 'Sorted')

    def createToolBars(self):
        self.toolbars = {}
        self.toolbars['File'] = self.addToolBar('File')
        for an in ('Open', 'Save', 'SaveAs', 'OpenDiff'):
            self.toolbars['File'].addAction(self.actions['File/'+an])
        self.toolbars['Git'] = gitsupport.GitToolBar(self)
        self.addToolBar(self.toolbars['Git'])

    def openfile(self, fname=None):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV File", ".",
                        "CSV files (*.csv *.tsv);;YAML files (*.yaml)")
        if fname != "":
            self.openfilename(fname)

    def openfilename(self, fname):
        if fname.lower().endswith(".yaml"):
            self.loadconfig(fname)
        else:
            self.config['datafile'] = fname
        fname = self.config['datafile']
        with urls.openFile(fname, 'r', config=self.config) as fh:
            self.model.loadFromCsv(fh, self.config)
        self.toolbars['Git'].changeFileName(fname, self.model, self.tableView)

    def loadconfig(self, fname):
        self.config_file = fname
        with open(fname, encoding="utf-8") as f:
            self.config = yaml.load(f)
        if 'css' in self.config:
            self.app.setStyleSheet(self.app.styleSheet() + self.config['css'])      # bad code for reloading
        self.model.loadConfig(self.config)

    def savefile(self):
        fname = self.config['datafile']
        if fname is None or fname == "":
            return
        with urls.openFile(fname, 'w', config=self.config, encoding="utf-8") as fh:
            self.model.saveCsv(fh)

    def saveasfile(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save CSV File", self.config['datafile'], 
                        "CSV files (*.csv *.tsv);;YAML files (*.yaml)")
        if fname != "":
            self.config['datafile'] = fname
            self.savefile()

    def openDiffFile(self):
        diffname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV File", ".", "CSV files (*.csv *.tsv)")
        if diffname != "":
            with open(diffname, encoding="utf-8") as f:
                self.model.loadDiffCsv(f)
            self.tableView.update()

    def sort_changed(self):
        v = self.actions['View/Sorted'].isChecked()
        #self.actions['View/Sorted'].setChecked(v)
        #print("sorted switched to " + str(v))
        self.tableView.setSortingEnabled(v)
        if not v:
            self.tableView.model().sort(-1, 0)
        self.tableView.update()

    def nextDiff(self):
        ci = self.tableView.currentIndex()
        newi = self.model.nextDiffFrom(ci)
        if newi is not None:
            pi = self.proxy.mapFromSource(newi)
            self.tableView.setCurrentIndex(pi)
            self.tableView.setFocus()
            self.tableView.scrollTo(pi)

    def lastDiff(self):
        ci = self.tableView.currentIndex()
        newi = self.model.lastDiffFrom(ci)
        if newi is not None:
            pi = self.proxy.mapFromSource(newi)
            self.tableView.setCurrentIndex(pi)
            self.tableView.scrollTo(pi)
            self.tableView.setFocus()
        

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    mainWin = Main()
    mainWin.show()
    sys.exit(app.exec_())
