# 创建数据库
create database TourBooking;
use TourBooking;

# 创建航班表
create table FLIGHTS(
    flightNum   char(5) primary key,
    price       int check(price > 0),
    numSeats    int check(numSeats > 0),
    numAvail    int check(numAvail >= 0),
    FromCity    varchar(50) not null,
    ArivCity    varchar(50) not null
) CHARSET=utf8;

# 创建宾馆房间表
create table HOTELS(
    hotelNum    char(5) primary key,
    location    varchar(50) not null,
    price       int check(price > 0),
    numRooms    int check(numRooms > 0),
    numAvail    int check(numAvail >= 0)
) CHARSET=utf8;

# 创建大巴班车表
create table BUS(
    BusNum      char(5) primary key,
    location    varchar(50) not null,
    price       int check(price > 0),
    numSeats    int check(numSeats > 0),
    numAvail    int check(numAvail >= 0)
) CHARSET=utf8;

# 创建客户数据表
create table CUSTOMERS(
    custID      char(5) primary key,
    custName    varchar(50) not null
) CHARSET=utf8;
	
# 创建预定表
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

create unique index resv_idx
on RESERVATIONS(resvType, resvKey);
