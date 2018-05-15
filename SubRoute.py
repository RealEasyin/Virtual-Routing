import socket
import threading
import os

ip = 'aaa'
listen_port = 20020
boss = ('192.168.199.211', 12306)


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip

def traceRoute(myip, destination):
    #'''获取从源IP到目的IP的路径'''
    s = socket.socket()
    s.connect(boss)
    s.send("all".encode())
    request = s.recv(1024).decode()
    request = request.lstrip("all ")
    Routing_Table = eval(request)
    print("最多五个越点跟踪")
    print("从" + myip + "到" + destination + "的路由: ")
    if not(destination in Routing_Table.keys()):
        print("跟踪失败！路由表中没有此目标。")
        return
    ttl = 1
    while ttl <= 5:
        s = socket.socket()
        nextip = Routing_Table[destination]["Next_Node"]
        s.connect((nextip, listen_port))
        s.send(("traceroute" + " " + str(ttl) + " "  + myip + " " +destination).encode())
        rp = s.recv(1024).decode()
        print(str(ttl) + " " + rp.split()[2])
        if (rp.split()[2] == destination):
            print("跟踪结束，已找到目标节点。")
            break
        s.close()
        ttl = ttl + 1
    if ttl > 5:
        print("失败，太远了")

def addPath(dip, dis):
    s = socket.socket()
    s.connect(boss)
    s.send(("path "+dip+" "+str(dis)).encode())

def delPath(dip):
    addPath(dip, 99999)

def askPath(dip):
    s = socket.socket()
    s.connect(boss)
    s.send(("ask "+dip).encode())
    request = s.recv(1024).decode().lstrip("ans ").split()
    return request[0], int(request[1])

def showRoutingTable():
    s = socket.socket()
    s.connect(boss)
    s.send("all".encode())
    request = s.recv(1024).decode()
    request = request.lstrip("all ")
    route_table = eval(request)
    print("Destantion          Via                   Cost")
    for t in route_table.keys():
        if (route_table[t]["Distance"]<99999):
            print( t + "      " + route_table[t]["Next_Node"] + "       " + str(route_table[t]["Distance"]))

def leave():
    s = socket.socket()
    s.connect(boss)
    s.send("all".encode())
    request = s.recv(1024).decode()
    request = request.lstrip("all ")
    route_table = eval(request)
    for t in route_table.keys():
        delPath(t)


def commandMain():
    while True:
        command = input()
        if command.startswith("add "):
            dip = command.lstrip("add ").split()[0]
            dis = command.lstrip("add ").split()[1]
            if dip==None or dis==None:
                print("Invalid input!")
                continue
            addPath(dip, dis)
        elif command.startswith("del "):
            dip = command.lstrip("del ").split()[0]
            if dip==None:
                print("Invalid input!")
                continue
            delPath(dip)
        elif command == "show":
            showRoutingTable()
        elif command.startswith("tracert"):
            traceRoute(ip, command.split()[1])
        elif command == "leave":
            leave()
            os._exit(0)
        else:
            print("Invalid input!")


def listenMain():
    s = socket.socket()
    s.bind((ip, listen_port))
    s.listen(5)
    while True:
        coon, addr = s.accept()
        request = coon.recv(1024).decode()
        print(str(addr)+" REQUEST: "+request)
        if request.startswith("traceroute"):
            request = request.split()
            ttl = int(request[1]) - 1
            if ttl == 0:
                coon.send(("response" + " " + request[2] + " " + ip).encode())
            else:
                traso = socket.socket()
                nextip, ddd = askPath(request[3])
                traso.connect((nextip, listen_port))
                traso.send(("traceroute" + " " + str(ttl) + " " + request[2] + " " + request[3]).encode())
                response = traso.recv(1024).decode()
                coon.send((response).encode())
######

        coon.close()


def main():
    global ip
    ip = get_host_ip()
    print("I'm "+ip)
    # n_table[ip] = 99999
    cm = threading.Thread(target = commandMain, args = ())
    cm.start()
    lm = threading.Thread(target = listenMain, args = ())
    lm.start()

if __name__ == "__main__":
    main()