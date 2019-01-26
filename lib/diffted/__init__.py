import sys, argparse
from PyQt5 import QtWidgets
import os
from diffted import main

def entry_point():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile",nargs="?")
    parser.add_argument("-s","--stylesheet",help="css stylesheet")
    parser.add_argument("-g","--gitmod",help="git modifier to diff with")
    parser.add_argument("-p","--profile",action="store_true",help="Profile startup")
    args, extras = parser.parse_known_args()

    if args.profile:
        import cProfile, pstats, io
        pr = cProfile.Profile()
        pr.enable() 
    app = QtWidgets.QApplication(sys.argv[:1] + extras)
    if args.stylesheet:
        with open(args.stylesheet) as fh:
            app.setStyleSheet("".join(fh.readlines()))
    mainWin = main.Main(app)
    #import pdb; pdb.set_trace()
    if args.infile is not None:
        mainWin.openfilename(args.infile)
    if args.gitmod is not None:
        mainWin.toolbars['Git'].version.setText(args.gitmod)
        mainWin.toolbars['Git'].diffAction.trigger()
    if args.profile:
        pr.disable()

    mainWin.show()
    res = app.exec_()

    if args.profile:
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats()
        ps.print_stats()
        print(s.getvalue())

    sys.exit(res)

