from amqp_collector import collectiondb
from influxdb import InfluxDBClient

class CollectionDbInflux(collectiondb.CollectionDB):
    def __init__(self, host, port, user, password, database):
        super(CollectionDbInflux, self).__init__(host, port, user, password, database)
        self._client = ""
    def connect(self):
        """
       :param parameters: Parameters to connect to database: host, port, username, password, database.
       :type parameters: dict.
       :return: An Influx database client connector.
       :rtype: influxdb.client.InfluxDBClient.
        """
        self._client = InfluxDBClient(self._host,self._port , self._user, self._password, self._database)


    def create_database(self):
        dblist =self._client.get_list_database()
        if self._database not in dblist:
            self._client.create_database(dbname=self._database)


    def delete_database(self,dbname):
        self._client.drop_database(dbname=dbname)


    def disconnect(self):
        pass

    def insert_data(self,data):
        """
        :type self._client:  InfluxDBClient
        :return: 
        """
        # print("Write points: {0}".format(data))

        # data= [{'measurement': 'host_metrics', 'fields': {'if_packets_rx': 0, 'if_packets_tx': 0},
        #           'tags': {'host': 'localhost', 'instance': 'ip6tnl0'}, 'time': 1503457480}]
        try:
            self._client.write_points(data)
        except Exception as err:
            print("Influxdb Write error {0} caught while writing {1}:",err,data)
        pass

    def save_all(self):
        pass
