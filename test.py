from PyQt5 import QtGui, QtCore, QtWidgets
import sys, os

# subclass
class CheckableComboBox(QtWidgets.QComboBox):
    # once there is a checkState set, it is rendered
    # here we assume default Unchecked
    def addItem(self, item):
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count()-1,0)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setCheckState(QtCore.Qt.Unchecked)

    def itemChecked(self, index):
        item = self.model().item(i,0)
        return item.checkState() == QtCore.Qt.Checked
        

# the basic main()
app = QtWidgets.QApplication(sys.argv)
dialog = QtWidgets.QMainWindow()
mainWidget = QtWidgets.QWidget()
dialog.setCentralWidget(mainWidget)
ComboBox = CheckableComboBox(mainWidget)
for i in range(6):
    ComboBox.addItem("Combobox Item " + str(i))

dialog.show()
sys.exit(app.exec_())