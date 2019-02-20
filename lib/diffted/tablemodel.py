
from PyQt5 import QtCore, QtGui, QtWidgets
import csv, os, re, ast
from difflib import SequenceMatcher

class EvalStyle(object):
    def __init__(self, rule=None):
        self.font = None
        self.backgroundColor = None
        self.foregroundColor = None
        if rule is not None:
            self.initFrom(rule)

    def initFrom(self, rule):
        for ck in ('foregroundColor', 'backgroundColor'):
            c = rule.get(ck, None)
            setattr(self, ck, QtGui.QBrush(QtGui.QColor(c)) if c is not None else None) 
        if 'font' in rule:
            f = QtGui.QFont()
            def mapstyle(n):
                return {'italic': 1, 'oblique': 2}.get(n, 0)
            def mapweight(n):
                return {'thin': 0, 'extralight': 12, 'light': 25, 'normal': 50,
                        'medium': 57, 'demibold': 63, 'bold': 75, 'extrabold': 81,
                        'black': 87}.get(n, 50)
            actions = {'family': (f.setFamily, str),
                       'style': (f.setStyle, mapstyle),
                       'weight': (f.setWeight, mapweight)}
            font = rule['font']
            for a, funcs in actions.items():
                v = font.get(a, None)
                if v is not None:
                    funcs[0](funcs[1](v))
        else:
            f = None
        setattr(self, "font", f)

    def merge(self, p):
        if p.font is not None:
            self.font = p.resolve(self.font) if self.font is not None else p.font
        if p.backgroundColor is not None:
            self.backgroundColor = p.backgroundColor
        if p.foregroundColor is not None:
            self.foregroundColor = p.foregroundColor

    def copy(self):
        res = EvalStyle()
        res.font = self.font
        res.backgrounColor = self.backgroundColor
        res.foregroundColor = self.foregroundColor
        return res

    def isEmpty(self):
        if self.font or self.foregroundColor or self.backgroundColor:
            return False
        return True

class Evaluator(object):
    def __init__(self):
        self.locals = {}
        self.fns = {
            '__builtins__': None,
            're' : re,
        }
        for x in ('True', 'False', 'None', 'int', 'float', 'str', 'abs', 'bool',
                  'dict', 'enumerate', 'filter', 'hex', 'len', 'list', 'map',
                  'max', 'min', 'ord', 'range', 'set', 'sorted', 'sum', 'tuple', 'zip'):
            self.fns[x] = __builtins__[x]

    def is_safe(self, exp):
        # no dunders in attribute names
        for n in ast.walk(ast.parse(exp)):
            if "__" in getattr(n, 'id', ""):
                return False
        return True

    def eval(self, exp, **kw):
        if exp is None:
            return True
        return eval(exp, self.fns, {**self.locals, **kw})

evaluator = Evaluator()

class DiffRow(list):
    def __hash__(self):
        return hash(u"\uFDD0".join(self))

class DitItem(QtGui.QStandardItem, QtCore.QObject):

    def __init__(self, *v, model=None):
        super(QtGui.QStandardItem, self).__init__(*v)
        self.model = model
        self.diffStyle = None 
        self._updateTypes = {'foregroundColor': (self.setForeground, QtGui.QBrush(QtCore.Qt.NoBrush)),
                             'backgroundColor': (self.setBackground, QtGui.QBrush(QtCore.Qt.NoBrush)),
                             'font': (self.setFont, QtGui.QFont())}
        self.evalStyle = None
        self.diffMode = None

    def setDiffMode(self, mode, styles):
        self.diffStyle = styles.get(mode, None)
        if mode != self.diffMode:
            self.update()
        self.diffMode = mode

    def mergeEvalStyle(self, p):
        if self.evalStyle is None:
            self.evalStyle = EvalStyle()
        self.evalStyle.mergeStyle(p)

    def setData(self, value, role):
        super(DitItem, self).setData(value, role)
        self.model.runRules(row=self.model.indexFromItem(self).row())

    def update(self, changed=True):
        if self.evalStyle is None and self.diffStyle is None:
            if not changed:
                return
            p = None
        if self.evalStyle is None:
            p = self.diffStyle
        elif self.diffStyle is None:
            p = self.evalStyle
        else:
            p = self.evalStyle.copy()
            p.merge(self.diffStyle)
            
        for ck, cf in self._updateTypes.items():
            v = getattr(p, ck, None)
            if v is None:
#                if not changed:
#                    continue
                cf[0](cf[1])
            else:
                cf[0](v)


class DitTableModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super(DitTableModel, self).__init__(parent)
        self.styles = {}
        self.hasDiff = False
        self.rules = {}
        self.itemChanged.connect(self.hasChanged)
        self.runningRules = False

    def hasChanged(self, item):
        self.dataChanged = True

    def loadConfig(self, config):
        for k, d in {'replace': {'backgroundColor': "#FFC0C0"},
                     'insert': {'backgroundColor': "#C0C0FF"},
                     'delete': {'backgroundColor': "#E0E0E0"}}.items():
            self.styles[k] = EvalStyle(config.get(k+"Style", d))
        if 'rules' not in config:
            return
        for r in config['rules']:
            e = r.get('eval', None)
            if e is not None and not evaluator.is_safe(e):
                continue
            self.rules.setdefault(r.get('col', None), []).append({'style': EvalStyle(r),
                                                                  'eval': r.get('eval', None)})

    def loadFromCsv(self, f, config):
        self.beginResetModel()
        self.clear()
        self.fname = f.path
#       self.dialect = csv.Sniffer().sniff(f.read(1024))
#       f.seek(0)
#       rdr = csv.DictReader(f, dialect=self.dialect)
        rdr = csv.DictReader(f)
        self.fieldnames = rdr.fieldnames[:]
        self.setHorizontalHeaderLabels(self.fieldnames)
        for r in rdr:
            items = [DitItem(r[x], model=self) for x in rdr.fieldnames]
            self.appendRow(items)
        self.endResetModel()
        self.dataChanged = False
        if len(self.rules):
            self.runRules()

    def saveCsv(self, f):
        writer = csv.DictWriter(f, fieldnames=self.fieldnames, # dialect=self.dialect,
                    lineterminator = "\n", quoting=csv.QUOTE_MINIMAL,
                    quotechar = '"', escapechar = '\\')
        writer.writeheader()
        for i in range(self.rowCount()):
            writer.writerow({self.fieldnames[j]: self.data(self.index(i, j))
                             for j in range(self.columnCount())})

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
                            item.setDiffMode(c, self.styles)
                for i in range(blen - alen):
                    for j in range(self.columnCount()):
                        self.itemFromIndex(self.index(bstart+i+alen, j)).setDiffMode('insert', self.styles)
                for i in range(alen - blen):
                    row = [DitItem(x) for x in diffdata[astart+blen+i]]
                    self.insertRow(bstart+blen+i, row)
                    for r in row:
                        r.setDiffMode('delete', self.styles)
                        r.setEditable(False)
                    inserted += 1
            elif t == 'insert':
                for i in range(blen):
                    for j in range(self.columnCount()):
                        self.itemFromIndex(self.index(bstart+i, j)).setDiffMode('insert', self.styles)
            elif t == 'delete':
                for i in range(alen):
                    row = [DitItem(x) for x in diffdata[astart+i]]
                    self.insertRow(bstart+i, row)
                    for r in row:
                        r.setDiffMode('delete', self.styles)
                        r.setEditable(False)
                inserted += alen
        self.hasDiff = True

    def runRules(self, row=None):
        if self.runningRules:
            return
        else:
            self.runningRules = True
        lastRow = None
        rowData = None
        nextRow = None
        rowRange = range(self.rowCount()-1, -1, -1) if row is None else [row]
        for i in rowRange:
            if nextRow is None:
                rowData = {self.fieldnames[j]: self.item(i,j).text() for j in range(self.columnCount())}
            else:
                lastRow = rowData
                rowData = nextRow
            if lastRow is None and i < self.rowCount() - 1:
                lastRow = {self.fieldnames[j]: self.item(i+1,j).text() for j in range(self.columnCount())}
            if i > 0:
                nextRow = {self.fieldnames[j]: self.item(i-1,j).text() for j in range(self.columnCount())}
            else:
                nextRow = None
            rowStyle = EvalStyle()
            for rule in self.rules.get(None, []):
                if evaluator.eval(rule['eval'], r=rowData, lastRow=nextRow, nextRow=lastRow):
                    rowStyle.merge(rule['style'])
            for j in range(self.columnCount()):
                cellStyle = rowStyle.copy()
                for rule in self.rules.get(self.fieldnames[j], []):
                    if evaluator.eval(rule['eval'], r=rowData, lastRow=nextRow, nextRow=lastRow):
                        cellStyle.merge(rule['style'])
                if not cellStyle.isEmpty() or row is not None:
                    item = self.item(i,j)
                    item.evalStyle = cellStyle
                    item.update(changed=False)
        self.runningRules = False

    def dumpDiff(self):
        for i in range(self.rowCount()-1, -1, -1):
            first = self.item(i, 0)
            if first.diffMode == 'delete':
                self.removeRow(i)
                continue
            for j in range(self.columnCount()):
                c = self.item(i, j)
                c.setDiffMode(None, self.styles)
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
            if item.diffMode is not None:
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

