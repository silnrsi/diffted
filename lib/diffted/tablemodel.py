
from PyQt5 import QtCore, QtGui, QtWidgets
import csv, os
from difflib import SequenceMatcher

class DiffRow(list):
    def __hash__(self):
        return hash(u"\uFDD0".join(self))

class Cell(QtWidgets.QWidget):
    _propDefaults = {
        'diffClass': None,
        'userClass': None
    }

    def initFromItem(self, item):
        for k, v in self._propDefaults.items():
            other = item.property(k)
            self.setProperty(k, other or v)

class DitDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, *a):
        super(DitDelegate, self).__init__(*a)
        self.label = Cell(self.parent())
        self.debugFlag = False

    def paint(self, painter, option, index):
        proxy = index.model()
        item = proxy.sourceModel().itemFromIndex(proxy.mapToSource(index))
        self.label.initFromItem(item)
        self.initStyleOption(option, index)
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        style.unpolish(self.label)
        style.polish(self.label)
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, option, painter, self.label)

class DitItem(QtGui.QStandardItem, QtCore.QObject):
    def __init__(self, *v):
        super(QtGui.QStandardItem, self).__init__(*v)
        self.properties = {}

    def setProperty(self, key, value):
        self.properties[key] = value

    def property(self, key):
        return self.properties.get(key, None)

class DitTableModel(QtGui.QStandardItemModel):
    diffBrush = QtGui.QBrush(QtGui.QColor("red"))
    insertBrush = QtGui.QBrush(QtGui.QColor("cyan"))
    deleteBrush = QtGui.QBrush(QtGui.QColor("gray"))
    whiteBrush = QtGui.QBrush(QtGui.QColor("white"))
    blackBrush = QtGui.QBrush(QtGui.QColor("black"))

    def __init__(self, parent=None):
        super(DitTableModel, self).__init__(parent)
        self.hasDiff = False

    def loadFromCsv(self, fname, config):
        self.beginResetModel()
        self.clear()
        self.fname = fname
        with open(fname) as f:
#            self.dialect = csv.Sniffer().sniff(f.read(1024))
#            f.seek(0)
#            rdr = csv.DictReader(f, dialect=self.dialect)
            rdr = csv.DictReader(f)
            self.fieldnames = rdr.fieldnames[:]
            self.setHorizontalHeaderLabels(self.fieldnames)
            for r in rdr:
                items = [DitItem(r[x]) for x in rdr.fieldnames]
                self.appendRow(items)
        self.endResetModel()

    def saveCsv(self, fname):
        with open(fname, "w") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames, # dialect=self.dialect,
                        lineterminator = os.linesep, quoting=csv.QUOTE_MINIMAL, quotechar = '"', escapechar = '\\')
            writer.writeheader()
            for i in range(self.rowCount()):
                writer.writerow({self.fieldnames[j]: self.data(self.index(i, j)) for j in range(self.columnCount())})

    def colDiff_(self, orig, new):
        res = [None] * len(new)
        m = SequenceMatcher(a=orig, b=new)
        for t, astart, aend, bstart, bend in m.get_opcodes():
            for i in range(bstart, bend):
                res[i] = t
        return res

    def loadDiffCsv(self, fh):
        if self.hasDiff:
            self.dumpDiff()
        #dialect = csv.Sniffer().sniff(fh.read(1024))
        #fh.seek(0)
        rdr = csv.DictReader(fh)
        diffdata = [DiffRow(r[x] for x in rdr.fieldnames) for r in rdr]
        maindata = [DiffRow(self.itemFromIndex(self.index(x, y)).text()
                        for y in range(self.columnCount()))
                            for x in range(self.rowCount())]
        m = SequenceMatcher(a=diffdata, b=maindata)
        inserted = 0    # Yes deleted items are inserted!
        for t, astart, aend, bstart, bend in m.get_opcodes():
            # print(t, astart, aend, bstart, bend)
            alen = aend - astart
            blen = bend - bstart
            bstart += inserted
            if t == 'replace':
                for i in range(min(alen, blen)):
                    coldiff = self.colDiff_(diffdata[astart+i], maindata[bstart+i])
                    for j, c in enumerate(coldiff):
                        if c is None:
                            continue
                        item = self.itemFromIndex(self.index(bstart+i, j))
                        if c in ('replace', 'insert', 'delete'):
                            item.setProperty('diffClass', c)
#                        if c == 'replace':
#                            item.setForeground(self.diffBrush)
#                        elif c == 'insert':
#                            item.setBackground(self.insertBrush)
#                        elif c == 'delete':
#                            item.setBackground(self.deleteBrush)
#                            item.setEditable(False)
                for i in range(blen - alen):
                    for j in range(self.columnCount()):
                        self.itemFromIndex(self.index(bstart+i+alen, j)).setProperty('diffClass', 'insert')
#                        self.itemFromIndex(self.index(bstart+i+alen, j)).setBackground(self.insertBrush)
                for i in range(alen - blen):
                    row = [DitItem(x) for x in diffdata[astart+blen+i]]
                    self.insertRow(bstart+blen+i, row)
                    for r in row:
#                        r.setBackground(self.deleteBrush)
                        r.setProperty('diffClass', 'delete')
                        r.setEditable(False)
                    inserted += 1
            elif t == 'insert':
                for i in range(blen):
                    for j in range(self.columnCount()):
                        self.itemFromIndex(self.index(bstart+i, j)).setProperty('diffClass', 'insert')
#                        self.itemFromIndex(self.index(bstart+i, j)).setBackground(self.insertBrush)
            elif t == 'delete':
                for i in range(alen):
                    row = [DitItem(x) for x in diffdata[astart+i]]
                    self.insertRow(bstart+i, row)
                    for r in row:
                        r.setProperty('diffClass', 'delete')
#                        r.setBackground(self.deleteBrush)
                        r.setEditable(False)
                inserted += alen
        self.hasDiff = True

    def dumpDiff(self):
        for i in range(self.rowCount()-1, -1, -1):
            first = self.item(i, 0)
            if first.property('diffClass') == 'delete':
#            if first.background() == self.deleteBrush:
                self.removeRow(i)
                continue
            for j in range(self.columnCount()):
                c = self.item(i, j)
                c.setProperty('diffClass', None)
#                if c.background() == self.insertBrush:
#                    c.setBackground(self.whiteBrush)
#                elif c.foreground() == self.diffBrush:
#                    c.setForeground(self.blackBrush)
        self.hasDiff = False

    def findDiffInRow(self, backwards, row, startCol):
        if backwards:
            end = -1
            counter = -1
        else:
            end = self.columnCount()
            counter = 1
        for i in range(startCol, end, counter):
            item = self.item(row, i)
            if item.property('diffClass') is not None:
#            b = item.background()
#            if b == self.insertBrush or b == self.deleteBrush or item.foreground() == self.diffBrush:
                return self.index(row, i)
        return None

    def nextDiffFrom(self, curri):
        row = curri.row()
        col = curri.column()
        resi = self.findDiffInRow(False, row, col+1)
        if resi is not None: return resi
        for r in range(row + 1, self.rowCount()):
            resi = self.findDiffInRow(False, r, 0)
            if resi is not None: return resi
        for r in range(0, row + 1):
            resi = self.findDiffInRow(False, r, 0)
            if resi is not None: return resi
        return None

    def lastDiffFrom(self, curri):
        row = curri.row()
        col = curri.column()
        resi = self.findDiffInRow(True, row, col-1)
        if resi is not None: return resi
        for r in range(row-1, -1, -1):
            resi = self.findDiffInRow(True, r, self.columnCount()-1)
            if resi is not None: return resi
        for r in range(self.rowCount()-1, row-1, -1):
            resi = self.findDiffInRow(True, r, self.columnCount()-1)
            if resi is not None: return resi
        return None
