import socket
import threading
import os


ip = '127.0.0.1'
listen_port = 16330
command_port = 16440
exitFlag = 0

Routing_Table = {}

# Route = {
#     'Distance' : '''总距离（字符串）''',
#     'Next_Node' : '''下一节点（字符串）''',
# }

#自动生成路由表
#def makeRoutingTable():

def showRoutingTable():
    '''获取路由表'''
    global Routing_Table
    print("Destination        Distance        Next Node\n")
    for router_ip in Routing_Table:
        print(router_ip + "        " + Routing_Table[router_ip]['Distance'] + "        " + Routing_Table[router_ip]['Next_Node'])

def addNeighbour(ip, distance):
    '''添加邻居'''
    temp = {}
    temp['Distance'] = distance
    temp['Next_Node'] = ip
    Routing_Table[ip] = temp

def traceRoute(myip, destination):
    '''获取从源IP到目的IP的路径'''
    print("最多五个越点跟踪")
    print("从" + myip + "到" + destination + "的路由: ")
    if not(destination in Routing_Table.keys()):
        print("跟踪失败！路由表中没有此目标。")
    ttl = 1
    while ttl <= 5:
        s = socket.socket()
        nextip = Routing_Table[destination]["Next_Node"]
        s.connect((nextip, listen_port))
        s.send("traceroute" + " " + str(ttl) + " "  + myip + " " +destination).encode()
        '''源IP报文格式: traceroute ttl myip destinationip'''
        # responsr = s.recv(1024).decode().split()
        # '''中间路由器回复报文格式: response sourceip curip'''
        # if response[0] == "response" and response[1] == myip:
        #     print(str(ttl) + " " + response[2])
        # if response[2] == destination:
        #     print("跟踪完成")
        #     break
        rp = s.recv(1024).decode()
        print(str(ttl) + " " + rp.split()[2])
        if (rp.split()[2] == destination):
            print("跟踪结束，已找到目标节点。")
            break
        s.close()
        ttl = ttl + 1
        if ttl >5:
            print("失败，太远了")

def leave():
    '''该路由器离开网络'''
    global Routing_Table
    for router_ip in Routing_Table:
        s = socket.socket()
        # s.bind((ip, command_port))
        s.connect((router_ip, listen_port))
        s.send("leave" + " " + ip).encode()
        response = s.recv(1024).decode()
        print(response)
        del Routing_Table[router_ip]

def commandMain():
    '''获取本地命令操作'''
    while True:
        command = input("Please input your command:")
        command = command.split()
        if command[0] == "add":
            '''格式例：add 192.168.199.143 8'''
            '''这里需要算法自动执行程序更新路由表'''
            addNeighbour(command[1], command[2])
        elif command[0] == "show":
            showRoutingTable()
        elif command[0] == "traceroute":
            '''格式例：traceroute ttl myip destinationip'''
            destination = command[1]
            traceRoute(ip, destination)
        elif command[0] == "leave":
            '''该路由器离开（损坏）'''
            '''这里需要算法自动执行程序更新路由表'''
            leave()
            break
        else:
            print("Invalid input!")


def listenMain():
    '''监听获取其他路由器传来的信息'''
    s = socket.socket()
    s.bind((ip, listen_port))
    s.listen(5)
    while True:
        coon, addr = s.accept()
        request = coon.recv(1024).decode().split()
        # if request[0] == "traceroute":
        #     '''继续上一级的traceroute()继续寻路'''
        #     '''源IP报文格式: traceroute ttl sourceip destinationip'''
        #     ttl = int(request[1]) - 1
        #     if ttl == 0:
        #         coon.send("response" + " " + request[2] + " " + ip)
        #     else:
        #         so = socket.socket()
        #         nextip = Routing_Table[request[3]]["Next_Node"]
        #         so.connect((nextip, listen_port))
        #         so.send("traceroute" + " " + str(ttl) + " " + request[2] + " " + request[3]).encode()
        # elif request[0] == "response":
        #     '''中间路由器回复报文格式: response sourceip curip'''
        #     if request[1] == ip:
        #         print(str(ttl) + " " + request[2])
        #     else: 
        #         lastip = Routing_Table[request[1]]["Next_Node"]
        #         so = socket.socket()
        #         so.connect((lastip, listen_port))
        #         so.send(request[0] + " " + request[1] + " " + request[2])
        if request[0] == "traceroute":
            '''traceroute ttl sourceip destinationip'''
            ttl = int(request[1]) - 1
            if ttl == 0:
                '''ttl==0时，向源节点回传response sourceip ttlip'''
                coon.send("response" + " " + request[2] + " " + ip).encode()
            else:
                '''否则继续向下一节点传送traceroute ttl sourceip destinationip'''
                traso = socket.socket()
                nextip = Routing_Table[request[3]]["Next_Node"]
                traso.connect((nextip, listen_port))
                traso.send("traceroute" + " " + str(ttl) + " " + request[2] + " " + request[3]).encode()
                '''等待传回的response报文：response sourceip ttlip，并传给上一个节点'''
                response = traso.recv(1024).encode()
                coon.send(response).encode()
        coon.close()
    s.close()


def main():
    global Routing_Table
    cm = threading.Thread(target = commandMain, args = ())
    cm.start()
    lm = threading.Thread(target = listenMain, args = ())
    lm.start()

if __name__ == "__main__":
    main()