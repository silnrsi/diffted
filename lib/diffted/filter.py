
from PyQt5 import QtCore, QtGui, QtWidgets
import re

class FlipFlop(QtWidgets.QWidget):
    def __init__(self, *names, parent=None):
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
                b.setStyleSheet('max-height: 12px; min-height: 10px; max-width: 12px')
            self.buttons.addButton(b, id=i)
            layout.addWidget(b)
        self.buttons.button(0).click()
        self.setLayout(layout)

class FilterEdit(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(FilterEdit, self).__init__(parent)
        self.setStyleSheet("""QCheckBox { spacing: 4px }
        QPushButton { padding: 2 2 2 2 }
        """)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(1, 0, 1, 0)
        self.lineEdit = QtWidgets.QLineEdit()
        rgroup = QtWidgets.QHBoxLayout()
        rgroup.setContentsMargins(1, 1, 1, 0)
        rgroup.setSpacing(1)
        self.checkBox = QtWidgets.QCheckBox("On")
        self.flipflop = FlipFlop("S", "R")
        self.dirbuttons = FlipFlop(1, 2)
        rgroup.addWidget(self.checkBox)
        rgroup.addStretch()
        rgroup.addWidget(self.dirbuttons)
        rgroup.addWidget(self.flipflop)
        layout.addWidget(self.lineEdit)
        layout.addLayout(rgroup)
        self.setLayout(layout)

    def arrow(self, down=False):
        return self.dirbuttons.buttons.button(1 if down else 0)

    def match(self, val):
        if self.flipflop.buttons.checkedId() == 0:
            return self.lineEdit.text() in val
        else:
            return re.search(self.lineEdit.text(), val)

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
                if f.flipflop.buttons.checkedId() == 0:
                    if not f.lineEdit.text() in m.data(m.index(row, i, parent)):
                        return False
                elif not re.search(f.lineEdit.text(), m.data(m.index(row, i, parent))):
                    return False
        return True

