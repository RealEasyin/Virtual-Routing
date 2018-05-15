import socket
import threading
import os
import operator
import time
import random

ip = '192.168.199.211'
listen_port = 16330
command_port = 16440
exitFlag = 0
lock=threading.Lock()

Routing_Table = {}
Graph_Table={}
Boardcast_list=[]
'''
Graph_Table {route:distance}
'''


# Route = {
#     'Distance' : '''总距离（字符串）''',
#     'Next_Node' : '''下一节点（字符串）''',
# }

#自动生成路由表
#def makeRoutingTable():

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def showRoutingTable():
    '''获取路由表'''
    #global Routing_Table
    print("Destination        Distance        Next Node\n")
    for router_ip, route in Routing_Table.items():
        print(router_ip ,"   ",route['Distance'] ,"    ",route['Next_Node'])

def LS():
	global ip
	global Routing_Table
    #拓扑图的点集
	N=set()
    #当前路由器到其他路由器的距离
	D={}
    #初始化
	for neihbour , distance in Graph_Table[ip].items():
		temp={}
		temp["Distance"]=distance
		temp["Next_Node"]=neihbour
		Routing_Table[neihbour]=temp
	for route in Graph_Table.keys():
		N.add(route)
		D[route]=99999
	for neihbour , distance in Graph_Table[ip].items():
		D[neihbour]=distance
	D[ip]=0
	N.remove(ip)
	lock.acquire()
	while N :
		min_route=99999
		next_route=0
		for route in N:
			next_route=route if D[route]<min_route else next_route
			min_route=D[route] if D[route]<min_route else min_route
			#print(D[route],next_route,min_route,route)
		if next_route==0:
			break
		N.remove(next_route)
		Routing_Table[next_route]["Distance"]=min_route
		for neihbour in Graph_Table[next_route].keys():
			if not neihbour in Routing_Table:
				Routing_Table[neihbour]={}
			#print(neihbour," ",next_route)
			#print(Graph_Table)
			Routing_Table[neihbour]["Next_Node"]=Routing_Table[next_route]["Next_Node"] if D[next_route]+Graph_Table[next_route][neihbour]<D[neihbour] else Routing_Table[neihbour]["Next_Node"]
			D[neihbour]=D[next_route]+Graph_Table[next_route][neihbour] if D[next_route]+Graph_Table[next_route][neihbour]<D[neihbour] else D[neihbour]
	delet_list=[]
	for route in Routing_Table.keys():
		Routing_Table[route]["Distance"]=D[route]
		if D[route]>=99999:
			delet_list.append(route)
	for route in delet_list:
		del Routing_Table[route]
	lock.release()
	#showRoutingTable()
 	#新的route_table生成完成		

#增加邻居
def addNeighbour(Nei_ip, distance):
	'''添加邻居'''
	global ip
	#print(Nei_ip)
	distance=int(distance)
	lock.acquire()
	if not Nei_ip in Graph_Table:
		Graph_Table[Nei_ip]={}
	Graph_Table[Nei_ip][ip]=distance
	Graph_Table[ip][Nei_ip]=distance
	a = random.randint(1, 10000)
	while a in Boardcast_list:
		a = random.randint(1, 10000)
	packet=("Update "+ip+" "+str(a)+" "+str(Graph_Table[ip])).encode()
	print(Graph_Table[ip])
	lock.release()
	Boardcast(packet,ip)
	LS()
	#showRoutingTable()


#更新
def Update(packet,addr):
	global ip
	global Graph_Table
	#需要更新的路由器
	Update_ip=packet.split()[1]
	way="Update "
	Boardcast_id=packet.split()[2]
	lock.acquire()
	new_Graph=eval(packet.lstrip(way+Update_ip+" "+Boardcast_id))
	Boardcast_id=int(Boardcast_id)
	#print(Graph_Table[Update_ip]== new_Graph)
	if Update_ip in Graph_Table and Boardcast_id in Boardcast_list:
		#如果已接收到该信息，则直接退出
		lock.release()
		return
	#如果有更新，则更新
	if not Update_ip in  Graph_Table:
		Routing_Table[Update_ip]={}
		Graph_Table[Update_ip]={}
	if new_Graph!=Graph_Table[Update_ip]:
		Graph_Table[Update_ip]=new_Graph
		for neihbour in Graph_Table[Update_ip]:
			if not neihbour  in Graph_Table:
				Graph_Table[neihbour]={}
				Routing_Table[neihbour]={}
			Graph_Table[neihbour][Update_ip]=new_Graph[neihbour]
	lock.release()
	#mark该广播已收到
	LS()
	Boardcast_list.append(Boardcast_id)
	Boardcast(packet.encode(),addr)


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
        #'''源IP报文格式: traceroute ttl myip destinationip'''
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
	if ttl > 5:
		print("失败，太远了")


def leave_request(packet,addr):
	'''
	str:packet
	str:addr
	'''
	leave_ip=packet.lstrip("LEAVE ")
	#删除该节点的所有信息
	if leave_ip in Routing_Table:
		lock.acquire()
		del Routing_Table[leave_ip]
		for neihbour in Graph_Table[leave_ip]:
			del Graph_Table[neihbour][leave_ip]
		del Graph_Table[leave_ip]
		lock.release()
		#重新计算路径
		LS()
		Boardcast(packet.encode(),addr)

	


def leave():
	'''该路由器离开网络'''
	global ip
	packet=("LEAVE "+ip).encode()
	#广播LEAVE报文
	Boardcast(packet,ip)
	os._exit(0)


def Boardcast(packet,addr):
	'''
	str.encode():packet
	'''
	global ip
	temp=[]
	for neihbour in Graph_Table[ip].keys():
		if neihbour==addr:
			continue
		temp.append(neihbour)
	for neihbour in temp:
		s=socket.socket()
		try:
			s.connect((neihbour,listen_port))
			s.send(packet)
			s.close()
		except:
			#print("Yes")
			packet="LEAVE "+neihbour
			leave_request(packet,ip)


def clear_Boardcast():
	global Boardcast_list
	if len(Boardcast_list)>5:
		Boardcast_list=Boardcast_list[5:]
	clear=threading.Timer(60,clear_Boardcast)
	clear.start()




def commandMain():
    '''获取本地命令操作'''
    global ip
    while True:
        command = input("Please input your command:")
        command = command.split()
        length=len(command)
        if command[0] == "add" and length==3:
            '''格式例：add 192.168.199.143 8'''
            '''这里需要算法自动执行程序更新路由表'''
            addNeighbour(command[1], command[2])
        elif command[0] == "show" and length==1:
            showRoutingTable()
        elif command[0] == "traceroute"and length==2:
            '''格式例：traceroute 192.168.199.143'''
            destination = command[1]
            traceRoute(ip,destination)
        elif command[0] == "leave" and length==1:
            '''该路由器离开（损坏）'''
            '''这里需要算法自动执行程序更新路由表'''
            leave()
        else:
            print("Invalid input!")


def listenMain():
	'''监听获取其他路由器传来的信息'''
	s = socket.socket()
	s.bind((ip, listen_port))
	s.listen(5)
	while True:
		coon, addr = s.accept()
		request = coon.recv(1024).decode()
        #print(request)
		if request.split()[0] == "LEAVE":
			t=threading.Thread(target=leave_request,args=(request,addr[0])) 
			t.start()
		elif request.split()[0]=="Update":
			t=threading.Thread(target=Update,args=(request,addr[0]))
			t.start()
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
		coon.close()



def main():
	#global Routing_Table
	global ip
	Graph_Table[ip]={}
	cm = threading.Thread(target = commandMain, args = ())
	cm.start()
	lm = threading.Thread(target = listenMain, args = ())
	lm.start()
	clear=threading.Timer(60,clear_Boardcast)
	clear.start()
	while True:
		a = random.randint(1, 10000)
		while a in Boardcast_list:
			a = random.randint(1, 10000)
		lock.acquire()
		packet=("Update "+ip+" "+str(a)+" "+str(Graph_Table[ip])).encode()
		lock.release()
		Boardcast(packet,ip)
		time_for_sleep=random.randint(1,10)
		time.sleep(time_for_sleep)

ip=get_host_ip()
Routing_Table[ip]={"Next_Node":ip,"Distance":0}
if __name__ == "__main__":
    main()