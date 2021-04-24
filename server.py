#!/usr/bin/env python3
import socket
import os
import sys
import signal
import re
import hashlib

def read(slov):
    odpoved = ""
    hlavicka = ""
    status_code = 100
    status_msg = "OK"

    try:
        with open(f'{slov["Mailbox"]}/{slov["Message"]}') as message_file:
            odpoved = message_file.read()
            length = len(odpoved)
            hlavicka = (f'Content-length {length}\n')

    except KeyError:
        status_code, status_msg = (200, 'Bad request')
    except FileNotFoundError:
        status_code, status_msg = (201, 'No such message')
    except OSError:
        status_code, status_msg = (202, 'Read error')
    return (hlavicka, odpoved, status_code, status_msg)


def ls(slov):
    odpoved = ""
    hlavicka = ""
    status_code = 100
    status_msg = "OK"

    try:
        zoznam = os.listdir(slov["Mailbox"])
        dlzka_z = len(zoznam)

        hlavicka = (f'Number-of-messages: {dlzka_z}\n')
        odpoved = "\n".join(zoznam) + "\n"

    except FileNotFoundError:
        status_code, status_msg = (203, 'No such mailbox')
    except KeyError:
        status_code, status_msg = (200, 'Bad request')

    return (hlavicka, odpoved, status_code, status_msg)


def write(slov, subor):
    odpoved = ""
    hlavicka = ""
    status_code = 100
    status_msg = "OK"

    try:
        aa = subor.read(int(slov["Content-length"]))
        bb = hashlib.md5(aa.encode()).hexdigest()

        with open(f'{slov["Mailbox"]}/{bb}', "w") as message_file:
            message_file.write(aa)

    except FileNotFoundError:
        status_code, status_msg = (203, 'No such mailbox')
    except KeyError:
        status_code, status_msg = (200, 'Bad request')
    except ValueError:
        status_code, status_msg = (200, 'Bad request')

    return (hlavicka, odpoved, status_code, status_msg)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 9999))
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
s.listen(5)

while True:
    connected_socket, address = s.accept()
    print(f'spojenie z {address}')
    pid_chld = os.fork()
    if pid_chld == 0:
        s.close()
        f = connected_socket.makefile(mode='rw', encoding='utf-8')

        while True:
            hlavicka = ""
            odpoved = ""
            slov = {}

            method = f.readline().strip()
            if not method:
                break

            stroka = f.readline()

            while stroka != "\n":
                a=0
                riadok=stroka.strip()
                if riadok.find(" ")!=-1:
                    hlavicka=""
                    obsah=""
                    a=a+1
                if not riadok.isascii():
                    hlavicka=""
                    obsah=""
                    a=a+1
                try:
                    riadok=riadok.split(":")
                except:
                    hlavicka=""
                    obsah=""
                    a=a+1
                if len(riadok)!=2:
                    hlavicka=""
                    obsah=""
                    a=a+1
                if(riadok[0].find("/")!=-1):
                    hlavicka=""
                    obsah=""
                    a=a+1
                if(a==0):
                    hlavicka=riadok[0]
                    obsah=riadok[1]
                slov[hlavicka] = obsah
                stroka = f.readline()
                a=0

            if len(slov) > 2:
                status_code, status_msg = (200, 'Bad request')


            for a in slov:
                if a == "" or slov[a] == "":
                    status_code, status_msg = (200, 'Bad request')

            status_code, status_ms = (100, 'OK')

            if status_code == 100:

                if method == 'READ':
                    hlavicka, odpoved, status_code, status_msg = read(slov)

                elif method == 'LS':
                    hlavicka,odpoved, status_code, status_msg = ls(slov)

                elif method == 'WRITE':
                    hlavicka, odpoved, status_code, status_msg = write(slov, f)

                else:
                    status_code, status_msg = (204, 'Unknown method')
                    f.write(f"{status_code} {status_msg}\n")
                    f.flush()
                    sys.exist(0)
            f.write(f"{status_code} {status_msg}\n")
            f.write(hlavicka)
            f.write("\n")
            f.write(odpoved)
            f.flush()
        f.close()
        sys.exit(0)
    else:
        connected_socket.close()
