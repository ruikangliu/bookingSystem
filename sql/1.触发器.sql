# 预约后更新航班、宾馆、大巴信息
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
            set new.resvNum = '??????????????'; # 预约数已满，将主键设为非法值，数据库插入报错
        end if;
    end if;
    if new.resvType = 2  then
        if (select numAvail from BUS where busNum = new.resvKey) > 0  
            and exists(select * from BUS where busNum = new.resvKey) 
        then
            update	BUS
            set		numAvail = numAvail - 1
            where	busNum = new.resvKey;
        else
            set new.resvNum = '??????????????';
        end if;
    end if;
    if new.resvType = 3  then
        if (select numAvail from HOTELS where hotelNum = new.resvKey) > 0 
             and exists(select * from HOTELS where hotelNum = new.resvKey)
        then
            update	HOTELS
            set		numAvail = numAvail - 1
            where	hotelNum = new.resvKey;
        else
            set new.resvNum = '??????????????';
        end if;
    end if;
end;

# 取消预约后更新航班、宾馆、大巴信息
create trigger cancel_reservation
after delete on RESERVATIONS
for each row
begin
    # 这里在更新 FLIGHTS 之前，先要查看一下被删除的
    # 预约中 flightNum 是否在 FLIGHTS 表中，如果不在，
    # 则表明这次预约删除是由航班删除而非客户主动取消
    # 预约导致的，此时就不能更新 FLIGHTS 表，否则会
    # 被 MySQL 判定为循环调用而报错
    if old.resvType = 1 
        and exists(select * from FLIGHTS where flightNum = old.resvKey) then
            update	FLIGHTS
            set		numAvail = numAvail + 1
            where	flightNum = old.resvKey;
    end if;
    if old.resvType = 2 
        and exists(select * from BUS where busNum = old.resvKey) then
            update	BUS
            set		numAvail = numAvail + 1
            where	busNum = old.resvKey;
    end if;
    if old.resvType = 3 
        and exists(select * from HOTELS where hotelNum = old.resvKey) then
            update	HOTELS
            set		numAvail = numAvail + 1
            where	hotelNum = old.resvKey;
    end if;
end;

-- 如果预约的航班/大巴/宾馆被删除，则对应的预约记录也要被删除
create trigger delete_reservation
after delete on FLIGHTS
for each row
begin
    delete from RESERVATIONS
    where old.flightNum = resvKey and resvType = 1;
end;

create trigger delete_reservation
after delete on BUS
for each row
begin
    delete from RESERVATIONS
    where old.busNum = resvKey and resvType = 2;
end;

create trigger delete_reservation
after delete on HOTELS
for each row
begin
    delete from RESERVATIONS
    where old.hotelNum = resvKey and resvType = 3;
end;

-- 如果预约的航班/大巴/宾馆信息被修改，则对应的预约记录也要被修改
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

create trigger update_reservation
after update on BUS
for each row
begin
    if new.busNum != old.busNum then
        update RESERVATIONS
        set resvKey = new.busNum
        where old.busNum = resvKey and resvType = 2;
    end if;
end;

create trigger update_reservation
after update on HOTELS
for each row
begin
    if new.hotelNum != old.hotelNum then
        update RESERVATIONS
        set resvKey = new.hotelNum
        where old.hotelNum = resvKey and resvType = 3;
    end if;
end;
