import os


if os.getenv('USE_PYMYSQL', '0').lower() in ('1', 'true', 'yes', 'on'):
	try:
		import pymysql

		pymysql.install_as_MySQLdb()
	except Exception:
		pass

