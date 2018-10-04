#!/usr/bin/env python

from PyQt5 import QtCore, QtGui, QtWidgets
from diffted.filter import FilterEdit

class DitHeaderView(QtWidgets.QHeaderView):
    def __init__(self, parent):
        super(DitHeaderView, self).__init__(QtCore.Qt.Horizontal, parent)
        self.filters = []
        self.setSortIndicatorShown(True)
        self.sectionDoubleClicked.connect(self.sectionDoubleClickedEvent)
        self._padding = 0
        parent.horizontalScrollBar().valueChanged.connect(self.adjustPositions)

    def setFilters(self, count):
        while self.filters:
            editor = self.filters.pop()
            editor.deleteLater()
        for i in range(count):
            editor = FilterEdit(self.parent())
            editor.lineEdit.setPlaceholderText("Filter")
            editor.show()
            self.filters.append(editor)
        self.adjustPositions()
        return self.filters

    def sizeHint(self):
        size = super(DitHeaderView, self).sizeHint()
        if self.filters:
            height = self.filters[0].sizeHint().height()
            size.setHeight(size.height() + height)
        return size

    def updateGeometries(self):
        if self.filters:
            height = self.filters[0].sizeHint().height()
            self.setViewportMargins(0, 0, 0, height + self._padding)
        else:
            self.setViewportMargins(0, 0, 0, 0)
        super(DitHeaderView, self).updateGeometries()
        self.adjustPositions()

    def adjustPositions(self):
        for index, editor in enumerate(self.filters):
            height = editor.sizeHint().height()
            editor.move(
                self.sectionPosition(index) + self.pos().x() + 2,
                super(DitHeaderView, self).sizeHint().height() + (self._padding // 2))
            editor.resize(self.sectionSize(index), height)

    def sectionDoubleClickedEvent(self, index):
        x = self.sortIndicatorOrder()
        if index == self.sortIndicatorSection():
            self.setSortIndicator(index, x ^ 1)
        else:
            self.setSortIndicator(index, 0)

class DitTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(DitTableView, self).__init__(parent)
        self.rowContextMenu = QtWidgets.QMenu()
        addrowsabove = self.rowContextMenu.addAction("Add rows above")
        addrowsabove.triggered.connect(self.addRowsAbove)
        addrowsbelow = self.rowContextMenu.addAction("Add rows below")
        addrowsbelow.triggered.connect(self.addRowsBelow)
        delrows = self.rowContextMenu.addAction("Remove rows")
        delrows.triggered.connect(self.delRows)
        rowhdr = self.verticalHeader()
        rowhdr.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        rowhdr.customContextMenuRequested.connect(self.row_rightclick)

        hdr = DitHeaderView(self)
        self.setHorizontalHeader(hdr)
        self.colContextMenu = QtWidgets.QMenu()
        addcolsright = self.colContextMenu.addAction("Add Columns right")
        addcolsright.triggered.connect(self.addColumnsRight)
        addcolsleft = self.colContextMenu.addAction("Add Columns left")
        addcolsleft.triggered.connect(self.addColumnsLeft)
        addcolsleft = self.colContextMenu.addAction("Remove columns")
        addcolsleft.triggered.connect(self.delColumns)
        namecol = self.colContextMenu.addAction("Rename column")
        namecol.triggered.connect(self.renameColumn)
        hdr.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        hdr.customContextMenuRequested.connect(self.column_rightclick)

    def resetModel(self):
        #self.setSortingEnabled(True)
        m = self.model()
        if m.columnCount() == 0:
            return
        hdr = self.horizontalHeader()
        m.setFilters(hdr.setFilters(m.columnCount()))
        hdr.setSortIndicator(0, 0)

    def row_rightclick(self, loc):
        vh = self.verticalHeader()
        self.currPos = vh.logicalIndexAt(loc)
        self.rowContextMenu.exec_(QtGui.QCursor.pos())

    def column_rightclick(self, loc):
        hh = self.horizontalHeader()
        self.currPos = hh.logicalIndexAt(loc)
        self.colContextMenu.exec_(QtGui.QCursor.pos())

    def _getSelectedRows(self):
        selections = set([x.row() for x in self.selectedIndexes()])
        if len(selections) == 0:
            selections = [self.currPos]
        return selections

    def _getSelectedColumns(self):
        selections = set([x.columns() for x in self.selectedIndexes()])
        if len(selections) == 0:
            selections = [self.currPos]

    def addRowsAbove(self):
        selections = self._getSelectedRows()
        num = len(selections)
        above = min(selections)
        self.model().insertRows(above, num)

    def addRowsBelow(self):
        selections = self._getSelectedRows()
        num = len(selections)
        below = max(selections) + 1
        self.model().insertRows(below, num)

    def delRows(self):
        selections = self._getSelectedRows()
        for i in sorted(selections, key=lambda x:-x):
            self.model().removeRows(i, 1)

    def addColumnsRight(self):
        selections = self_getSelectedColumns()
        num = len(selections)
        right = max(selections) + 1
        self.model().insertColumns(right, num)

    def addColumnsLeft(self):
        selections = self_getSelectedColumns()
        num = len(selections)
        left = max(selections)
        self.model().insertColumns(left, num)

    def delColumns(self):
        selections = self._getSelectedColumns()
        for i in sorted(selections, key=lambda x:-x):
            self.model().removeColumns(i, 1)

    def renameColumn(self):
        # this doesn't work, sigh
        hdr = self.horizontalHeader()
        index = hdr.model().index(0, self.currPos)
        hdr.item(index).setEditable(True)
        hdr.setCurrentIndex(index)
        hdr.edit(index)
        hdr.item(index).setEditable(False)
