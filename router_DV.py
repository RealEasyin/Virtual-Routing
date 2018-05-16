import socket
import threading
import os


ip = 'aaa'
listen_port = 20020
exitFlag = 0
default_route = {"Distance":99999, "Next_None": None}
Routing_Table = {}

n_table ={}

lock = threading.Lock()

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


def renewPath():
    addPk = "PATH "+str(Routing_Table)
    for t in n_table.keys():
        if n_table[t]<99999:
            s = socket.socket()
            s.connect((t, listen_port))
            s.send(addPk.encode())


def addPath(nip, distance):
    flag = Routing_Table.get(nip, default_route)["Distance"] < 99999 
    tmp = {}
    if flag:
        tmp = Routing_Table[nip]
    Routing_Table[nip] = {"Distance": distance, "Next_Node": nip}
    n_table[nip] = distance
    renewPath()
    if flag and tmp["Next_Node"]!=nip and tmp["Distance"]<distance:
        Routing_Table[nip] = tmp

def askCost(sip, dip):
    s = socket.socket()
    s.connect((sip, listen_port))
    s.send(("ASK "+dip).encode())
    a = s.recv(1024).decode()
    return int(a.lstrip("ANS "))

def ansCost(conn, pk):
    pk = pk.lstrip("ASK ")
    conn.send(("ANS "+str(Routing_Table.get(pk, default_route)["Distance"])).encode())

def renewListener(sip, pk):
    flag = False
    pk = pk.lstrip("PATH ")
    nrt = eval(pk)

    if nrt.get(ip, default_route)["Next_Node"] == ip:
        n_table[sip] = nrt.get(ip, default_route)["Distance"]
        if n_table[sip] < Routing_Table.get(sip, default_route)["Distance"] or Routing_Table.get(sip, default_route)["Next_Node"]==sip:
            if Routing_Table.get(sip, default_route) != {"Distance": n_table[sip], "Next_Node": sip}:
                flag = True
                Routing_Table[sip] = {"Distance": n_table[sip], "Next_Node": sip}
    allKey = list(Routing_Table.keys()) + list(nrt.keys())
    for k in allKey:
        if k == ip or k==sip:
            continue
        else:
            m = 99999
            n = 'NO'
            for t in n_table.keys():
                if n_table[t]<99999:
                    ttpp = 0
                    if t == k:
                        ttpp = n_table[t]
                    else:
                        ttpp = askCost(t, k) + n_table[t]
                    if ttpp < m:
                        m = ttpp
                        n = t
            if m!=Routing_Table.get(k, default_route)["Distance"] and k!=sip:
                flag = True
            Routing_Table[k] = {"Distance": m, "Next_Node": n}

    if flag:
        renewPath()
    return

            

def newPath(nip, distance):
    addPath(nip, distance)


def leave():
    for t in Routing_Table.keys():
        Routing_Table[t]["Distance"] = 99999
    for t in n_table.keys():
        Routing_Table[t]["Distance"] = 99999
        if t in n_table.keys():
            Routing_Table[t]["Next_Node"] = t
    renewPath()




def showRoutingTable():
    global Routing_Table
    print("Destination        Distance        Next Node")
    for router_ip in Routing_Table:
        if Routing_Table[router_ip]["Distance"]<99999:
            print(router_ip + "        " + str(Routing_Table[router_ip]['Distance']) + "        " + Routing_Table[router_ip]['Next_Node'])
    print("\n")

def commandMain():
    while True:
        command = input()
        command = command.split()
        if command[0] == "add" and len(command)==3:
            lock.acquire()
            addPath(command[1], int(command[2]))
            lock.release()
        elif command[0] == "show":
            lock.acquire()
            showRoutingTable()
            lock.release()
        elif command[0] == "leave":
            lock.acquire()
            leave()
            lock.release()
            os._exit(0)
        elif command[0] == "tracert" and len(command)==2:
            traceRoute(ip, command[1])
        else:
            print("Invalid input!")

def echoListener(coon, addr):
    request = coon.recv(1024).decode()
    print(str(addr)+" REQUEST: "+request)
    if request.startswith("PATH "):
        lock.acquire()
        renewListener(addr[0], request)
        lock.release()
    elif request.startswith("ASK "):
        ansCost(coon, request)
######
    elif request.startswith("traceroute"):
        request = request.split()
        ttl = int(request[1]) - 1
        if ttl == 0:
            coon.send(("response" + " " + request[2] + " " + ip).encode())
        else:
            traso = socket.socket()
            nextip = Routing_Table[request[3]]["Next_Node"]
            traso.connect((nextip, listen_port))
            traso.send(("traceroute" + " " + str(ttl) + " " + request[2] + " " + request[3]).encode())
            response = traso.recv(1024).decode()
            coon.send((response).encode())
######
    coon.close()


def listenMain():
    s = socket.socket()
    s.bind((ip, listen_port))
    s.listen(5)
    while True:
        coon, addr = s.accept()
        el = threading.Thread(target=echoListener, args=(coon, addr))
        el.start()


def main():
    global Routing_Table
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