

@[TOC](目录)



- 基于 MySQL，设计并实现一个**简单的旅行预订系统**。该系统涉及的信息有航班、大巴班车、宾馆房间和客户数据等信息
- 全部代码见 [Github](https://github.com/lianli-o/bookingSystem)
# 基本功能
- 为该旅行预订系统设置两种用户：
  - (1) **预订系统管理者** `admin`。管理者可以直接**对航班、大巴、宾馆、客户信息进行增删改查**，还可以**查询预约信息** (不允许 `admin` 直接在后台更改客户的预约信息，如果航班取消或航班号修改，数据库会自动利用触发器对相应的预约信息进行删改)。同时也支持 `admin` **直接输入 SQL 语句**来操纵数据库
  - (2) **普通客户**。支持客户的登录与注册。普通客户可以对航班/大巴/宾馆进行**预约**/**取消预约**、**查询预约**订单情况、**查询旅行线路**、**检查预定线路合理性**

# ER 图设计及说明

- 如下图所示，客户与航班、大巴车、宾馆之间均为多对多关系。例如，一个客户可以预约多个航班，一个航班也可以被多个用户所预约
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210427215538936.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
> 请忽视上图中的箭头...


# 数据库逻辑结构设计

- **FLIGHTS 表**用来记录航班信息。这里假设在一个航班上，所有座位的价格都一样，因此 `FLIGHTS` 表中，航班号 `flightNum` 为**主键**。**用户定义完整性**主要是确保各个属性的取值有实际意义，具体定义如下：
```sql
create table FLIGHTS(
    flightNum   char(5) primary key,
    price       int check(price > 0),
    numSeats    int check(numSeats > 0),
    numAvail    int check(numAvail >= 0),
    FromCity    varchar(50) not null,
    ArivCity    varchar(50) not null
) CHARSET=utf8;
```

- **HOTELS 表**用来记录宾馆信息。这里假设在一个宾馆内，所有房间的价格都一样，因此 `HOTELS` 表中，宾馆号 `hotelNum` 为**主键**。**用户定义完整性**主要是确保各个属性的取值有实际意义，具体定义如下：

```sql
create table HOTELS(
    hotelNum    char(5) primary key,
    location    varchar(50) not null,
    price       int check(price > 0),
    numRooms    int check(numRooms > 0),
    numAvail    int check(numAvail >= 0)
) CHARSET=utf8;
```
- **BUS 表**用来记录大巴班车信息。这里假设同一个大巴车上所有座位价格一样，因此 `BUS` 表中，车号 `BusNum` 为主键。**用户定义完整性**主要是确保各个属性的取值有实际意义，具体定义如下：

```sql
create table BUS(
    BusNum      char(5) primary key,
    location    varchar(50) not null,
    price       int check(price > 0),
    numSeats    int check(numSeats > 0),
    numAvail    int check(numAvail >= 0)
) CHARSET=utf8;
```
- **CUSTOMERS 表**用来记录客户信息，客户 ID `custID` 为**主键**。同时**用户定义完整性**规定 `custName` 不能为空，否则就没有了实际意义：

```sql
create table CUSTOMERS(
    custID      char(5) primary key,
    custName    varchar(50) not null
) CHARSET=utf8;
```
- **RESERVATIONS 表**用来记录客户的预约信息。规定预约号 `resvNum` 为**主键** ((`resvType`, `resvKey`) 为候选码)。`custID` 为**外码**，参照 CUSTOMERS 表的 `custID` 属性；**用户定义完整性**规定 `resvType` 只能取值 1 / 2 / 3，分别表示预约类型为航班/大巴车/宾馆；规定 `resvKey` 对应 FLIGHTS / HOTELS / BUS 表的一个主键，用来表示预约的航班号/车号/宾馆号：
```sql
create table RESERVATIONS(
    resvNum     char(5) primary key,
    custID      char(5) not null,
    resvType    int check(resvType in (1, 2, 3)),
    resvKey     char(5) check(
        resvKey in (
            select flightNum from FLIGHTS
            union select hotelNum from HOTELS
            union select BusNum from BUS
        )
    ),
    foreign key (custID) references CUSTOMERS(custID)
) CHARSET=utf8;
```


# 数据库物理设计
- MySQL 在表的主键上都建立了索引。除此之外，因为在查询预约对应的航班号/车号/宾馆号时经常要查询 (`resvType`, `resvKey`) 这一候补码，因此在 `resvType` 和 `resvKey` 属性上也建立索引：

```sql
create unique index resv_idx
on RESERVATIONS(resvType, resvKey);
```

# 详细设计与实现
## 触发器的定义与实现
> **航班、大巴车、宾馆的实现都类似，因此下面主要以航班 FLIGHTS 表为例进行讲解**

**主要使用了以下触发器保持数据库的一致性**：
- (1) 在 `RESERVATIONS` 表上设置插入触发器，如果**插入一条航班预约信息** (`new.resvType = 1`) 且该航班号存在 (航班号在 FLIGHTS 表中)，则查看该航班的剩余座位数，如果该航班还有剩余座位，则到航班表中将该航班的剩余座位数减一，否则禁止此次预约 (回滚)
```sql
create trigger make_reservation 
before insert on RESERVATIONS
for each row
begin
    if new.resvType = 1 then
        if (select numAvail from FLIGHTS where flightNum = new.resvKey) > 0
             and exists(select * from FLIGHTS where flightNum = new.resvKey) 
        then
            update	FLIGHTS
            set		numAvail = numAvail - 1
            where	flightNum = new.resvKey;
        else
       	 	# 预约数已满，不允许预约
       	 	# 由于 MySQL 触发器中不允许使用 rollback，
       	 	# 因此通过将主键设为非法值，数据库插入报错来阻止插入
            set new.resvNum = '??????????????'; 
        end if;
    end if;
end;
```
- (2) 在 `RESERVATIONS` 表上设置删除触发器，如果**取消航班预约** (`old.resvType = 1`) 且 FLIGHTS 表中存在该航班信息，则将 FLIGHTS 表中对应航班的可用座位数加一
  - 这里一定要先检查 FLIGHTS 表中存在该航班信息是因为取消航班预约也可能是由对应航班取消导致的 (这是后面要讲的一个触发器的功能)，因此如果不检查的话可能会导致触发器循环调用 (删除 FLIGHTS 表中的航班信息导致删除对应航班的预约信息，进而触发 `RESERVATIONS` 表上的删除触发器，该触发器又企图对 FLIGHTS 表进行更新减少对应航班的可用座位数 (尽管这个更新实际不会发生，但 MySQL 依然会报错))，这在 MySQL 中是不允许的

```sql
create trigger cancel_reservation
after delete on RESERVATIONS
for each row
begin
    if old.resvType = 1 
        and exists(select * from FLIGHTS where flightNum = old.resvKey) then
            update	FLIGHTS
            set		numAvail = numAvail + 1
            where	flightNum = old.resvKey;
    end if;
end;
```
- (3) 在 `FLIGHTS` 表上设置删除触发器，如果有**航班被取消**，则删除该航班对应的预约信息

```sql
create trigger delete_reservation
after delete on FLIGHTS
for each row
begin
    delete from RESERVATIONS
    where old.flightNum = resvKey and resvType = 1;
end;
```
- (4) 在 `FLIGHTS` 表上设置更新触发器，如果有**航班号被更改**，则同步更新该航班对应的预约信息

```sql
create trigger update_reservation
after update on FLIGHTS
for each row
begin
    if new.flightNum != old.flightNum then
        update RESERVATIONS
        set resvKey = new.flightNum
        where old.flightNum = resvKey and resvType = 1;
    end if;
end;
```
## 数据库事务的定义与实现

### 三个主要的类
**`Database` 类**
- 首先定义 `Database` 类，它主要通过 pymysql 库实现数据库连接、执行 sql 语句、返回 sql 语句的查询结果、用 MySQL 风格打印查询结果等功能
***
**`Menu` 类**
- 主要提供各级菜单的显示以及用户功能选择的获取
***
**`BookingSys` 类**
- 继承自 `Database` 类，旅行预订系统的各项功能主要都是由它提供的，下面主要讲述该类中方法的实现

### 旅行预订系统管理者
> 下面不会贴太多代码。代码的基本思路都是让用户输入必要的信息，然后组成 SQL 语句，通过 pymysql 库提交数据库执行

**(1) 直接输入 SQL 语句**操纵数据库
- 这个实现比较简单，就是通过 pymysql 库执行用户输入的 SQL 语句，如果发生错误则进行回滚
***
**(2) 对航班、大巴、宾馆、客户信息进行增删改**
> 航班、大巴、宾馆、客户信息的增删改查都比较类似，下面以航班为例进行说明
- 注意：这里不允许 `admin` 直接在后台更改客户的预约信息，如果航班取消或航班号修改，数据库会自动利用触发器对相应的预约信息进行删改
- **增**加航班：要求用户输入 `flightNum`, `price`, `numSeats`, `FromCity`, `ArivCity` 这五个属性的值，然后构建出 `insert` 语句，利用 `Database` 类提供的 SQL 语句执行功能进行插入
- **删**除航班：要求用户输入要删除的航班号 `flightNum`，然后构建出 `delete` 语句，利用 `Database` 类提供的 SQL 语句执行功能进行删除
- 修**改**航班信息：要求用户输入要修改的航班号 `flightNum`，然后输入要修改的属性名和新值，最后构建出 `update` 语句，利用 `Database` 类提供的 SQL 语句执行功能进行更新
***
**(3) 对航班、大巴、宾馆、客户、预约信息进行查询**
-  查询**航班**信息时 (**大巴、宾馆、客户**信息查询同理)，直接利用 `Database` 类提供的 SQL 语句执行功能执行 `select * from FLIGHTS` 语句，然后利用  `Database` 类提供的查询结果打印功能将其规整地打印出来
- 查询**预约**信息时，还要求客户选择查询航班/大巴/宾馆中哪一个的预约情况。以航班为例，将 `RESERVATIONS`, `CUSTOMERS`, `FLIGHTS` 表进行自然连接并筛选出航班的预约信息 (`resvType = 1`)，最后输出预约号、客户 id、预约的航班号、航班价格、航班起点及终点。也就是执行以下 SQL 语句：

```sql
select resvNum, CUSTOMERS.custID, flightNum, price, FromCity, ArivCity
from RESERVATIONS, CUSTOMERS, FLIGHTS
where resvKey = flightNum and resvType = 1
	and RESERVATIONS.custID = CUSTOMERS.custID;
```

### 普通客户
> 以下说明均以航班为例，大巴/宾馆的实现过程同理

**(1) 客户登录与注册**
- 在用户输入其 id 后，首先构建 `select custID from CUSTOMERS` 的 SQL 查询语句，然后通过  `Database` 类提供的查询功能进行查询，返回查询结果
- 如果用户输入的 id 在查询结果中，说明该**客户存在**，打印出**登录成功**的信息，之后再构建 `select custName from CUSTOMERS where custid = %s` 的 SQL 语句进行查询 (`%s` 这里为输入的客户 id)，打印出该客户 id 对应的名字
- 如果用户输入的 id 不在查询结果中，则要求客户继续提供新用户名 name，最后构建 `insert into CUSTOMERS values('%s', '%s')` 插入 SQL 语句向客户表中插入新的客户信息 (id 和 name)，并打印出**注册成功**的提示信息


***
**(2) 预约**
- 客户选择预约模式后，还要再选择预约航班/大巴车/宾馆；下面以预约航班为例进行说明：首先要求客户输入航班起点 `FromCity` 与到达城市 `ArivCity`，然后构建查询 SQL 语句：`select * from FLIGHTS where FromCity = '%s' and ArivCity = '%s'  and numAvail > 0` 来选出所有符合起点与终点条件以及机上还有剩余座位的航班信息并将其打印出来
- 接着查询 `RESERVATIONS` 表中所有预约信息的 `resvNum` 并随机生成一个不同于预约表中已有预约号的新的预约号
- 接着要求客户继续输入想要预约的航班号，在进行确认后在 `RESERVATIONS` 表中插入一条预约信息，其中 `resvType = 1` 表示预约的是航班，`resvKey` 为 `flightNum`，`custID` 为进行预约的客户 id，`resvNum` 为刚才随机生成的新预约号

***
**(3) 取消预约**
- 同样以取消预约航班为例，首先如下面的代码所示 (`id` 为当前取消预约的客户 id，`verbose` 设为 `True` 表示打印预约信息，`output_resvNum` 设为 `True` 表示除了打印航班的起点终点，还打印航班的预约号)，将 `CUSTOMERS`, `FLIGHTS`, `RESERVATIONS` 三个表做自然连接，然后选出指定客户的预约信息 (预约号、航班号、起点、终点)，并将选出的**预约信息打印**出来以供客户选择要取消哪个预约

```python
def query_flights(self, id, verbose=False, output_resvNum=False):
	"""查询指定客户的航班信息"""
	key = "RESERVATIONS.resvNum, " if output_resvNum else ""
	sql = """select %s FLIGHTS.flightNum, FromCity, ArivCity
			from CUSTOMERS, FLIGHTS, RESERVATIONS
			where CUSTOMERS.custID = RESERVATIONS.custID
			and FLIGHTS.flightNum = RESERVATIONS.resvKey
			and resvType = %d
			and CUSTOMERS.custID = '%s'""" %(key, self.RESERVE_FLIGHT, id)
	flights = self.query(sql)

	if verbose:
		if len(flights) == 0:
			print("You haven't reserved any flight yet.")
		else :
			print("Reserved Flight:")
			self.print_query_results(flights)

	return flights
```
- 在打印了航班预约信息之后，要求客户输入要取消的预约号 `resvNum`。此时将 `RESERVATIONS` 和 `FLIGHTS` 表做自然连接来查询客户输入的 `resvNum` 是否为航班预约，如果是，则构建 `delete from RESERVATIONS where resvNum = '%s'` SQL 语句对该条预约记录进行删除


***
(4) **查询预约情况**
- 下面同样以查询航班信息为例进行说明：这里查询预约情况调用的就是上面的 `query_flights` 方法来打印用户的航班预约信息 (不同的是将 `output_resvNum` 设为 `False` 来避免打印出预约号)
***

(5) **查询旅行线路**
- 这里默认只有航班才能跨城市移动，大巴车只能在本地移动，因此查询旅行线路同样是调用 `query_flights` 方法查询客户已经预约的航班信息，最终打印出每一个航班的起点和终点
***
(6) **检查线路合理性**
- 主要是检查客户预约的大巴车和宾馆是否在航班途经的城市上，如果不在，则线路不合理。因此先调用 `query_flights` 方法查询客户已经预约的航班信息，然后将所有途经城市都存到一个集合 `cities` 中，之后分别调用 `query_buses` 和 `query_hotels` 方法查询客户预约的大巴车和宾馆记录，如果其中有大巴车或宾馆的地点不在 `cities` 中，则线路不合理


# 数据库测试

## 普通客户
**登录**
- **登录界面**: 要求输入用户 id
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428160121251.png#pic_center)
- 这里输入一个新客户 id `00001`，系统提示需要先注册，要求输入客户名
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428160343983.png#pic_center)
- 这里输入客户名为 `lianlio`，系统提示**注册成功**，同时弹出客户服务菜单，从 0 ~ 5 依次表示退出登录、预约、查询预约、取消预约、查询旅行线路、检查旅行线路合理性
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428160532163.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 此时如果我退出系统再次输入 id 进行登录，系统就会提示登陆成功，并显示欢迎信息：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428163945907.png#pic_center)

***
**预约**
- 输入 1 来选择预约服务，这里系统继续询问要预约航班、大巴还是宾馆
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428161058205.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 这里以预约航班为例，输入 1 以预约航班；系统继续询问要预约从哪里到哪里的航班
![在这里插入图片描述](https://img-blog.csdnimg.cn/2021042816115222.png#pic_center)
- 假设预约大连到无锡的航班，系统经过查询后输出了所有大连到无锡的航班信息，并进一步询问要预约的航班号
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428161325702.png#pic_center)
- 这里选择 17593 号航班，在确认预约后，系统提示预约成功
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428161528887.png#pic_center)

***
**预约查询**
- 继续选择客户服务 2 (预约查询)，并选择查询预约的航班信息。如下图所示，系统打印出了刚才预约的信息 (00001 号客户预约了 17593 号航班，从大连飞往无锡)
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428163052932.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
***
**取消预约**
- 选择客户服务 3 (取消预约)，并选择取消航班预约。此时系统自动打印出了当前客户的航班预约情况 (这里我事先又增加了几个航班预约)，并询问客户要取消哪个航班的预约
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428165049509.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 选择取消 19213 号从深圳飞往上海的航班，对应的预约号为 90670。之后系统会询问是否删除从深圳到上海的航班预约，确认后系统显示删除成功的提示
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428165705969.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
***
**查询旅行线路**
- 在选择查询旅行线路后，系统打印出旅行线路
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428165810883.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
***
**检查预定线路合理性**
- 如下图所示，我目前预约的宾馆均在航班途经城市上
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428170248436.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 此时选择"检查预定线路合理性"服务，系统显示旅行计划合理
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428170345987.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 下面我再多预定一个深圳的宾馆，这个宾馆不在我的旅行路线上
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428170841570.png#pic_center)
- 此时再次选择"检查预定线路合理性"服务，系统显示旅行计划不合理
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428170913887.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
## 预订系统管理者
- 在登录界面输入 `admin` 进入系统管理者界面，可以直接**对航班、大巴、宾馆、客户信息进行增删改查**，还可以**查询预约信息** (不允许 `admin` 直接在后台更改客户的预约信息，如果航班取消或航班号修改，数据库会自动利用触发器对相应的预约信息进行删改)。同时也支持 `admin` **直接输入 SQL 语句**来操纵数据库
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428193135951.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)



***
> 下面以航班为例演示增删改查


**(1) 查询航班信息**
- 选择对 FLIGHTS 表进行操作后，系统询问是要进行增删改查哪种操作。这里选择“查询” (3. Query)
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428193838628.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 选择后，系统自动输出所有航班的信息：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428194315380.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
***

**(2) 新增航班**
- 在选择对 FLIGHTS 表进行操作后，选择 1. Insert 进行航班信息的插入。系统要求输入航班的各项信息
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428194523345.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 下面插入一趟航班号为 `12345`，票价 999，载客量 100，从无锡飞往大连的航班。系统显示插入成功
![在这里插入图片描述](https://img-blog.csdnimg.cn/2021042819474129.png#pic_center)
- 再次进行查询，可以观察到这趟航班已被成功添加
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428194914197.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
***

**(3) 修改航班信息**
- 在选择对 FLIGHTS 表进行操作后，选择 4. Update 进行航班信息的更新。系统要求输入想要修改的航班号
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428195245393.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 这里就对刚才添加的航班 `12345` 进行修改。输入航班号后，系统要求输入想要更改的航班属性与新值。这里将航班号改为 `54321`.最后系统提示修改成功：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428195708746.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 此时对航班信息进行查询，发现 `12345` 航班被修改为了 `54321` 航班：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428195832894.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
***
**(4) 删除航班信息**
- 在选择对 FLIGHTS 表进行操作后，选择 2.Delete 进行航班信息的删除。系统要求输入想要删除的航班号，这里我们就选择删除航班 `54321`；最后系统提示删除成功：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428200042474.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 再次查询航班信息，可以看到航班 `54321` 已被删除
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428200233983.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)

***


**(5) 查询预约信息**
- 首先选择查询预约服务，接着系统询问要查询航班还是大巴还是宾馆的预约信息
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428201322167.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 这里选择查询航班预约信息：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428201408573.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
***
**直接执行 SQL 语句**
- 管理者还可以选择直接使用 SQL 语句来更灵活的操纵数据库
- 如下图所示，查询航班信息，目前最后一行上航班 `19213` 的票价为 999
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428202056638.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 下面将航班 `19213` 的票价涨价 301 元。输入 SQL 语句后系统提示执行成功：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428202143940.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 再次查询航班信息，航班 `19213` 的票价涨价到了 1300
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428202236708.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
## 触发器测试

- (1) **插入一条航班预约信息** (`new.resvType = 1`) 且该航班号存在 (航班号在 FLIGHTS 表中)，则将该航班的剩余座位数减一，否则禁止此次预约 (回滚)
  - 首先查看航班信息，注意到航班 `18791` 目前剩余座位还有 30 个
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428203254382.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
  - 下面切换为普通客户对航班 `18791` 进行预约
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428203355192.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- 预约完成后切换回 admin 用户，查看航班信息，发现航班 `18791` 的可用座位数减少了一个
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428203452667.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- (2) 如果**取消航班预约** (`old.resvType = 1`) 且 FLIGHTS 表中存在该航班信息，则将 FLIGHTS 表中对应航班的可用座位数加一
  - 取消对航班 `18791` 的预约
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428203658430.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
  - 再次查看航班 `18791` 的可用座位数，发现增加了一个
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428203806466.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
- (3) 如果有**航班被取消**，则删除该航班对应的预约信息；如果有**航班号被更改**，则同步更新该航班对应的预约信息
  - 首先查看客户目前的航班预约情况：
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428203928543.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
  - 切换到 admin 模式，删除 `11714` 航班
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428204029858.png#pic_center)
  - 此时再查看航班预约情况，发现 `11714` 航班的预约已被删除
![在这里插入图片描述](https://img-blog.csdnimg.cn/20210428204107201.png?,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3dlaXhpbl80MjQzNzExNA==,size_16,color_FFFFFF,t_70#pic_center)
## 参考项目
- [TourBookingSystem](https://github.com/izcat/TourBookingSystem)


