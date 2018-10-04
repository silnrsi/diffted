
from PyQt5 import QtCore, QtGui, QtWidgets
import re

class FlipFlop(QtWidgets.QWidget):
    def __init__(self, *names, parent=None):
        super(FlipFlop, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        self.buttons = QtWidgets.QButtonGroup()
        self.buttons.setExclusive(True)
        for i, n in enumerate(names):
            b = QtWidgets.QPushButton(n)
            b.setCheckable(True)
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
        rgroup.addWidget(self.checkBox)
        rgroup.addWidget(self.flipflop)
        layout.addLayout(rgroup)
        layout.addWidget(self.lineEdit)
        self.setLayout(layout)

class FilterProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FilterProxy, self).__init__(parent)
        self.filters = []

    def setFilters(self, filters):
        self.filters = filters
        for f in filters:
            f.checkBox.stateChanged.connect(self.filterChanged)

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

