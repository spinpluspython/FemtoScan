from pyqtgraph.Qt import QtGui
#import pyqtgraph.Qt.pQtGui as pQtGui
import PyQt5.QtCore as QtCore


from pyqtgraph.parametertree import Parameter, ParameterTree


class CustomParamTree(ParameterTree):
    setValue = QtCore.pyqtSignal(str, str, str)

    LockinA = {"Part 1": 0, "Part 2": 20, "Part 3": 30, "Part 4": 40, "Part 5": 50, "Part6": 60, "Part 7": 70,
               "Part 8": 80, "Part 10": 90}  # for testing

    LockinB = {"Part B1": 0, "Part B2": 20, "Part B3": 30, "Part B4": 40, "Part B5": 50, "Part B6": 60, "Part B7": 70,
               "Part B8": 80, "Part B9": 90}  # also for testing



    def __init__(self, parent=None):
        ParameterTree.__init__(self)
        self.setParent(parent)
        self.params = []
        self.p = Parameter

        self.params = self.makeParamtreeList([[self.LockinA, "lockinA"], [self.LockinB, "lockinB"]])



        self.p= Parameter.create(name='params', type='group', children=self.params)
        print(self.p)
        self.p.sigTreeStateChanged.connect(self.change)
        self.setParameters(self.p, showTop=False)
        self.setWindowTitle('Example: Parameter Tree')

        win = QtGui.QWidget()
        layout = QtGui.QGridLayout()
        win.setLayout(layout)

        win.show()
        win.resize(1600, 1600)

    # Makes a List to create a parameterTree out of a dict (not sure if dict, list or custom-thingy is given -> adapt)

    #fixed type float
    def makeParamtreeList(self, objectList): #for testing objectList has shape of helpList

        """
        
        Args:
            objectList: List of objects which contain parameters  

        Returns: List that is compatible with the Parameter.create function

        """

        ret = []
        #helpList = [[object.parameters, object.name for object in objectList  # helpList has the shape [[ObjectA, "NameA"],[ObjectB, "NameB"],...]
        for object in objectList:
            helper1 = []                      #helper1 is a list off all childs of each obj in objectList
            #for key in Object.parameters():
            Keylist = []
            for key in object[0]:
                Keylist.append(str(key))

            for key in Keylist:
                helper1.append({'name': key, 'type': "float", 'value': object[0][key]})

            ret.append({'name': object[1], 'type': 'group', 'children': helper1})

            #print(ret)

        return ret


## If anything changes in the tree
    def change(self, param, changes):

        """
        
        Args: 
            changes: contains the Parameter (as Object.Parameter), the change type (not important) and the new data/value

        Returns: nothing

        """

        print("tree changes:")
        for param, change, data in changes:

            path = self.p.childPath(param)     # path = ['object', 'Parameter'
            print(path)
            if path is not None:

                childName = '.'.join(path)
            else:
                childName = param.name()
            print('  parameter: %s' % childName)
            print('  change:    %s' % change)
            print('  data:      %s' % str(data))
            print('  ----------')
            #print(type(childName), type(change))
            self.setValue.emit(childName, change, str(data))




    def valueChanging(self, param, value):
        print("Value changing (not finalized): %s %s" % (param, value))






if __name__ == '__main__':

    app = QtGui.QApplication([])
    w = CustomParamTree()
    w.show()
    QtGui.QApplication.instance().exec_()