
from PyQt5 import QtWidgets, QtGui
import subprocess
from subprocess import call, check_output, CalledProcessError, DEVNULL, PIPE
from io import StringIO
import os, re

def check_output(cmd, **kw):
    kw['stdin'] = PIPE
    kw['stderr'] = DEVNULL
    if hasattr(subprocess, 'STARTUPINFO'):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        kw['startupinfo'] = si
        kw['env'] = os.environ
    else:
        kw['shell'] = True
    return subprocess.check_output(cmd, **kw)

def reldir(fname):
    dirname = os.path.dirname(fname) or '.'
    return os.path.relpath(dirname, os.getcwd())

def gitTestFile(fname):
    path = reldir(fname)
    if re.match(r"^http[s]?://", fname):
        return False
    try:
        res = check_output("git -C {} ls-files --error-unmatch {}".format(path, os.path.basename(fname)))
    except FileNotFoundError:
        res = False
    except CalledProcessError:
        res = False
    else:
        res = True
    return res

class GitSupport():
    def __init__(self, fname):
        self.path = reldir(fname)
        self.fname = os.path.basename(fname)
        res = check_output("git -C {} branch -a".format(self.path)).decode('utf-8')
        self.branches = []
        for x in res.splitlines():
            b = x[2:].strip()
            if x[0] == "*":
                self.currbranch = b
            self.branches.append(b)

    def getfileat(self, branch, modifier):
        if modifier is None or modifier == "":
            rev = branch
        else:
            rev = branch + "@{" + modifier + "}"
        res = check_output('git -C {} show "{}:./{}"'.format(self.path, rev, self.fname)).decode('utf-8')
        return res

class GitToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super(GitToolBar, self).__init__(parent)
        self.diffAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("stock_shuffle"), "&Diff")
        self.diffAction.triggered.connect(self.diffActionChanged)
        self.diffAction.setCheckable(True)
        self.downAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("down"), "&Next")
        self.downAction.triggered.connect(parent.nextDiff)
        self.upAction = QtWidgets.QAction(QtGui.QIcon.fromTheme("up"), "&Previous")
        self.upAction.triggered.connect(parent.lastDiff)
        self.branch = QtWidgets.QComboBox(self)
        self.branchLabel = QtWidgets.QLabel("Branch", self)
        self.version = QtWidgets.QLineEdit(self)
        self.version.setPlaceholderText("branch modifier")
        self.version.setMaximumWidth(200)
        self.versionLabel = QtWidgets.QLabel("Version", self)
        self.version.returnPressed.connect(self.diffAction.trigger)
        self.addWidget(self.branchLabel)
        self.addWidget(self.branch)
        self.addWidget(self.version)
        self.addWidget(self.versionLabel)
        self.addAction(self.diffAction)
        self.addAction(self.downAction)
        self.addAction(self.upAction)
        self.hide()

    def changeFileName(self, fname, model, view):
        if not gitTestFile(fname):
            self.hide()
            self.model = None
            return
        self.model = model
        self.view = view
        self.gs = GitSupport(fname)
        self.branch.clear()
        self.branch.addItems(self.gs.branches)
        self.branch.setCurrentText(self.gs.currbranch)
        self.version.clear()
        self.show()

    def diffActionChanged(self):
        if self.model is None:
            self.diffAction.setChecked(False)
            return
        v = self.diffAction.isChecked()
        if v:
            s = self.gs.getfileat(self.branch.currentText(), self.version.text())
            if s:
                fh = StringIO(s)
                self.model.loadDiffCsv(fh)
                fh.close()
        else:
            self.model.dumpDiff()
        self.view.update()
