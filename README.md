# Virtual-Routing

## 环境说明
* 开发环境：Linux、Windows 10
* 开发语言：python3
* 运行环境：Linux、Windows
* 使用库：socket、os、threading、operator、time

## 源码
https://github.com/RealEasyin/Virtual-Routing

## 功能

### 自动功能
* 自动获取本地IP
* 自动更新路由表

### 交互功能
* 添加新邻居    `add neighborhoodIP Distance`
* 模拟路由器脱离网络 `leave`
* 显示路由表 `show`
* 显示从源到目的地的路由路径 `tracert`

## 实现逻辑
* 去中心化路由：LS算法、DV算法
* 中心化路由：LS算法

### 数据结构
```python
Routing_Table = {
    '目的地IP': Route,
    ···
}

Route = {
    'Distance' : '''总距离（字符串）''',
    'Next_Node' : '''下一节点（字符串）''',
}
```

### tracert
*定义一个ttl，ttl从1开始取值，并认为规定ttl最大值为大跟踪越点数。源节点每次向目标节点方向发送一个带有ttl的报文*
`traceroute ttl sourceip destinationip`，*每传输到一个节点，ttl的值就减一，当ttl的值减为零时，所在节点向源节点就回传一个回应报文*`response sourceip ttlip`，*源节点收到该报文后就输出对应ttl和此节点的IP。*
```python
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
        rp = s.recv(1024).decode()
        print(str(ttl) + " " + rp.split()[2])
        if (rp.split()[2] == destination):
            print("跟踪结束，已找到目标节点。")
            break
        s.close()
        ttl = ttl + 1
    if ttl >5:
        print("失败，太远了")


def listenMain():
    '''监听获取其他路由器传来的信息'''
    ...
        request = coon.recv(1024).decode().split()
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
    ...
```
