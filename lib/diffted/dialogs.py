
from PyQt5 import QtWidgets, QtGui

class GithubCredentialsDialog(object):
    def __init__(self, url="", username="", pwd="", log=""):
        self.url = url
        self.username = username
        self.password = pwd
        self.log = log

    def runDialog(self, url):
        dlg = QtWidgets.QDialog()
        dlgVBox = QtWidgets.QVBoxLayout()
        urlLabel = QtWidgets.QLabel("Github Project Url: " + url)
        dlgVBox.addWidget(urlLabel)
        dlg.setLayout(dlgVBox)
        self.widgets = {}
        self.hboxes = {}
        self.labels = {}
        self.inputs = {}

        fields = (("username", "Username or API Key:"),
                  ("password", "Password:"),
                  ("log", "History statement:"))

        for k, v in fields:
            self.widgets[k] = QtWidgets.QWidget(dlg)
            self.widgets[k].setStyleSheet("margin: 0 0 0 0")
            self.hboxes[k] = QtWidgets.QHBoxLayout()
            self.labels[k] = QtWidgets.QLabel(v+" ")
            self.inputs[k] = QtWidgets.QLineEdit(getattr(self, k, ""), dlg)
            self.hboxes[k].addWidget(self.labels[k])
            self.hboxes[k].addWidget(self.inputs[k])
            if k != "log":
                self.inputs[k].setEchoMode(QtWidgets.QLineEdit.PasswordEchoOnEdit)
                button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme('dialog-password'),"")
                button.setCheckable(True)
                button.toggled.connect(lambda c,k=k: self.inputs[k].setEchoMode(0 if c else QtWidgets.QLineEdit.PasswordEchoOnEdit))
                self.hboxes[k].addWidget(button)
            self.widgets[k].setLayout(self.hboxes[k])
            dlgVBox.addWidget(self.widgets[k])

        buttonsWidget = QtWidgets.QWidget(dlg)
        buttonsHBox = QtWidgets.QHBoxLayout()
        buttonsCancel = QtWidgets.QPushButton("Cancel")
        buttonsOK = QtWidgets.QPushButton("OK")
        buttonsHBox.addStretch()
        buttonsHBox.addWidget(buttonsCancel)
        buttonsHBox.addWidget(buttonsOK)
        buttonsWidget.setLayout(buttonsHBox)
        dlgVBox.addWidget(buttonsWidget)

        buttonsOK.clicked.connect(dlg.accept)
        buttonsCancel.clicked.connect(dlg.reject)

        res = dlg.exec_()
        if res:
            for k, v in fields:
                setattr(self, k, self.inputs[k].text())
        return res
