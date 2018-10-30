
from PyQt5 import QtCore, QtGui, QtWidgets
import re

class FlipFlop(QtWidgets.QWidget):
    def __init__(self, *names, parent=None, tooltips=None):
        super(FlipFlop, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        self.buttons = QtWidgets.QButtonGroup()
        self.buttons.setExclusive(True)
        for i, n in enumerate(names):
            try:
                t = int(n)
            except ValueError:
                t = 0
            if t == 0:
                b = QtWidgets.QPushButton(n)
                b.setCheckable(True)
                b.setStyleSheet('font-size: 10px; max-height: 8px; min-height: 7px; max-width: 12px')
            else:
                b = QtWidgets.QToolButton(self)
                b.setArrowType(n)
                b.setStyleSheet('QToolButton { max-height: 12px; min-height: 10px; max-width: 12px} QToolTip { font-size: 11pt }')
            self.buttons.addButton(b, id=i)
            if tooltips is not None and len(tooltips) > i:
                b.setToolTip(tooltips[i])
            layout.addWidget(b)
        self.buttons.button(0).click()
        self.setLayout(layout)

class FilterEdit(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(FilterEdit, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(1, 0, 1, 0)
        self.lineEdit = QtWidgets.QLineEdit()
        rgroup = QtWidgets.QHBoxLayout()
        rgroup.setContentsMargins(1, 1, 1, 0)
        rgroup.setSpacing(1)
        self.checkBox = QtWidgets.QCheckBox("On")
        self.checkBox.setStyleSheet("spacing: 2px")
        self.regBox = QtWidgets.QCheckBox("Reg")
        self.regBox.setStyleSheet("QCheckBox { font-size: 10px; height: 36px; margin: 0 2px 0 2px; padding-bottom: -6px; spacing: -13px } ::indicator { subcontrol-position: top left; width: 13px; height: 13px; }")
        self.regBox.setToolTip("Interpret filter as regular expression")
        #self.flipflop = FlipFlop("S", "R")
        self.dirbuttons = FlipFlop(1, 2, tooltips=["Search backwards", "Search forwards"])
        rgroup.addWidget(self.checkBox)
        rgroup.addStretch()
        rgroup.addWidget(self.dirbuttons)
        rgroup.addWidget(self.regBox)
        layout.addWidget(self.lineEdit)
        layout.addLayout(rgroup)
        self.setLayout(layout)

    def arrow(self, down=False):
        return self.dirbuttons.buttons.button(1 if down else 0)

    def match(self, val):
        if self.isRegex():
            return re.search(self.lineEdit.text(), val)
        else:
            return self.lineEdit.text() in val

    def isRegex(self):
        return self.regBox.isChecked()

    def getSettings(self):
        val = self.lineEdit.text()
        reg = self.isRegex()
        ison = self.checkBox.isChecked()
        if val != "":
            return (val, reg, ison)
        else:
            return None

    def setFromSettings(self, vals):
        self.lineEdit.setText(vals[0])
        self.regBox.setChecked(vals[1])
        if self.checkBox.isChecked() != vals[2]:
            f.checkBox.setChecked(vals[2])

class FilterProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FilterProxy, self).__init__(parent)
        self.filters = []

    def setFilters(self, filters):
        self.filters = filters
        for i, f in enumerate(filters):
            f.checkBox.stateChanged.connect(self.filterChanged)
            f.arrow(True).clicked.connect(lambda e,x=f,y=i: x.parent().findNextInColumn(y, x))
            f.arrow(False).clicked.connect(lambda e,x=f,y=i: x.parent().findPrevInColumn(y, x))

    @QtCore.pyqtSlot(int)
    def filterChanged(self, state):
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        m = self.sourceModel()
        for i, f in enumerate(self.filters):
            if f.checkBox.isChecked():
                if not f.isRegex():
                    if not f.lineEdit.text() in m.data(m.index(row, i, parent)):
                        return False
                elif not re.search(f.lineEdit.text(), m.data(m.index(row, i, parent))):
                    return False
        return True

