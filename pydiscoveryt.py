'''

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
    
xcept ImportError:
print("PyQt5 is not installed")
'''
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtCore import QUrl

#except ImportError:
#print("PySide2 is not installed")


#from PySide2.QtWebKit import *
#from PySide2.QtWebKitWidgets import *

import sys
import socket
import random
#import discovery as discovery


def discover(port):
    print("Discovering on port: {}".format(port))
    host = '255.255.255.255'
    data = bytes([0x70, 0x63, 0x00, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

    timeout = 1
    results = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(timeout)

            try:
                s.sendto(data, (host, port))        
            except socket.error:
                print(socket.error)
                
            try:
                while True:
                    data = s.recv(1024)
                    try:                    
                        modem = parse(data)                        
                        results.append(modem)                    
                        print("{0} - {1} - {2}".format(modem["mac"], modem["ip"], modem["product"]))
                    except Exception as e:
                        print("Parse exception: {0}".format(e))

            except socket.timeout:
                #print(socket.timeout)
                pass

            except socket.error:
                print(socket.error)
            finally:                
                return results
                         
    except Exception as e:
        print("Exception: {0}".format(e))
        #print("Exception{0}".format(e.args))
       
     
def parseMac(data):           
    #mac = line.subsring(2,8)
    mac = ""
    try:
        for x in range(2,8):
            n = hex(data[x])[2:4]

            if len(n) == 1:
                n = "" + "0" + n
            mac += n.upper()
            
            if x < 7:
                mac += ":"
        return mac
    except Exception as e:
        print("Parse Mac exception: {0}".format(e))
        return mac

def parseIp(data):    
    ip = ""
    try:
        for x in range(9,13):
            ip += str(data[x])
            if x < 12:
                ip += "."
        return ip
    except Exception as e:
        print("Parse IP exception: {0}".format(e))
        return ip


def rawToStr(data):
    s = ""
    for each in data:
        s += chr(each)
    return s


def parse(data):    
    microhard = "00:0F:92"
    mac = parseMac(data) 
    modem = {}
    if mac.count(microhard):        
        ip = parseIp(data)        
        chars = rawToStr(data)     
        line = chars[13:len(chars)].split("\0")
        #print(line)
        description = line[0]
        address = line[1]
        product = line[2]
        software = line[3]
        mode = line[4]
        network = line[5]                        
                
        modem["mac"]= mac
        modem["ip"] = ip
        modem["description"] = description        
        modem["address"] = address
        modem["product"] = product
        modem["software"] = software
        modem["mode"] = mode
        modem["network"] = network 
        modem["apn"] = ''
        modem["domain"] = ''

        cellModems = ["VIP4G", "IPn3G", "IPn4G", "Bullet", "Dragon"]
        for each in cellModems:            
            if modem["product"].count(each):                
                apn = line[7]
                domain = line[9]                            
                modem["apn"] = apn
                modem["domain"] = domain                                        
        
        return modem    
    else:
        print("Not a microhard modem: {0}". format(mac))
        

class DiscoveryWorker(QtCore.QThread):
    completedSignal = QtCore.Signal(dict, str)
    
    def __init__(self, port):
        QtCore.QThread.__init__(self)
        self.port = port
        
        
    def run(self):
        print("Discovery worker... on port {}".format(self.port))
                
        result = discover(self.port)
        self.completedSignal.emit(result, self.objectName())
        

class DiscoverWidget(QtWidgets.QWidget):
    
    cellPort = 20097
    vipPort = 20077
    ipPort= 20087
    
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
   
        self.threads = {}
        
        self.cellButton = QtWidgets.QPushButton("Cell")
        self.cellButton.clicked.connect(self.cell_button_action)
        
        self.vipButton = QtWidgets.QPushButton("VIP")
        self.vipButton.clicked.connect(self.vip_button_action)

        self.ipButton = QtWidgets.QPushButton("IP")
        self.ipButton.clicked.connect(self.ip_button_action)

        self.allButton = QtWidgets.QPushButton("All")
        self.allButton.clicked.connect(self.all_button_action)

        self.clearButton = QtWidgets.QPushButton("Clear")
        self.clearButton.clicked.connect(self.clear_button_action)
        
        self.buttonsLayout = QtWidgets.QHBoxLayout()                
        self.buttonsLayout.addWidget(self.cellButton)
        self.buttonsLayout.addWidget(self.vipButton)
        self.buttonsLayout.addWidget(self.ipButton)
        self.buttonsLayout.addWidget(self.allButton)
        self.buttonsLayout.addWidget(self.clearButton)
        
        self.headers = ["MAC", "IP Address", "Product", "Description", "Software", "APN", "Domain", "Mode", "Network", "Address"]
        
        self.table = QtWidgets.QTableWidget(0, len(self.headers), self)

        self.table.setHorizontalHeaderLabels(self.headers)        
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        #self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)        
        #self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(self.on_click)

        #self.label = QtWidgets.QLabel("Discovery")
        #self.label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.buttonsLayout)
        self.layout.addWidget(self.table)      
                
        self.setLayout(self.layout)    
     
        self.resize(800, 400)
        self.setWindowTitle("Discover IP")
        self.show()

        
    def on_click(self):        
        for item in self.table.selectedItems():
            #print(item.row(), item.column(), item.text())
            if item.column() == 1:
                url = "https://" + item.text()                
                #self.view = QWebEngineView()
                #self.view.load(QUrl(url))
                #self.view.show()
                browser = "firefox --new-tab " + url
                print(browser)
                self.process = QtCore.QProcess()
                self.process.start(browser)

            
    def completeAction(self, modems, name):
        print("Completed Action... thread name {}".format(name))
        self.setTable(modems)
        
        thread = self.threads.get(name)
        #if thread.isFinished():
        self.threads.pop(name)
        #else handle active thread...wait?
        
        print("Active workers {}".format(len(self.threads)))
        

    def cell_button_action(self):
        #QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        name = str(random.randint(0, 65534))
        worker = DiscoveryWorker(self.cellPort)
        worker.completedSignal.connect(self.completeAction)
        worker.setObjectName(name)
        worker.start()             

        self.threads.update({name: worker})
        
        #print(worker.currentThread(), QtCore.QThread.currentThread(), worker.thread())

    def vip_button_action(self):
        #QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)        
                
        name = str(random.randint(0, 65534))
        worker = DiscoveryWorker(self.vipPort)
        worker.completedSignal.connect(self.completeAction)
        worker.setObjectName(name)
        worker.start()             

        self.threads.update({name: worker})
        

    def ip_button_action(self):
        #QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                
        name = str(random.randint(0, 65534))        
        worker = DiscoveryWorker(self.ipPort)
        worker.completedSignal.connect(self.completeAction)
        worker.setObjectName(name)
        worker.start()             

        self.threads.update({name: worker})
        

    def all_button_action(self):
        
        self.cell_button_action()
        self.vip_button_action()
        self.ip_button_action()
            
            

    def setTable(self, modems):
        self.table.setSortingEnabled(False)     
        index = 0
        for modem in modems:            
            index += 1
            self.table.setRowCount(index)

            row = index - 1   
            keys = ["mac", "ip", "product", "description", "software", "apn", "domain", "mode", "network", "address"]
            col = 0
            for key in keys:
                cell = modem[key]
                self.item = QtWidgets.QTableWidgetItem(cell)
                if key == "ip":
                    self.item.setForeground(QtGui.QColor(0, 0, 255))
                self.table.setItem(row, col, self.item)    
                col += 1                       

        self.table.resizeColumnsToContents()        
        self.table.setSortingEnabled(True)
        
        #Not needed with threads
        #QtWidgets.QApplication.restoreOverrideCursor()


    def clear_button_action(self):        
        self.table.clear()
        self.table.setRowCount(0)       
        self.table.setHorizontalHeaderLabels(self.headers)

       



if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    widget = DiscoverWidget()
    
    sys.exit(app.exec_())

else:
    print("Importing {0}".format(__name__))
