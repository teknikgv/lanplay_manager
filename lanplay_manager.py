import json
import os
import platform
import re
import sys
import threading

import requests
from PyQt5 import uic, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QInputDialog, QDialog, \
    QLineEdit, QDialogButtonBox, QVBoxLayout, QLabel

from db import database


class LanplayManagerWindow(QMainWindow):
    class ErrorDialog(QDialog):
        def __init__(self, message):
            super().__init__()

            self.setWindowTitle("Errrrorrr!")

            q_dialog_button = QDialogButtonBox.Ok

            self.buttonBox = QDialogButtonBox(q_dialog_button)
            self.buttonBox.accepted.connect(self.accept)
            self.buttonBox.rejected.connect(self.reject)

            self.layout = QVBoxLayout()
            self.layout.addWidget(QLabel(message))
            self.layout.addWidget(self.buttonBox)
            self.setLayout(self.layout)

    server_address = None
    add_server_win = None
    list_box = None
    thread: threading.Thread = None

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

    refresh_server_list_signal = pyqtSignal(list, dict)

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

        self.refresh_server_list_signal.connect(self.refresh_server_list_function)

        self.refresh_server_list_thread()

    def launch_server(self):
        selected_server = self.check_selected_server()
        if selected_server:
            if self.check_server_status(selected_server, True):
                path = os.environ.get("TEKNIK_BINS_DIR", "bin/")
                match platform.system():
                    case "Windows":
                        command = "start /B start cmd.exe @cmd /k %s %s"
                    case "Darwin" | "Linux":
                        command = "bash -c \"%s %s\""
                    case _:
                        print("unsupported system!")
                        sys.exit(-1)
                flags = "--relay-server-addr %s" % selected_server
                command = command % (path, flags)
                thread = threading.Thread(target=os.system, args=command)
                thread.start()
        else:
            self.ErrorDialog('Please select a server from the list.')

    def delete_server(self):
        selected_server = self.check_selected_server()
        if selected_server:
            db = database()
            db.delete_server(selected_server)
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
            url = "http://" + server_address
            res = requests.post(url, json=self.graphql_request, timeout=1)
            print(server_address)
            if res.status_code == 200:
                data = json.loads(res.text)['data']
                status['online'] = int(data['serverInfo']['online'])
                status['idle'] = int(data['serverInfo']['idle'])
                status['rooms'] = data['room']
                return status
        except:
            pass

        try:
            url = "http://%s/info" % server_address
            res = requests.get(url, timeout=1)
            if res.status_code == 200:
                data = json.loads(res.text)
                status = {}
                if 'online' in data:
                    status['online'] = int(data['online'])
        except:
            pass

        try:
            url = "http://" + server_address
            res = requests.get(url, timeout=1)
            if res.status_code == 200:
                data = json.loads(res.text)
                if 'clientCount' in data:
                    status['online'] = int(data['clientCount'])
        except:
            pass

        if 'online' not in status:
            status['online'] = "?"
        if 'idle' not in status:
            status['online'] = "?"

        if show_message:
            self.ErrorDialog('Server not reachable.')

        return status

    def check_selected_server(self):
        try:
            index = self.ui.server_list.currentRow()
            print(index)
            if index == -1:
                raise 'No row selected'
            selected_server = self.ui.server_list.item(index, 2).text()
            print(selected_server)
            while selected_server.startswith('  '):
                index -= 1
                print(index)
                selected_server = self.ui.server_list.item(index, 2).text()
                print(selected_server)
            return selected_server
        except:
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
                    self.ErrorDialog('Server address invalid').exec()
                    self.add_server()
                elif self.check_server_status(server_address, True):
                    db = database()
                    rows = db.select_server(server_address)
                    if rows:
                        self.ErrorDialog('Server already added').exec()
                        self.add_server()
                    else:
                        db.insert_server(server_address)
                        self.refresh_server_list_thread()
                    db.close_connection()
            else:
                self.ErrorDialog('Server address invalid').exec()
                self.add_server()

    def refresh_server_list_thread(self):
        if self.thread is not None and self.thread.is_alive():
            return

        self.thread = threading.Thread(target=self.refresh_server_list)
        self.thread.start()

    def refresh_server_list(self):
        db = database()
        rows = db.select_server('')
        db.close_connection()
        servers_status = {}
        for row in rows:
            address = str(row[1])
            servers_status[address] = self.check_server_status(address, False)
        self.refresh_server_list_signal.emit(rows, servers_status)

    def refresh_server_list_function(self, rows, servers_status):
        server_list = self.ui.server_list

        while server_list.rowCount() > 0:
            server_list.removeRow(0)
        for row in rows:
            server_address = str(row[1])
            server_status = servers_status[server_address]

            list_index = server_list.rowCount()
            server_list.insertRow(list_index)
            server_list.setItem(list_index, 2, QTableWidgetItem(server_address))

            server_list.setItem(list_index, 0, QTableWidgetItem(str(server_status['online'])))
            server_list.setItem(list_index, 1,
                                QTableWidgetItem(str(server_status['idle']) if ('idle' in server_status) else ''))

            if ('rooms' in server_status) and server_status['rooms'] is not None:
                for room in server_status['rooms']:
                    list_index = server_list.rowCount()
                    server_list.insertRow(list_index)
                    server_list.setItem(list_index, 0, QTableWidgetItem(str(room['nodeCount'])))
                    server_list.setItem(list_index, 2, QTableWidgetItem(f"{self.lookup_tid(room['contentId'])} hosted "
                                                                        f"by {room['hostPlayerName']}"))

    def lookup_tid(self, tid):

        for game in self.tids:
            if tid.lower() == game['ID'].lower():
                return game['Name']


# Add server labels
save_label = "Save"
oops_label = "Oops!"
great_label = "Great!"
server_added_label = "Server added!"
sever_address_value_label = "Sever address cannot be empty!"
server_already_exists_label = "Server already exists!"
server_port_values_label = "Server port must be between 0 and 65535"
server_address_example_label = "Server address must be like lan.teknik.app:11451 for example"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    lanplaymanagerwindow = LanplayManagerWindow()
    sys.exit(app.exec())
