from abc import ABCMeta, abstractmethod

class CollectionDB(object):

    def __init__(self, host, port, user, password, database):

        self._host = host;
        self._port = port;
        self._user = user;
        self._password = password;
        self._database = database;

    @abstractmethod
    def connect(self,parameters):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self,parameters):
        raise NotImplementedError

    @abstractmethod
    def insert_data(self,data):
        raise NotImplementedError

    @abstractmethod
    def create_database(self,dbname):
        raise NotImplementedError

    @abstractmethod
    def delete_database(self,dbname):
        raise NotImplementedError

    @abstractmethod
    def save_all(self):
        raise NotImplementedError