import random
from dbSQL import Database

class Menu:
	def __init__(self):
		self.main_menu_title = "BookingSystem"
		self.main_menu_customer_services = [
			"1.Make Reservation",
			"2.Query Reservation",
			"3.Cancel Reservation",
			"4.Query Travel Route",
			"5.Check Travel Route Rationality",
			"0.Log out"
		]
		self.n_customer_service = 6
		self.main_menu_admin_services = [
			"1.FLIGHTS",
			"2.BUS",
			"3.HOTELS",
			"4.CUSTOMERS",
			"5.RESERVATIONS",
			"6.Execute SQL Command",
			"0.Log out"
		]
		self.n_admin_service = 7
		self.main_menu_customer_welcome = "Customer Service"
		self.main_menu_admin_welcome = "Admin Service"

	def main_menu(self, is_admin=False):
		print("\n\n\n")
		services = self.main_menu_admin_services if is_admin else self.main_menu_customer_services
		print("+" + "-" * 16 + self.main_menu_title + "-" * 16 + "+")
		for service in services:
			print("|  " + "%-40s" %(service) + "  |")
		print("+" + "-" * (32 + len(self.main_menu_title)) + "+")
		print()
		welcome = self.main_menu_admin_welcome if is_admin else self.main_menu_customer_welcome
		print("+" + "-" * 16 + welcome + "-" * 16 + "+")
		n_service = self.n_admin_service if is_admin else self.n_customer_service
		choice = input("Please select a service (0~%d): " %(n_service - 1))
		if choice in [str(i) for i in range(n_service)]:
			return int(choice)
		else:
			print("Invalid input!")
			return self.main_menu()

	def in_menu(self, str):
		"""二级菜单"""
		choice = input("1.%s flight\n2.%s bus\n3.%s hotel\nYour choice: " % (str, str, str))
		if choice in ["1","2","3"]:
			return int(choice)
		else:
			print("Invalid input! Please input again: ")
			return self.in_menu(str)

	def log_in_menu(self):
		print("\n\n\n")
		print("+" + "-" * 16 + "Log in" + "-" * 16 + "+")
		return input("Please input your ID (5 bits, e.g. 00001):")

class BookingSys(Database):
	def __init__(self, user, password):
		super().__init__(user, password, "TourBooking")
		self.RESERVE_FLIGHT = 1		# 预约种类 RevType
		self.RESERVE_BUS = 2
		self.RESERVE_HOTEL = 3
		self.menu = Menu()
	
	def query_custID(self, id=""):
		"""查询 custid 是否存在 (如果不传入 custid 则返回数据库中的全部 custid)"""
		sql = """select custID 
				from CUSTOMERS 
				"""	
		if not id == "":
			sql += """where custID = '%s'""" % (id)
		results = self.query(sql)
		return [result['custID'] for result in results]

	def query_custName(self, id):
		"""查询 custid 对应的 custName"""
		sql = """select custName 
				from CUSTOMERS
				where custid = %s
				"""	%(id)
		results = self.query(sql)	# 在数据库中执行查询语句，返回查询结果
		return results[0]['custName']

	def insert_customer(self, id, name):
		"""插入新的用户"""
		sql = "insert into CUSTOMERS values('%s', '%s')" % (id, name)
		return self.insert(sql)		

	def query_reservations(self, id=""):
		"""查询预约情况"""
		sql = "select * from RESERVATIONS"
		if not id == "":
			sql += " where resvNum = '%s'" % (id)
		results = self.query(sql)
		return [result['resvNum'] for result in results]

	def insert_reservation(self, id, resvType, resvKey):
		"""插入预约记录"""
		resv_nums = self.query_reservations()
		resvNum = str(random.randint(1, 99999))
		while resvNum in resv_nums:
			resvNum = str(random.randint(1, 99999))

		sql = "insert into RESERVATIONS values('%s', '%s', %d, '%s')" % (resvNum, id, resvType, resvKey)
		return self.insert(sql)

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

	def query_hotels(self, id, verbose=False, output_resvNum=False):
		"""查询指定客户的宾馆信息"""
		key = "RESERVATIONS.resvNum, " if output_resvNum else ""
		sql = """select %s location
				from CUSTOMERS, HOTELS, RESERVATIONS
				where CUSTOMERS.custID = RESERVATIONS.custID
				and HOTELS.hotelNum = RESERVATIONS.resvKey
				and resvType = %d
				and CUSTOMERS.custID = '%s'""" %(key, self.RESERVE_HOTEL, id)
		hotels = self.query(sql)

		if verbose:
			if len(hotels) == 0:
				print("You haven't reserved any hotel yet.")
			else :
				print("Reserved Hotel:")
				self.print_query_results(hotels)

		return hotels

	def query_buses(self, id, verbose=False, output_resvNum=False):
		"""查询指定客户的大巴车信息"""
		key = "RESERVATIONS.resvNum, " if output_resvNum else ""
		sql = """select %s location
				from CUSTOMERS, BUS, RESERVATIONS
				where CUSTOMERS.custID = RESERVATIONS.custID
				and BUS.busNum = RESERVATIONS.resvKey
				and resvType = %d
				and CUSTOMERS.custID = '%s'""" %(key, self.RESERVE_BUS, id)
		buses = self.query(sql)

		if verbose:
			if len(buses) == 0:
				print("You haven't reserved any bus yet.")
			else :
				print("Reserved Bus:")
				self.print_query_results(buses)
		
		return buses

	def query_reservation(self, id):
		"""查询航班/大巴/宾馆的预约情况"""	
		choice = self.menu.in_menu("Query Reserced")
		if choice == self.RESERVE_FLIGHT:
			self.query_flights(id, verbose=True)
		elif choice == self.RESERVE_BUS:
			self.query_buses(id, verbose=True)
		elif choice == self.RESERVE_HOTEL:
			self.query_hotels(id, verbose=True)

	def query_travel_route(self, id):
		"""查询客户的旅行线路，即预定的航班信息"""
		flights = self.query_flights(id)
		if len(flights):
			print("You have %d flight reservation(s)!" %(len(flights)))
			for i, flight in enumerate(flights):
				print("flight%d: " %(i) + "From '%s' to '%s'" % (flight['FromCity'], flight['ArivCity']))
		else:
			print("You haven't reserved a flight yet!")

	def check_route_rationality(self, id):
		"""检查线路合理性"""
		flights = self.query_flights(id)
		cities = set()		# 记录线路经过的城市
		for flight in flights :
			cities.add(flight['FromCity'])
			cities.add(flight['ArivCity'])

		buses = self.query_buses(id)
		for bus in buses:
			if bus['location'] not in cities:
				print("Your travel plan is irrational!")	# 如果有预定的大巴车不在航班途经城市，则旅游计划不合理
				return

		hotels = self.query_hotels(id)
		for hotel in hotels :
			if hotel['location'] not in cities:
				print("Your travel plan is irrational!")		# 如果有预定的宾馆不在航班途经城市，则旅游计划不合理
				return
		print("Good plan! Have a nice day!")

	def reserve_flight(self, id):
		"""预约航班"""
		sql = "select * from FLIGHTS where "
		try:
			FromCity, ArivCity = input("Please input your departure city and arrival city"
										" (e.g. Shenzhen Shanghai):").split(" ")
			sql += 'FromCity = "%s" and ArivCity = "%s" and ' % (FromCity, ArivCity)
		except:
			print("invalid input!\nAll Available flights: ")
		sql += """numAvail > 0"""	# 所选航班一定要有座位才行
		flights = self.query(sql)

		if len(flights) == 0 :
			print("Sorry, the flight you want is not available...")
		else:
			# 显示航班信息
			print("We have the following flights:")
			self.print_query_results(flights)
			# 预定航班
			flightNum = "-1"
			flightNums = [flight['flightNum'] for flight in flights]
			while flightNum not in flightNums:
				flightNum = input("Please input the flightNum you want to reserve (input 0 to cancel):")
				if flightNum == "0":
					break
			# 确认	
			if flightNum != "0" :
				ans = input("Are you sure that you want to reserve the flight %s ? (Y/N):" % (flightNum))
				if ans == "Y" or ans == "y" :
					if self.insert_reservation(id, self.RESERVE_FLIGHT, flightNum):
						print("Reserve success!")
					else:
						print("Sorry, your reservation has somehow failed...")
				elif ans == "N" or ans == "n":
					print("Reservation canceled!")

	def reserve_bus(self, id):
		sql = "select * from BUS where "
		try:
			loc = input("Please input the location (e.g. Wuhan): ")
			sql += "location = '%s' " % (loc)
		except:
			print("invalid input!\nAll Available buses: ")
		sql += "and numAvail > 0" 
		buses = self.query(sql)
		if len(buses)==0 :
			print("Sorry, the bus you want is not available...")
		else :
			# 显示大巴车信息
			print("We have the following buses:")
			self.print_query_results(buses)

			# 预定大巴车
			busNum = "-1"
			busNums = [bus['BusNum'] for bus in buses]
			while busNum not in busNums:
				busNum = input("Please input the BusNum you want to reserve (input 0 to cancel):")
				if busNum == "0":
					break
			# 确认		
			if busNum != "0" :
				ans = input("Are you sure that you want to reserve the bus %s ? (Y/N):" % (busNum))
				if ans == "Y" or ans == "y" :
					if self.insert_reservation(id, self.RESERVE_BUS, busNum):
						print("Reservation successed!")
					else:
						print("Sorry, your reservation has somehow failed...")
				elif ans == "N" or ans == "n" :
					print("Reservation canceled!")

	def reserve_hotel(self, id):
		sql = "select * from HOTELS where "
		try:
			loc = input("Please input the location (e.g. Wuhan): ")
			sql += "location = '%s' " % (loc)
		except:
			print("invalid input!\nAll Available hotels: ")
		sql += "and numAvail > 0" 
		hotels = self.query(sql)
		if len(hotels)==0 :
			print("Sorry, the hotel you want is not available...")
		else :
			print("We have the following hotels:")
			self.print_query_results(hotels)

			hotelNum = "-1"
			hotelNums = [hotel['hotelNum'] for hotel in hotels]
			while hotelNum not in hotelNums:
				hotelNum = input("Please input the hotelNum you want to reserve (input 0 to cancel):")
				if hotelNum == "0":
					break
			# 确认		
			if hotelNum != "0" :
				ans = input("Are you sure that you want to reserve the hotel %s ? (Y/N):" % (hotelNum))
				if ans == "Y" or ans == "y" :
					if self.insert_reservation(id, self.RESERVE_HOTEL, hotelNum):
						print("Reservation successed!")
					else:
						print("Sorry, your reservation has somehow failed...")
				elif ans == "N" or ans == "n" :
					print("Reservation canceled!")

	def make_reservation(self, id):
		"""预约航班/大巴/宾馆"""
		choice = self.menu.in_menu("Reserve")
		if choice == self.RESERVE_FLIGHT:
			self.reserve_flight(id)
		elif choice == self.RESERVE_BUS:
			self.reserve_bus(id)
		elif choice == self.RESERVE_HOTEL:
			self.reserve_hotel(id)

	def cancel_reservation(self, id):
		"""取消航班/大巴/宾馆的预订"""
		choice = self.menu.in_menu("Cancel Reserved")	
		
		if choice == self.RESERVE_FLIGHT:
			self.query_flights(id, verbose=True, output_resvNum=True)
			while True:
				resvNum = input("Please input the resvNum you want to cancel (input 0 to quit): ")
				if resvNum == "0":
					return
				sql = """select FromCity, ArivCity
						from RESERVATIONS, FLIGHTS
						where resvKey = flightNum and resvNum = '%s'""" % (resvNum)
				cancel_resv = self.query(sql)
				if len(cancel_resv):
					break
				else:
					print("Sorry, the resvNum does not exist! Please try again.")
		elif choice == self.RESERVE_BUS:
			self.query_buses(id, verbose=True, output_resvNum=True)
			while True :
				resvNum = input("Please input the resvNum you want to cancel (input 0 to quit): ")
				if resvNum == "0":
					return
				sql = """select location
						from RESERVATIONS, BUS
						where resvKey = BusNum and resvNum = '%s'""" % (resvNum)
				cancel_resv = self.query(sql)
				if len(cancel_resv):
					break
				else:
					print("Sorry, the resvNum does not exist! Please try again.")
		elif choice == self.RESERVE_HOTEL:
			self.query_hotels(id, verbose=True, output_resvNum=True)
			while True :
				resvNum = input("Please input the resvNum you want to cancel (input 0 to quit): ")
				if resvNum == "0":
					return
				sql = """select location
						from RESERVATIONS, HOTELS
						where resvKey = hotelNum and resvNum = '%s'""" % (resvNum)
				cancel_resv = self.query(sql)
				if len(cancel_resv):
					break
				else:
					print("Sorry, the resvNum does not exist! Please try again.")
	
		print("Are you sure you want to cancel the following reservation (Y/N)? ")
		self.print_query_results(cancel_resv)
		ans = input("Your choice: ")
		if ans == "Y" or ans == "y":
			self.delete("delete from RESERVATIONS where resvNum = '%s'" % (resvNum))
			print("Reservation canceled!")
		elif ans == "N" or ans == "n" :
			print("Quit")

	def admin_insert(self, choice):
		if choice == 1:	#  插入航班
			flightNum, price, numSeats, FromCity, ArivCity = input("Please input the flight information (flightNum price numSeats FromCity ArivCity): ").split(" ")
			sql = "insert into FLIGHTS values('%s', %d, %d, %d, '%s', '%s')" % (flightNum, int(price), int(numSeats), int(numSeats), FromCity, ArivCity)
		elif choice == 2:	# 插入大巴
			busNum, location, price, numSeats = input("Please input the bus information (busNum location price numSeats):").split(" ")
			sql = "insert into BUS values('%s', '%s', %d, %d, %d)" % (busNum, location, int(price), int(numSeats), int(numSeats))
		elif choice == 3:	# 插入宾馆
			hotelNum, location, price, numRooms = input("Please input the hotel information (hotelNum location price numRooms):").split(" ")
			sql = "insert into HOTELS values('%s', '%s', %d, %d, %d)" % (hotelNum, location, int(price), int(numRooms), int(numRooms))
		elif choice == 4:	# 插入客户
			custID, custName = input("Please input the customer information (custID custName):").split(" ")
			sql = "insert into CUSTOMERS values('%s', '%s')" % (custID, custName)
		if self.insert(sql):
			print("Insert successed!")
		else :
			print("Insert failed!")

	def admin_delete(self, choice):	
		if choice == 1:	#  删除航班
			flightNum = input("Please input the flightNum you want to delete:")
			sql = "delete from FLIGHTS where flightNum = '%s'" % (flightNum)
		elif choice == 2:	# 删除大巴
			busNum = input("Please input the busNum you want to delete:")
			sql = "delete from BUS where busNum = '%s'" % (busNum)
		elif choice == 3:	# 删除宾馆
			hotelNum = input("Please input the hotelNum you want to delete:")
			sql = "delete from HOTELS where hotelNum = '%s'" % (hotelNum)
		else:	# 删除客户
			custID = input("Please input the custID you want to delete:")
			sql = "delete from CUSTOMERS where custID = '%s'" % (custID)
		if self.delete(sql):
			print("delete successed!")
		else :
			print("delete failed!")

	def admin_query(self, choice):
		if choice == 1:	# 查询航班
			sql = "select * from FLIGHTS"
			flights = self.query(sql)
			if len(flights) == 0 :
				print("No flight.")
			else :
				print("Flights:")
				self.print_query_results(flights)
		elif choice == 2:	# 查询大巴车
			sql = "select * from BUS"
			buses = self.query(sql)
			if len(buses)==0 :
				print("No bus.")
			else :
				print("buses:")
				self.print_query_results(buses)
		elif choice == 3:	# 查询宾馆
			sql = "select * from HOTELS"
			hotels = self.query(sql)
			if len(hotels) == 0 :
				print("No hotel.")
			else :
				print("hotels:")
				self.print_query_results(hotels)
		elif choice == 4:	# 查询客户
			sql = "select * from CUSTOMERS"
			custs = self.query(sql)
			if len(custs) == 0 :
				print("No customer.")
			else :
				print("customers:")
				self.print_query_results(custs)
		elif choice == 5: # 查看预定信息
			opt = input("Which one do you want to check? 1.flight / 2.bus / 3.hotel (1~3): ")
			
			if opt == "1":	# 查询航班预定信息
				sql = """select resvNum, CUSTOMERS.custID, flightNum, price, FromCity, ArivCity
							from RESERVATIONS, CUSTOMERS, FLIGHTS
							where resvKey = flightNum and resvType = %d
								and RESERVATIONS.custID = CUSTOMERS.custID""" %(self.RESERVE_FLIGHT)
				flights = self.query(sql)
				if len(flights) == 0 :
					print("No flight reservation!")
				else :
					print("Reserved flight:")
					self.print_query_results(flights)		
			elif opt == "2":	# 查询大巴车预定信息
				sql = """select resvNum, CUSTOMERS.custID, BusNum, price, location
							from RESERVATIONS, CUSTOMERS, BUS
							where resvKey = busNum and resvType = %d
								and RESERVATIONS.custID = CUSTOMERS.custID""" %(self.RESERVE_BUS)
				buses = self.query(sql)
				if len(buses)==0 :
					print("No bus reservation!")
				else :
					print("Reserved bus:")
					self.print_query_results(buses)	
			elif opt == "3":	# 查询宾馆预定信息
				sql = """select resvNum, CUSTOMERS.custID, hotelNum, price, location
						from RESERVATIONS, CUSTOMERS, HOTELS
						where resvKey = hotelNum and resvType = %d
							and RESERVATIONS.custID = CUSTOMERS.custID""" % (self.RESERVE_HOTEL)
				hotels = self.query(sql)
				if len(hotels)==0 :
					print("No hotel reservation!")
				else :
					print("Reserved hotel:")
					self.print_query_results(hotels)	

	def admin_update(self, choice):
		if choice == 1:	#  更新航班
			flightNum = input("Please input the flightNum: ")
			attr, new_val = input("Please input the attribute you want to alter and its new value (e.g. price 100): ").split(" ")
			sql = "update FLIGHTS set %s = %s where flightNum = %s" % (attr, new_val, flightNum)
		elif choice == 2:	# 更新大巴
			BusNum = input("Please input the BusNum: ")
			attr, new_val = input("Please input the attribute you want to alter and its new value (e.g. price 100): ").split(" ")
			sql = "update BUS set %s = %s where BusNum = %s" % (attr, new_val, BusNum)
		elif choice == 3:	# 更新宾馆
			hotelNum = input("Please input the hotelNum: ")
			attr, new_val = input("Please input the attribute you want to alter and its new value (e.g. price 100): ").split(" ")
			sql = "update HOTELS set %s = %s where hotelNum = %s" % (attr, new_val, hotelNum)
		elif choice == 4:	# 更新客户
			custID = input("Please input the custID: ")
			attr, new_val = input("Please input the attribute you want to alter and its new value (e.g. custName lianlio): ").split(" ")
			sql = "update CUSTOMERS set %s = %s where custID = %s" % (attr, new_val, custID)
		if self.insert(sql):
			print("Update successed!")
		else :
			print("Update failed!")

def run(bookingDB):
	while True:
		id = bookingDB.menu.log_in_menu()
		if id == "admin":	# 系统管理员可以进行任意的增删改查或直接执行SQL语句
			while True:
				choice = bookingDB.menu.main_menu(is_admin=True)
				if choice == 0:
					print("---------------System log out--------------")
					break
				elif choice == 6:
					while True:
						print("Please input MySQL instructors in ONE line (Input exit to quit)")
						command = input()
						if command == "exit":
							break
						if bookingDB.execute(command):
							print("Executed successfully :)")
						else:
							print("ERROR! Please check your SQL instr. again!")
					break
				# 增删查改
				if choice in [1, 2, 3, 4]:
					op = input("1.Insert   2.Delete   3.Query   4.Update  0.Back\nYour choice: ")
					if op == "1":
						bookingDB.admin_insert(choice)
					elif op == "2":
						bookingDB.admin_delete(choice)
					elif op == "3":
						bookingDB.admin_query(choice)
					elif op == "4":
						bookingDB.admin_update(choice)
				elif choice == 5:	# 查询预约
					bookingDB.admin_query(choice)
		else:	# 用户端服务
			if id not in bookingDB.query_custID(id):
				print("Welcome to the booking system!\nPlease sign up first :)")
				name = input("Your Name: ")
				if bookingDB.insert_customer(id, name) :
					print("Sign up successed! Hope you enjoy the system!")
			else:
				cust_name = bookingDB.query_custName(id)
				print("Log in successed!")
				print("Hi " + cust_name + "! Welcome back :)")
			
			while True:
				choice = bookingDB.menu.main_menu()
				if choice == 1:
					bookingDB.make_reservation(id)
				elif choice == 2:
					bookingDB.query_reservation(id)
				elif choice == 3:
					bookingDB.cancel_reservation(id)
				elif choice == 4:
					bookingDB.query_travel_route(id)
				elif choice == 5:
					bookingDB.check_route_rationality(id)
				else:
					break

if __name__ == '__main__':
	user = 'root'
	password = input("Please input your Database password: ")
	bookingDB = BookingSys(user=user, password=password)
	run(bookingDB)
