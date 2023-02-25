class Base():
    DEBUG = False
    TESTING = False

class dev(Base):
    DEBUG = True
    DEVELOPMENT = True
    LISTEN_ADDRESS = '127.0.0.1'
    LISTEN_PORT = 5000

class prod(Base):
    DEBUG = False
    TESTING = False
    DATABASE_URI = 'mysql+mysqldb://root:root@prod_host_name/demo_prod'
    LISTEN_ADDRESS = '209.94.59.175'
    LISTEN_PORT = 5000

