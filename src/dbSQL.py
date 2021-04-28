import pymysql

class Database:
	def __init__(self, user, password, dbname):
		self.DBUser = user
		self.DBPassword = password
		self.DBName = dbname

	def connect(self):
		"""打开数据库连接"""
		return pymysql.connect(host="localhost", 
								user=self.DBUser, 
								password=self.DBPassword, 
								database=self.DBName, 
								charset='utf8mb4',
								cursorclass=pymysql.cursors.DictCursor)

	def execute(self, sql):
		"""
		执行 SQL 语句: 增、删、改
			@sql: SQL 语句组成的字符串
		"""
		db = self.connect()
		cursor = db.cursor()	# 使用 cursor() 方法获取操作游标
		try:
			cursor.execute(sql)	# 执行SQL语句
			db.commit()			# 提交到数据库执行
			db.close()			# 关闭数据库连接
			return True
		except:
			db.rollback()		# 如果发生错误则回滚
			db.close()
			print("Warning: SQL ERROR!")
			return False

	def insert(self, sql):
		return self.execute(sql)

	def delete(self, sql):
		return self.execute(sql)

	def update(self, sql):
		return self.execute(sql)

	def query(self, sql):
		"""
		执行 SQL 语句: 查询，返回全部表
			@sql: SQL 语句组成的字符串
		"""
		db = self.connect()
		cursor = db.cursor()
		result = ()
		try:
			cursor.execute(sql)
			result = cursor.fetchall()	# 获取所有记录列表
		except:
			db.rollback()
			print("Warning: SQL ERROR!")
		finally:
			db.close()
		return result

	def print_query_results(self, res):
		if len(res) == 0:
			return

		def print_sep():
			print('+' + '-' * (11 * len(res[0].keys()) + 3) + '+')
		
		print_sep()
		print('| ', end="")
		for key in res[0].keys():
			print("%-10s" %(key), end=' ')		# 打印表头
		print(' |')
		print_sep()
		for row in res:
			print('| ', end="")
			for val in row.values():
				print("%-10s" %(str(val)), end=' ')
			print(' |')
		print_sep()





