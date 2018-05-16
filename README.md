# Virtual-Routing

## 环境说明
* 开发环境：Linux、Windows 10
* 开发语言：python3
* 运行环境：Linux、Windows
* 使用库：socket、os、threading、operator、time

## 源码
https://github.com/RealEasyin/Virtual-Routing


## 算法使用
* 去中心化路由：LS算法、DV算法
* 中心化路由：LS算法

## 数据结构
```python
Routing_Table = {
    '目的地IP': Route,
    ···
}
// 其中Route为：
Route = {
    'Distance' : '''总距离（字符串）''',
    'Next_Node' : '''下一节点（字符串）''',
}
```
## DV路由
### 基础算法：DV路由算法
1. 每个路由维护一个全局最短路径表，并维护自己的参与链路表（邻居表）
2. 当此路由维护的全局表更新时，通知所有邻居新的邻接表
3. 每当收到更新时，C(x, y) = min(D(v) + C(v, y)}
### 报文格式：
| 报文类型 | 报文头 | 报文格式 | 备注 |
| --------   | -----:   | :----: | -----|
| 路由更新    | `PATH`      |   `PATH Routing_Table`| 其中，`Routing_Table`为路由表
| 路径查询        | `ASK`    |   `ASK destination` | 其中，`destination`为目标IP    |
| 路径应答        | `ANS`  |   `ANS cost`    | 其中，`cost`为路径长度
### 实现流程

![DV流程图](https://raw.githubusercontent.com/Skyraker2016/markdownpic/master/virtualRoutingDV.png)
### 具体说明
* 维护一个路由表 `Routing_Table`
* 维护自己的邻居链路 `n_table`
* 用一个临时路由表包含链路改变，代替两种更新报文
1. `def addPath(nip, distance)` 添加/修改/删除路径：
    
    输入：`nip`-邻居IP；`distance`-链路代价
    实现：将`nip： distance`加入邻居链路表`n_table`中，将此邻居链路加入/覆盖路由表 `Routing_Table[nip] = {"Distance": distance, "Next_Node"： distance}`，并作为临时路由表发送更新。若原本此路由小于新的路由,且不是直接相连，则在发送后要重新覆盖回来。
2. 
    1. `def renewPath()` 告知变更：

        邻居`n_table`中所有可联通邻居（距离<99999）发送自己更新的路由表，报文格式：`PATH Routing_Table`，其中，`Routing_Table`为自己的路由表
    1. `def renewListener(sip, pk)` **监听更新**：

        算法的关键功能。

        输入：`sip`-更新了的邻居；`pk`更新报文，其中包含`PATH`头及`nrt`（neightbour_routing_table）

        实现：
        1. 更新`n_table`邻居表：当`Routing_Table`中，某项的目标与下一跳均为本机ip时，则说明这一条路由代表邻居链路。（代替了原算法中的D，即邻居距离向量）。显然当邻居链路更新时，由于`addPath`与`leave`的实现时，当邻居链路更新时会将邻居链路覆蓋爲直連格式，再另行更改。
        2. 更新`Routing_Table`：对所有已有的节点、`nrt`带来的节点进行更新。每次更新，遍历寻找相邻节点v，计算最小的`C(v,y)+D(x)`，用以更新路由表。
        3. 若路由表有所更新，则告知变更
4. 
    1. `askCost(sip, dip)` 询问路径长度：

        由于本机并不保留邻居的路由表，因此每次更新时的`C(v,y)`都是向`sip`询问到`dip`的距离
    1. `ansCost(conn, pk)` 应答路径长度：
        
        应答路径长度，不可达则返回99999

## LS路由

### 算法说明
这次项目中我使用了`Dijkstra算法`，也就是书上提到算法，算法的描述如下：  
1. 以某点为起点，加入点集。
2. 在图中未在点集中的节点中选择与起点距离最短的点a
3. 把a加入集合，把a的邻接节点的距离更新，公式为：$D(x) = D(a) + c(a, x)$
4. 重复2-4，直到途中的点都加入点集中或者已无可加入点集的点（孤立点或不连通图）
### 算法具体实现
对每个路由器，都已自身为起点，根据自己的拓扑图，执行Dijkstra算法，获得最新的路由表，孤立点或不连通点则从路由表中清除。
报文说明：
### Update报文
`Update host_ip ID Graph_host`

#### 报文说明
`Update`：报文方法  
`host_ip`：初始广播发送该报文的路由器的ip地址  
`Graph_host`：初始广播发送该报文的路由器的在拓扑图中的与他相连的链路的信息，每项具体格式为：`Adjacent_ip` : cost，`Adjacent_ip`指该路由器的下一跳路由器的ip地址，cost指两者间链路的费用。

#### 报文作用
Update报文用于定时的广播，向所有路由器广播自己的接入链路情况是否发生改变，当接受到Update报文时，每个路由器会与自身所具有的拓扑图进行比较，如果两者一致，则不再转发该报文；如果不一致，更新自身拓扑图，然后继续转发广播该报文


### Leave报文
`LEAVE IP`

#### 报文说明
`LEAVE`：报文方法
`IP`：离开了网络的路由器的IP地址
报文作用：
LEAVE报文用于通知拓扑图中其他路由器该路由器已经离开了网络，在网络中的路由器请在自己的拓扑图中删除该路由器并更新自己的路由表。LEAVE报文在路由器正常退出或者邻居无法连接上该路由器时发出。

### 流程图
#### 把一个路由器添加进网络
![LS流程图add](https://raw.githubusercontent.com/Skyraker2016/markdownpic/master/virtualRout_zh1.jpeg)
#### 处理update报文
![LS流程图update](https://raw.githubusercontent.com/Skyraker2016/markdownpic/master/virtualRout_zh4.jpeg)
#### 路由器离开网络
![LS流程图 离开网络](https://raw.githubusercontent.com/Skyraker2016/markdownpic/master/virtualRout_zh2.jpeg)
#### 路由器损坏
![LS流程图 损坏](https://raw.githubusercontent.com/Skyraker2016/markdownpic/master/virtualRout_zh5.jpeg)
#### 处理LEAVE报文
![LS流程图leave](https://raw.githubusercontent.com/Skyraker2016/markdownpic/master/virtualRout_zh3.jpeg)

### 功能
1. 模拟添加一个路由器
当一个虚拟路由器启用时，它并没有加入虚拟网络，没有与虚拟网络连接的状态。调用`add`指令，模拟一个路由器与另一个路由器连接。两者通过广播更新自己的拓扑图，然后执行LS算法获得最新的路由表。

2. 更新路由器之间的链路费用
同样使用add指令，add指令新输入的链路费用会覆盖两个路由器间的链路费用，通过广播把该更新通知其他路由器，执行LS算法，更新路由表

3. 模拟路由器退出
当一个路由器想退出网络，不再工作时，执行leave指令，模拟路由器退出网络，路由器广播最后的leave报文，程序结束。其他路由器收到leave报文，更新自己的拓扑图，执行LS算法更新路由表

4. 模拟路由器损坏
当一个路由器尝试连接它的邻接路由器而没有收到回复时，说明该邻接路由器已经损坏，路由器将更新自己的连接表，执行LS算法更新路由表，并广播该邻接路由表的LEAVE报文

### 中心化路由
#### 基础算法：LS算法
由于有中心路由器，因此需要共享完整拓扑图的`LS算法`有着天然的优势。算法思想详见LS算法部分。
#### 报文格式：
* 用户路由发送：

    | 报文类型 | 报文头 | 报文格式 | 备注 |
    | --------   | -----:   | :----: | -----|
    | 路由更新    | `path`      |   `path distanation distance`| 其中，`distanation`为目标节点，`distance`为花费代价。|
    | 路径查询        | `ask`    |   `ask destination` | 其中，`destination`为目标IP    |
    | 路径应答        | `all`  |   `all`    |  |
* 中央路由发送：

    | 报文类型 | 报文头 | 报文格式 | 备注 |
    | --------   | -----:   | :----: | -----|
    | 路由更新    | `ans`      |   `ans via distance`| 其中，`via`为下一跳节点，`distance`为花费代价。|
    | 路径应答        | `all`  |   `all routing_table`    | 其中，`routing_table`为对应路由器的完整路由表 |


#### 实现流程：

![流程图](https://raw.githubusercontent.com/Skyraker2016/markdownpic/master/virtualControl.png)
#### 具体说明：
类似于云计算，一切关于路由表的生成都储存在中央路由器中计算。
##### 用户路由：

* 不需要维护路由表
* 当需要使用路由表时，向中央路由请求路由表
* 自动获得本机IP，手动获得中央路由IP
* 操作：
    1. `add ip cost`: 添加或修改一条与自身相连的链路信息
    2. `del ip`: 删除一条与自身相连的链路信息(即将某路径的花费置为99999)
    3. `show`: 显示自己的总路由表
    4. `leave`: 使自身失效，即离开路由表
##### 中央路由：
* 维护总路由表、总拓扑图
* 自动获得本中央路由IP
* 功能：
    1. 修改拓扑图，并用LS，基于新的拓扑图生成新路由表
    2. 为用户路由器提供路由表查询服务

## traceroute 功能
*定义一个ttl，ttl从1开始取值，并认为规定ttl最大值为大跟踪越点数。源节点每次向目标节点方向发送一个带有ttl的报文*
`traceroute ttl sourceip destinationip`，*每传输到一个节点，ttl的值就减一，当ttl的值减为零时，所在节点向源节点就回传一个回应报文*`response sourceip ttlip`，*源节点收到该报文后就输出对应ttl和此节点的IP。*
