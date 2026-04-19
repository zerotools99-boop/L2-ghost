from flask import Flask, request, jsonify
from config import *
from encrypt import *
import threading
import time
import socket
import json
import base64
import requests
from datetime import datetime
import jwt
from google.protobuf.timestamp_pb2 import Timestamp
import errno
import select
import atexit
import os
import signal
import sys
import psutil
import urllib3
import random
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
clients = {}
shutting_down = False

def parse_ghost_names(ghost_names_param):
    """Parse ghost names from either {name1}{name2} or comma-separated list"""
    if not ghost_names_param:
        return []

    if '{' in ghost_names_param and '}' in ghost_names_param:
        names = re.findall(r'\{(.*?)\}', ghost_names_param)
        return names

    names = [name.strip() for name in ghost_names_param.split(',') if name.strip()]
    return names

def AuTo_ResTartinG():
    return

def ResTarT_BoT():
    return

class TcpBotConnectMain:
    def __init__(self, account_id, password):
        self.account_id = account_id
        self.password = password
        self.key = None
        self.iv = None
        self.socket_client = None
        self.clientsocket = None
        self.running = False
        self.connection_attempts = 0
        self.max_connection_attempts = 2
        self.AutH = None
        self.DaTa2 = None
        self.sockf1_thread = None

    def run(self):
        if shutting_down:
            return

        if not hasattr(self, "auto_restart_thread_started"):
            t = threading.Thread(target=AuTo_ResTartinG, daemon=True)
            t.start()
            self.auto_restart_thread_started = True

        self.running = True
        self.connection_attempts = 0

        while (
            self.running
            and not shutting_down
            and self.connection_attempts < self.max_connection_attempts
        ):
            try:
                self.connection_attempts += 1
                print(
                    f"[{self.account_id}] Connection attempt {self.connection_attempts}/{self.max_connection_attempts}"
                )
                self.get_tok()
                break
            except Exception as e:
                print(f"[{self.account_id}] Error in run: {e}")
                if self.connection_attempts >= self.max_connection_attempts:
                    print(
                        f"[{self.account_id}] Reached max connection attempts. Stopping."
                    )
                    self.stop()
                    break
                print(f"[{self.account_id}] Retrying after 5 seconds...")
                time.sleep(5)

    def stop(self):
        self.running = False
        try:
            if self.clientsocket:
                self.clientsocket.close()
        except:
            pass
        try:
            if self.socket_client:
                self.socket_client.close()
        except:
            pass
        print(f"[{self.account_id}] Client stopped")

    def restart(self, delay=5):
        if shutting_down:
            return
        print(f"[{self.account_id}] Restarting client in {delay} seconds...")
        time.sleep(delay)
        self.run()

    def is_socket_connected(self, sock):
        try:
            if sock is None:
                return False
            writable = select.select([], [sock], [], 0.1)[1]
            if sock in writable:
                sock.send(b"")
                return True
            return False
        except (OSError, socket.error) as e:
            if e.errno == errno.EBADF:
                print(f"[{self.account_id}] Socket bad file descriptor")
            return False
        except Exception as e:
            print(f"[{self.account_id}] Socket check error: {e}")
            return False

    def ensure_connection(self):
        if not self.is_socket_connected(self.socket_client) and self.running:
            print(f"[{self.account_id}] Attempting to reconnect")
            self.restart(delay=2)
            return False
        return True

    def sockf1(self, tok, online_ip, online_port, packet, key, iv):
        while self.running and not shutting_down:
            try:
                self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_client.settimeout(30)
                self.socket_client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

                online_port = int(online_port)
                print(f"[{self.account_id}] Connecting to {online_ip}:{online_port}...")
                self.socket_client.connect((online_ip, online_port))
                print(f"[{self.account_id}] Connected to {online_ip}:{online_port}")
                self.socket_client.send(bytes.fromhex(tok))
                print(f"[{self.account_id}] Token sent successfully")

                while (
                    self.running
                    and not shutting_down
                    and self.is_socket_connected(self.socket_client)
                ):
                    try:
                        readable, _, _ = select.select(
                            [self.socket_client], [], [], 1.0
                        )
                        if self.socket_client in readable:
                            self.DaTa2 = self.socket_client.recv(99999)
                            if not self.DaTa2:
                                print(
                                    f"[{self.account_id}] Server closed connection gracefully"
                                )
                                break

                            if (
                                "0500" in self.DaTa2.hex()[0:4]
                                and len(self.DaTa2.hex()) > 30
                            ):
                                try:
                                    self.packet = json.loads(
                                        DeCode_PackEt(
                                            f'08{self.DaTa2.hex().split("08", 1)[1]}'
                                        )
                                    )
                                    self.AutH = self.packet["5"]["data"]["7"]["data"]
                                    print(
                                        f"[{self.account_id}] 0500 packet received, AutH={self.AutH}"
                                    )
                                    
                                except Exception as parse_err:
                                    print(
                                        f"[{self.account_id}] Error parsing 0500: {parse_err}"
                                    )

                    except socket.timeout:
                        continue
                    except (OSError, socket.error) as e:
                        if e.errno == errno.EBADF:
                            print(
                                f"[{self.account_id}] Bad file descriptor, reconnecting..."
                            )
                            break
                        else:
                            print(
                                f"[{self.account_id}] Socket error: {e}. Reconnecting..."
                            )
                            break
                    except Exception as e:
                        print(
                            f"[{self.account_id}] Unexpected error: {e}. Reconnecting..."
                        )
                        break

            except socket.timeout:
                print(f"[{self.account_id}] Connection timeout, retrying...")
            except (OSError, socket.error) as e:
                if e.errno == errno.EBADF:
                    print(f"[{self.account_id}] Bad file descriptor during connection")
                else:
                    print(f"[{self.account_id}] Connection error: {e}")
            except Exception as e:
                print(f"[{self.account_id}] Unexpected error: {e}")

            
            if self.running and not shutting_down:
                print(f"[{self.account_id}] Reconnecting to online server in 2 seconds...")
                time.sleep(2)

    def connect(
        self, tok, packet, key, iv, whisper_ip, whisper_port, online_ip, online_port
    ):
        while self.running and not shutting_down:
            try:
                self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.clientsocket.settimeout(None)
                self.clientsocket.connect((whisper_ip, int(whisper_port)))
                print(f"[{self.account_id}] Connected to {whisper_ip}:{whisper_port}")
                self.clientsocket.send(bytes.fromhex(tok))
                self.data = self.clientsocket.recv(1024)
                self.clientsocket.send(get_packet2(self.key, self.iv))
                self.sockf1_thread = threading.Thread(
                    target=self.sockf1,
                    args=(tok, online_ip, online_port, "anything", key, iv),
                    daemon=True
                )
                self.sockf1_thread.start()

                while self.running and not shutting_down:
                    dataS = self.clientsocket.recv(1024)
                    if not dataS:
                        break
            except Exception as e:
                if not shutting_down:
                    print(
                        f"[{self.account_id}] Error in connect: {e}. Retrying in 3 seconds..."
                    )
                    time.sleep(3)
            finally:
                if self.clientsocket:
                    try:
                        self.clientsocket.close()
                    except:
                        pass

                if self.running and not shutting_down:
                    print(f"[{self.account_id}] Reconnecting to whisper server in 2 seconds...")
                    time.sleep(2)

    def parse_my_message(self, serialized_data):
        MajorLogRes = MajorLoginRes()
        MajorLogRes.ParseFromString(serialized_data)
        timestamp = MajorLogRes.kts
        key = MajorLogRes.ak
        iv = MajorLogRes.aiv
        BASE64_TOKEN = MajorLogRes.token
        timestamp_obj = Timestamp()
        timestamp_obj.FromNanoseconds(timestamp)
        timestamp_seconds = timestamp_obj.seconds
        timestamp_nanos = timestamp_obj.nanos
        combined_timestamp = timestamp_seconds * 1_000_000_000 + timestamp_nanos
        return combined_timestamp, key, iv, BASE64_TOKEN

    def GET_PAYLOAD_BY_DATA(self, JWT_TOKEN, NEW_ACCESS_TOKEN, date):
        token_payload_base64 = JWT_TOKEN.split(".")[1]
        token_payload_base64 += "=" * ((4 - len(token_payload_base64) % 4) % 4)
        decoded_payload = base64.urlsafe_b64decode(token_payload_base64).decode("utf-8")
        decoded_payload = json.loads(decoded_payload)
        NEW_EXTERNAL_ID = decoded_payload["external_id"]
        SIGNATURE_MD5 = decoded_payload["signature_md5"]
        now = datetime.now()
        now = str(now)[: len(str(now)) - 7]
        formatted_time = date
        payload = bytes.fromhex(Payload1A13)
        payload = payload.replace(b"2025-08-02 17:15:04", str(now).encode())
        payload = payload.replace(
            b"10e299be9f8199bd50f8c52bbae4695bc1935563ba17d3859c97237bd45cb428",
            NEW_ACCESS_TOKEN.encode("UTF-8"),
        )
        payload = payload.replace(
            b"b70245b92be827af56d8932346f351f2", NEW_EXTERNAL_ID.encode("UTF-8")
        )
        payload = payload.replace(
            b"7428b253defc164018c604a1ebbfebdf", SIGNATURE_MD5.encode("UTF-8")
        )
        PAYLOAD = payload.hex()
        PAYLOAD = encrypt_api(PAYLOAD)
        PAYLOAD = bytes.fromhex(PAYLOAD)
        whisper_ip, whisper_port, online_ip, online_port = self.GET_LOGIN_DATA(
            JWT_TOKEN, PAYLOAD
        )
        return whisper_ip, whisper_port, online_ip, online_port

    def GET_LOGIN_DATA(self, JWT_TOKEN, PAYLOAD):
        url = GetLoginDataRegion
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {JWT_TOKEN}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FreeFireVersion,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)",
            "Host": "client.ind.freefiremobile",
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate, br",
        }

        max_retries = 3
        attempt = 0
        while attempt < max_retries and not shutting_down:
            try:
                response = requests.post(
                    url, headers=headers, data=PAYLOAD, verify=False
                )
                response.raise_for_status()
                x = response.content.hex()
                json_result = get_available_room(x)
                parsed_data = json.loads(json_result)
                whisper_address = parsed_data["32"]["data"]
                online_address = parsed_data["14"]["data"]
                online_ip = online_address[: len(online_address) - 6]
                whisper_ip = whisper_address[: len(whisper_address) - 6]
                online_port = int(online_address[len(online_address) - 5 :])
                whisper_port = int(whisper_address[len(whisper_address) - 5 :])
                return whisper_ip, whisper_port, online_ip, online_port
            except requests.RequestException as e:
                print(
                    f"[{self.account_id}] Request failed: {e}. Attempt {attempt + 1} of {max_retries}. Retrying..."
                )
                attempt += 1
                time.sleep(2)
        print(f"[{self.account_id}] Failed to get login data after multiple attempts.")
        return None, None, None, None

    def guest_token(self, uid, password):
        url = "https://ffmconnect.ggpolarbear.com/oauth/guest/token/grant"
        headers = {
            "Host": "ffmconnect.ggpolarbear.com",
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 10;en;EN;)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close",
        }
        data = {
            "uid": f"{uid}",
            "password": f"{password}",
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067",
        }
        response = requests.post(url, headers=headers, data=data)
        data = response.json()
        NEW_ACCESS_TOKEN = data["access_token"]
        NEW_OPEN_ID = data["open_id"]
        OLD_ACCESS_TOKEN = (
            "10e299be9f8199bd50f8c52bbae4695bc1935563ba17d3859c97237bd45cb428"
        )
        OLD_OPEN_ID = "b70245b92be827af56d8932346f351f2"
        time.sleep(0.2)
        data = self.TOKEN_MAKER(
            OLD_ACCESS_TOKEN, NEW_ACCESS_TOKEN, OLD_OPEN_ID, NEW_OPEN_ID, uid
        )
        return data

    def TOKEN_MAKER(
        self, OLD_ACCESS_TOKEN, NEW_ACCESS_TOKEN, OLD_OPEN_ID, NEW_OPEN_ID, id
    ):
        headers = {
            "X-Unity-Version": "2018.4.11f1",
            "ReleaseVersion": FreeFireVersion,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-GA": "v1 1",
            "Content-Length": "928",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; ASUS_Z01QD Build/QKQ1.190825.002)",
            "Host": "loginbp.ggpolarbear.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        data = bytes.fromhex(Payload1A13)
        data = data.replace(b"1.123.1", b"1.123.1")
        data = data.replace(OLD_OPEN_ID.encode(), NEW_OPEN_ID.encode())
        data = data.replace(OLD_ACCESS_TOKEN.encode(), NEW_ACCESS_TOKEN.encode())
        hex_data = data.hex()
        encrypted_data = encrypt_api(hex_data)
        Final_Payload = bytes.fromhex(encrypted_data)
        URL = MajorLoginRegion
        RESPONSE = requests.post(URL, headers=headers, data=Final_Payload, verify=False)
        combined_timestamp, key, iv, BASE64_TOKEN = self.parse_my_message(
            RESPONSE.content
        )
        if RESPONSE.status_code == 200:
            if len(RESPONSE.text) < 10:
                return False
            whisper_ip, whisper_port, online_ip, online_port = self.GET_PAYLOAD_BY_DATA(
                BASE64_TOKEN, NEW_ACCESS_TOKEN, 1
            )
            self.key = key
            self.iv = iv
            print(f"[{self.account_id}] Key: {key}, IV: {iv}")
            return (
                BASE64_TOKEN,
                key,
                iv,
                combined_timestamp,
                whisper_ip,
                whisper_port,
                online_ip,
                online_port,
            )
        else:
            return False

    def get_tok(self):
        token_data = self.guest_token(self.account_id, self.password)
        if not token_data:
            print(f"[{self.account_id}] Failed to get token")
            self.restart()
            return

        token, key, iv, Timestamp, whisper_ip, whisper_port, online_ip, online_port = (
            token_data
        )
        print(f"[{self.account_id}] Whisper: {whisper_ip}:{whisper_port}")

        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            account_id = decoded.get("account_id")
            encoded_acc = hex(account_id)[2:]
            hex_value = self.dec_to_hex(Timestamp)
            time_hex = hex_value
            BASE64_TOKEN_ = token.encode().hex()
            print(f"[{self.account_id}] Token decoded. Account ID: {account_id}")
        except Exception as e:
            print(f"[{self.account_id}] Error processing token: {e}")
            self.restart()
            return

        try:
            head = hex(len(encrypt_packet(BASE64_TOKEN_, key, iv)) // 2)[2:]
            length = len(encoded_acc)
            zeros = "00000000"
            if length == 9:
                zeros = "0000000"
            elif length == 8:
                zeros = "00000000"
            elif length == 10:
                zeros = "000000"
            elif length == 7:
                zeros = "000000000"
            else:
                print(f"[{self.account_id}] Unexpected length encountered")
            head = f"0115{zeros}{encoded_acc}{time_hex}00000{head}"
            final_token = head + encrypt_packet(BASE64_TOKEN_, key, iv)
        except Exception as e:
            print(f"[{self.account_id}] Error creating final token: {e}")
            self.restart()
            return

        self.connect(
            final_token,
            "anything",
            key,
            iv,
            whisper_ip,
            whisper_port,
            online_ip,
            online_port,
        )
        return final_token, key, iv

    def dec_to_hex(self, ask):
        ask_result = hex(ask)
        final_result = str(ask_result)[2:]
        if len(final_result) == 1:
            final_result = "0" + final_result
            return final_result
        else:
            return final_result

    def execute_command(self, command, *args):
        if command == "/XRRR":
            try:
                if not self.socket_client or not self.is_socket_connected(
                    self.socket_client
                ):
                    return "Socket not connected, please wait for connection..."

                team_code = args[0] if len(args) > 0 else None
                account_name = args[1] if len(args) > 1 else "UnknownGhost"

                if not team_code:
                    return "No team code provided for /XRRR"

                print(
                    f"[{self.account_id}] Executing /XRRR for team code {team_code} with name {account_name}"
                )
                sys.stdout.flush()

                self.socket_client.send(
                    GenJoinSquadsPacket(team_code, self.key, self.iv)
                )
                time.sleep(0.5)
                start_time = time.time()
                got_0500 = False
                idT = None
                sq = None

                while not got_0500 and (time.time() - start_time) < 10:
                    if (
                        self.DaTa2
                        and len(self.DaTa2.hex()) >= 4
                        and "0500" in self.DaTa2.hex()[0:4]
                    ):
                        try:
                            self.dT = json.loads(
                                DeCode_PackEt(self.DaTa2.hex()[10:])
                            )
                            if (
                                "5" in self.dT
                                and "data" in self.dT["5"]
                                and "31" in self.dT["5"]["data"]
                                and "1" in self.dT["5"]["data"]
                            ):
                                sq = self.dT["5"]["data"]["31"]["data"]
                                idT = self.dT["5"]["data"]["1"]["data"]
                                got_0500 = True
                                print(
                                    f"[{self.account_id}] Got 0500 with ID: {idT}"
                                )
                                break
                        except Exception as parse_err:
                            print(
                                f"[{self.account_id}] Error parsing 0500: {parse_err}"
                            )
                    time.sleep(0.1)

                if not got_0500:
                    return f"Failed to get 0500 for team code {team_code} within timeout"

                self.socket_client.send(ExiT("000000", self.key, self.iv))
                time.sleep(0.1)

                self.socket_client.send(
                    ghost_pakcet(idT, account_name, sq, self.key, self.iv)
                )
                time.sleep(0.1)
                self.socket_client.send(ExiT("000000", self.key, self.iv))

                return f"Ghost {account_name} successfully joined squad {idT} (original code {team_code})"

            except Exception as e:
                print(f"[{self.account_id}] Error in execute_command: {e}")
                return f"Error executing command: {e}"
        else:
            return f"Unknown command: {command}"

def load_accounts(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def cleanup():
    global shutting_down
    shutting_down = True
    print("Shutting down all clients...")
    for account_id, client in list(clients.items()):
        client.stop()
        del clients[account_id]
    print("Cleanup completed")

@app.route("/")
def home():
    return "OK", 200

@app.route("/start_client", methods=["GET"])
def start_client():
    if shutting_down:
        return jsonify({"error": "Server is shutting down"}), 503

    account_id = request.args.get("account_id")
    password = request.args.get("password")

    if not account_id or not password:
        return jsonify({"error": "Account ID and password are required"}), 400

    if account_id in clients:
        return jsonify({"error": "Client already running"}), 400

    client = TcpBotConnectMain(account_id, password)
    clients[account_id] = client

    client_thread = threading.Thread(target=client.run)
    client_thread.daemon = True
    client_thread.start()

    return jsonify({"message": f"Client {account_id} started successfully"}), 200

@app.route("/stop_client", methods=["GET"])
def stop_client():
    if shutting_down:
        return jsonify({"error": "Server is shutting down"}), 503

    account_id = request.args.get("account_id")

    if not account_id:
        return jsonify({"error": "Account ID is required"}), 400

    if account_id not in clients:
        return jsonify({"error": "Client not found"}), 404

    client = clients[account_id]
    client.stop()
    del clients[account_id]

    return jsonify({"message": f"Client {account_id} stopped successfully"}), 200

@app.route("/execute_command", methods=["GET"])
def execute_command():
    if shutting_down:
        return jsonify({"error": "Server is shutting down"}), 503

    account_id = request.args.get("account_id")
    command = request.args.get("command")
    client_id = request.args.get("client_id")
    name = request.args.get("name")

    if not account_id or not command:
        return jsonify({"error": "Account ID and command are required"}), 400

    if account_id not in clients:
        return jsonify({"error": "Client not found"}), 404

    client = clients[account_id]

    args = []
    if client_id:
        try:
            args.append(int(client_id))
        except ValueError:
            return jsonify({"error": "Invalid client_id format"}), 400

    if name:
        args.append(name)

    result = client.execute_command(command, *args)

    return jsonify({"result": result}), 200

@app.route("/list_clients", methods=["GET"])
def list_clients():
    return jsonify({"clients": list(clients.keys())}), 200

@app.route("/execute_command_all", methods=["GET"])
def execute_command_all():
    if shutting_down:
        return jsonify({"error": "Server is shutting down"}), 503

    command = request.args.get("command")
    ghost_names_param = request.args.get("ghost_names", None)

    if not command:
        return jsonify({"error": "Command parameter is required"}), 400

    command = command.strip()
    cmd = None
    arg = None
    if "=" in command:
        parts = command.split("=", 1)
        cmd = parts[0].strip()
        arg = parts[1].strip() if len(parts) > 1 else None
    else:
        parts = command.split(" ", 1)
        cmd = parts[0].strip()
        arg = parts[1].strip() if len(parts) > 1 else None

    ghost_names_list = parse_ghost_names(ghost_names_param)

    sorted_clients = sorted(clients.items(), key=lambda x: int(x[0]))

    results = {}
    for idx, (account_id, client) in enumerate(sorted_clients):

        if ghost_names_list:
            if len(ghost_names_list) == 1:
                account_name = ghost_names_list[0]
            else:
                if idx < len(ghost_names_list):
                    account_name = ghost_names_list[idx]
                else:
                    account_name = ghost_names_list[-1]
        else:
            account_name = str(account_id)

        if cmd == "/XRRR" and arg:
            result = client.execute_command(cmd, arg, account_name)
            results[account_id] = f"Dev: ROHIT | {result} | Name: {account_name}"
        else:
            results[account_id] = f"Unknown or invalid command: {command} | Name: {account_name}"

    return jsonify({"results": results})

@app.route("/ghost_all", methods=["GET"])
def ghost_all():
    if shutting_down:
        return jsonify({"error": "Server is shutting down"}), 503

    teamcode = request.args.get("teamcode")
    ghost_names_param = request.args.get("ghost_names", "")

    if not teamcode:
        return jsonify({"error": "teamcode parameter is required"}), 400

    ghost_names_list = parse_ghost_names(ghost_names_param)

    sorted_clients = sorted(clients.items(), key=lambda x: int(x[0]))

    results = {}

    for idx, (account_id, client) in enumerate(sorted_clients):

        if ghost_names_list:
            if len(ghost_names_list) == 1:
                account_name = ghost_names_list[0]
            else:
                account_name = ghost_names_list[idx] if idx < len(ghost_names_list) else ghost_names_list[-1]
        else:
            account_name = str(account_id)

        result = client.execute_command("/XRRR", teamcode, account_name)
        results[account_id] = f"Dev: ROHIT | {result} | Name: {account_name}"

    return jsonify({"results": results})

@app.route("/ghost", methods=["GET"])
def ghost():
    if shutting_down:
        return jsonify({"error": "Server is shutting down"}), 503

    teamcode = request.args.get("teamcode")
    ghost_name = request.args.get("ghost_name")

    if not teamcode:
        return jsonify({"error": "teamcode parameter is required"}), 400

    if not ghost_name:
        ghost_name = "Ghost"

    # pick FIRST available client only
    if not clients:
        return jsonify({"error": "No clients available"}), 500

    account_id, client = next(iter(sorted(clients.items(), key=lambda x: int(x[0]))))

    result = client.execute_command("/XRRR", teamcode, ghost_name)

    return jsonify({
        "account_id": account_id,
        "result": f"Dev: ROHIT | {result} | Name: {ghost_name}"
    })

@app.route("/shutdown", methods=["GET"])
def shutdown_server():
    global shutting_down
    shutting_down = True
    cleanup()
    return jsonify({"message": "Server shutdown initiated"}), 200

def signal_handler(sig, frame):
    print("Received shutdown signal")
    cleanup()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)

    if os.getenv("RENDER") != "true":
        try:
            accounts = load_accounts("accounts.json")
            for account_id, password in accounts.items():
                client = TcpBotConnectMain(account_id, password)
                clients[account_id] = client
                threading.Thread(target=client.run, daemon=True).start()
                time.sleep(2)
        except FileNotFoundError:
            print("No accounts file found. Starting without preloaded accounts.")

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=False)