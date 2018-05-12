import socket
import threading
import os


ip = '172.18.35.15'
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
    for router_ip, route in Routing_table:
        print(router_ip + route['Distance'] + route['Next_Node'])


def addNeighbour(ip, distance):
    '''添加邻居'''
    temp = {}
    temp['Distance'] = distance
    temp['Next_Node'] = ip
    Routing_Table[ip] = temp

def traceRoute(destination):
    '''打印当前ip并调用下一路由器的该函数'''
    print(ip + '->')
    s = socket.socket()
    # s.bind((ip, command_port))
    router_ip = Routing_Table[destination][Next_Node]
    s.connect(router_ip)
    s.send("traceroute" + destination).encode()

def leave():
    '''该路由器离开网络'''
    global Routing_Table
    for router_ip, route in Routing_table:
        s = socket.socket()
        # s.bind((ip, command_port))
        s.connect(router_ip)
        s.send("leave" + ip).encode()
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
            '''格式例：traceroute 192.168.199.143'''
            destination = command[1]
            traceRoute(destination)
        elif command[0] == "leave":
            '''该路由器离开（损坏）'''
            '''这里需要算法自动执行程序更新路由表'''
            leave()
            os._exit()
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
        if request[0] == "traceroute":
            '''继续上一级的traceroute()继续寻路'''
            destination = request[1]
            traceRoute(destination)
        elif request[0] == "leave":
            '''某一相邻路由器离开网络'''
            '''这里需要算法自动执行程序更新路由表'''
            router_ip = request[1]
            del Routing_Table[router_ip]
            coon.send("Success!").encode()


def main():
    global Routing_Table
    cm = threading.Thread(target = commandMain, args = ())
    cm.start()
    lm = threading.Thread(target = listenMain, args = ())
    lm.start()

if __name__ == "__main__":
    main()