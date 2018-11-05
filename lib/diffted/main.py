#!/usr/bin/env python

from PyQt5 import QtWidgets, QtGui, QtCore
from diffted.tablemodel import DitTableModel
from diffted.tableview import DitTableView
from diffted.filter import FilterProxy
from diffted.dialogs import GithubCredentialsDialog
from diffted import gitsupport, urls
from collections import namedtuple
import yaml, os

class Main(QtWidgets.QMainWindow):
    def __init__(self, app):
        super(Main, self).__init__()
        self.app = app
        self.config = {}
        self.config_file = None
        self.recents = []
        self.credentials = {}
        self.fileSettings = {}
        self.readSettings()
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
        self.newAction('File/Open_Url', "Open &Url...", self.openurl, None)
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
        self._addMenuItems(fileMenu, 'File/', 'Open', 'Open_Url', 'Save', 'SaveAs', '|', 'OpenDiff', 'Quit')
        if len(self.recents) > 0:
            fileMenu.addSeparator()
            for i in range(len(self.recents)):
                a = fileMenu.addAction(self.recents[i])
                a.triggered.connect(lambda _,x=i: self.openfilename(self.recents[x]))
        viewMenu = menuBar.addMenu('&View')
        self._addMenuItems(viewMenu, 'View/', 'Sorted')

    def createToolBars(self):
        self.toolbars = {}
        self.toolbars['File'] = self.addToolBar('File')
        for an in ('Open', 'Save', 'SaveAs', 'OpenDiff'):
            self.toolbars['File'].addAction(self.actions['File/'+an])
        self.toolbars['Git'] = gitsupport.GitToolBar(self)
        self.addToolBar(self.toolbars['Git'])

    def openfile(self, e, fname=None):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV File", ".",
                        "CSV files (*.csv *.tsv);;YAML files (*.yaml)")
        if fname != "":
            self.openfilename(fname)

    def openurl(self, e, fname=None):
        if fname is None:
            fname, ok = QtWidgets.QInputDialog.getText(self, "Open URL", "Github URL:")
            if not ok:
                return
        self.openfilename(fname)

    def openfilename(self, fname):
        if fname.lower().endswith(".yaml"):
            self.loadconfig(fname)
            self.addRecent(fname)
        else:
            self.config_file = None
            self.config['datafile'] = fname
            self.addRecent(fname)
        fname = self.config['datafile']
        if self.config_file is not None:
            fname = os.path.join(os.path.dirname(self.config_file), fname)
        with urls.openFile(fname, 'r', gui=self) as fh:
            self.model.loadFromCsv(fh, self.config)
        self.toolbars['Git'].changeFileName(fname, self.model, self.tableView)
        fs = self.fileSettings.get(self.config['datafile'], None)
        if fs is not None:
            self.tableView.setFromSettings(fs)
            self.proxy.invalidateFilter()

    def loadconfig(self, fname):
        self.config_file = fname
        with urls.openFile(fname, 'r', gui=self) as f:
            self.config = yaml.load(f)
        if 'css' in self.config:
            self.app.setStyleSheet(self.app.styleSheet() + self.config['css'])      # bad code for reloading
        self.model.loadConfig(self.config)

    def savefile(self):
        fname = self.config['datafile']
        if fname is None or fname == "" or not self.model.dataChanged:
            return
        if self.config_file is not None:
            fname = os.path.join(os.path.dirname(self.config_file), fname)
        with urls.openFile(fname, 'w', config=self.config, encoding="utf-8", gui=self) as fh:
            self.model.saveCsv(fh)

    def saveasfile(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save CSV File", self.config['datafile'], 
                        "CSV files (*.csv *.tsv);;YAML files (*.yaml)")
        if fname.lower().endswith(".yaml"):
            self.config_file = fname
            with open(fname, "w") as fh:
                yaml.dump(self.config, fh)
            fname = os.path.join(os.path.dirname(fname), self.config['datafile'])

        if fname != "":
            if self.config_file is not None:
                fname = os.path.relpath(fname, start=os.path.dirname(self.config_file))
            self.config['datafile'] = fname
            self.savefile()

    def getGithubCredentials(self, githuburl, noui=False):
        cred = self.credentials.get(githuburl, None)
        if noui:
            return cred
        d = GithubCredentialsDialog(url=githuburl, **cred)
        if not d.runDialog(githuburl):
            return None
        cred = {}
        cred['username'] = d.username
        cred['pwd'] = d.password
        cred['log'] = d.log     # yeh yeh not really credentials, but on the form
        self.credentials[githuburl] = cred
        return cred

    def openDiffFile(self):
        diffname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open CSV File", ".", "CSV files (*.csv *.tsv)")
        if diffname != "":
            with open(diffname, encoding="utf-8") as f:
                self.model.loadDiffCsv(f)
            self.tableView.update()

    def busyStart(self):
        self.app.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

    def busyStop(self):
        self.app.restoreOverrideCursor()

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

    def addRecent(self, fname):
        if fname in self.recents:
            self.recents.pop(self.recents.index(fname))
        self.recents.insert(0, fname)
        while len(self.recents) > 10:
            self.recents.pop()

    def closeEvent(self, e):
        self.writeSettings()
        e.accept()

    def readSettings(self):
        settings = QtCore.QSettings("SIL", "diffted")

        settings.beginGroup("MainWindow")
        self.resize(settings.value("size", QtCore.QSize(500, 500)))
        settings.endGroup()

        num = settings.beginReadArray("recentFiles")
        for i in range(num):
            settings.setArrayIndex(i)
            self.recents.append(settings.value("filename"))
        settings.endArray()

        num = settings.beginReadArray("GithubCredentials")
        for i in range(num):
            settings.setArrayIndex(i)
            cred = {}
            url = settings.value("Url")
            cred['username'] = settings.value("username")
            cred['pwd'] = settings.value("password")
            self.credentials[url] = cred
        settings.endArray()

        num = settings.beginReadArray("FileSettings")
        for i in range(num):
            settings.setArrayIndex(i)
            fname = settings.value("fileName")
            colsizes = settings.value("columnWidths")
            numfilts = settings.beginReadArray("filters")
            filters = {}
            for j in range(numfilts):
                settings.setArrayIndex(j)
                colname = settings.value("colname")
                filterval = settings.value("filterValue")
                isreg = settings.value("isRegexp")
                ison = settings.value("enabled")
                filters[colname] = (filterval, isreg == 'true', ison == 'true')
            settings.endArray()
            fs = {}
            self.fileSettings[fname] = fs
            fs['colsizes'] = [int(x) for x in colsizes.split()]
            fs['filters'] = filters
        settings.endArray()

    def writeSettings(self):
        settings = QtCore.QSettings("SIL", "diffted")

        settings.beginGroup("MainWindow")
        settings.setValue("size", self.size())
        settings.endGroup()

        settings.beginWriteArray("recentFiles", len(self.recents))
        for i in range(len(self.recents)):
            settings.setArrayIndex(i)
            settings.setValue("filename", self.recents[i])
        settings.endArray()

        if len(self.credentials):
            settings.beginWriteArray("GithubCredentials")
            i = 0
            for k, v in self.credentials.items():
                settings.setArrayIndex(i)
                settings.setValue("Url", k)
                settings.setValue("username", v['username'])
                settings.setValue("password", v['pwd'])
            settings.endArray()

        if 'datafile' in self.config:
            self.fileSettings[self.config['datafile']] = self.tableView.getSettings()
        settings.beginWriteArray("FileSettings", len(self.fileSettings))
        i = 0
        for k, v in sorted(self.fileSettings.items()):
            settings.setArrayIndex(i)
            settings.setValue("fileName", k)
            settings.setValue("columnWidths", " ".join(str(x) for x in v['colsizes']))
            settings.beginWriteArray("filters", len(v['filters']))
            j = 0
            for jk, jv in v['filters'].items():
                settings.setArrayIndex(j)
                settings.setValue('colname', jk)
                settings.setValue('filterValue', jv[0])
                settings.setValue('isRegexp', jv[1])
                settings.setValue('enabled', jv[2])
                j += 1
            settings.endArray()
            i += 1
        settings.endArray()

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    mainWin = Main()
    mainWin.show()
    sys.exit(app.exec_())
