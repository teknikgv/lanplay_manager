from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QMainWindow, QTableWidgetItem, QInputDialog, QDialog, QLineEdit, QDialogButtonBox, QVBoxLayout, QLabel
from PyQt5 import uic, QtGui
import sys

import os, requests, json, re
import threading
from tkinter import *
from db import database


class LanplayManagerWindow(QMainWindow):

    class errorDialog(QDialog):
        def __init__(self, message):
            super().__init__()

            self.setWindowTitle("Errrrorrr!")

            QBtn = QDialogButtonBox.Ok

            self.buttonBox = QDialogButtonBox(QBtn)
            self.buttonBox.accepted.connect(self.accept)
            self.buttonBox.rejected.connect(self.reject)

            self.layout = QVBoxLayout()
            self.layout.addWidget(QLabel(message))
            self.layout.addWidget(self.buttonBox)
            self.setLayout(self.layout)




    server_address = None
    add_server_win = None
    list_box = None
    thread = None

    tids = None

    graphql_request = {"query": """
        query {
            serverInfo {
                online,
                idle,
                version
            }
            room {
                ip
                contentId,
                hostPlayerName,
                sessionId,
                nodeCountMax,
                nodeCount,
                nodes {playerName,nodeId,isConnected}
                advertiseDataLen,
                advertiseData
            }
        }
    """}


    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('lib/assets/lanplaymanager.ui', self)
        self.tids = json.loads(open('lib/assets/games.json').read())

        self.setWindowIcon(QtGui.QIcon('lib/assets/lan.ico'))


        # authenticate when the login button is clicked
        self.ui.launch_server_button.clicked.connect(self.launch_server)
        self.ui.add_server_button.clicked.connect(self.add_server)
        self.ui.delete_server_button.clicked.connect(self.delete_server)
        self.ui.refresh_list_button.clicked.connect(self.refresh_server_list_thread)

        self.show()

        self.refresh_server_list_thread()

        

    def launch_server(self):
        if self.check_server_status(selectedServer, True):
            command = "start /B start cmd.exe @cmd /k bin\lan-play.exe --relay-server-addr %s" % selectedServer
            os.system(command)
        else:
            self.errorDialog('Please select a server from the list.')

    def delete_server(self):
        selectedServer = self.check_selected_server()
        if selectedServer:
            db = database()
            db.delete_server(selectedServer)
            db.close_connection()
            self.refresh_server_list_thread()

    def check_server_status(self, server_address, show_message):
        """
        Check the server status and returns players online
        :param show_message:
        :param server_address:
        :return:
        """
        status = {}


        try: 
            url = "http://%s" % server_address
            res = requests.post(url, json=self.graphql_request, timeout = 1)
            print(server_address)
            if (res.status_code == 200):
                data = json.loads(res.text)['data']
                status['online'] = int(data['serverInfo']['online'])
                status['idle'] = int(data['serverInfo']['idle'])
                status['rooms'] = data['room']
                return status
        except:
            pass
        
        try:
            url = "http://%s/info" % server_address
            res = requests.get(url, timeout = 1)
            if (res.status_code == 200):
                data = json.loads(res.text)
                status = {}
                if ('online' in data):
                    status['online'] = int(data['online'])
        except:
            pass

        try:
            url = "http://%s" % server_address
            res = requests.get(url, timeout = 1)
            if (res.status_code == 200):
                    data = json.loads(res.text)
                    if 'clientCount' in data:
                        status['online'] = int(data['clientCount'])
        except:
            pass

        if (not 'online' in status):
            status['online'] = "?"
        if (not 'idle' in status):
            status['online'] = "?"

        if show_message:
            self.errorDialog('Server not reachable.')

        return status

    def check_selected_server(self):
        try:
            index = self.ui.server_list.currentRow()
            print(index)
            if index == -1:
                raise 'No row selected'
            selectedServer = self.ui.server_list.item(index, 2).text()
            print(selectedServer)
            while (selectedServer.startswith('  ')):
                index -= 1
                print(index)
                selectedServer = self.ui.server_list.item(index, 2).text()
                print(selectedServer)
            return selectedServer
        except Exception:
            return None

    def do_popup(self, event):
        self.popup_menu.post(event.x_root, event.y_root)

    def add_server(self):

        server_address, ok = QInputDialog().getText(self, "Add a server",
                                     "Server address:", QLineEdit.Normal)

        if server_address and ok:
            pattern = re.compile("^(?!http:|https:|www.)([-a-zA-Z0-9@:%._]{1,256}):([0-9]{1,5})$")
            if pattern.match(server_address):
                port_server = int(server_address.split(":")[1])

                if port_server < 0 or port_server > 65535:
                    self.errorDialog('Server address invalid').exec()
                    self.add_server()
                elif self.check_server_status(server_address, True):
                    db = database()
                    rows = db.select_server(server_address)
                    if rows:
                        self.errorDialog('Server already added').exec()
                        self.add_server()
                    else:
                        db.insert_server(server_address)
                        self.refresh_server_list_thread()
                    db.close_connection()
            else:
                self.errorDialog('Server address invalid').exec()
                self.add_server()

    def add_server_elements(self):
        input_server = Entry(self.add_server_win, width=40, textvariable=self.server_address)
        input_server.pack(expand="yes", anchor="center")

        enter_button = Button(self.add_server_win, text=save_label, font=(24), command=self.save_server)
        enter_button.pack(expand="yes", anchor="center")

    def save_server(self):
        if not self.server_address.get():
            messagebox.showinfo(oops_label, sever_address_value_label, parent=self.add_server_win)
        else:
            server_address = self.server_address.get()
            pattern = re.compile("^(?!http:|https:|www.)([-a-zA-Z0-9@:%._]{1,256}):([0-9]{1,5})$")

            


    def refresh_server_list_thread(self):
        thread = threading.Thread(target=self.refresh_server_list)
        thread.start()

    def refresh_server_list(self):

        serverlist = self.ui.server_list
        
        while (serverlist.rowCount() > 0): 
            serverlist.removeRow(0)

        db = database()
        rows = db.select_server('')
        db.close_connection()

        for row in rows:
            server_address = str(row[1])

            listIndex = serverlist.rowCount()
            serverlist.insertRow(listIndex)
            serverlist.setItem(listIndex, 2, QTableWidgetItem(server_address))

            server_status = self.check_server_status(server_address, False)
            serverlist.setItem(listIndex, 0, QTableWidgetItem(str(server_status['online'])))
            serverlist.setItem(listIndex, 1, QTableWidgetItem(str(server_status['idle']) if ('idle' in server_status) else ''))

            if (('rooms' in server_status) and server_status['rooms'] != None):
                for room in server_status['rooms']:
                    listIndex = serverlist.rowCount()
                    serverlist.insertRow(listIndex)
                    serverlist.setItem(listIndex, 0, QTableWidgetItem(str(room['nodeCount'])))
                    serverlist.setItem(listIndex, 2, QTableWidgetItem(f"    {self.lookup_tid(room['contentId'])} hosted by {room['hostPlayerName']}"))



    def lookup_tid(self, tid):

        for game in self.tids:
            if (tid.lower() == game['ID'].lower()):
                return game['Name']

        return "Unknown Game"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    lanplaymanagerwindow = LanplayManagerWindow()
    sys.exit(app.exec())
