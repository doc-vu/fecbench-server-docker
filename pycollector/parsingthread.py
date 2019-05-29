
import queue
from amqp_collector import amqp_listener
from amqp_collector import collectd_parser
from amqp_collector import collectiondb_influx
import json

#
# {
#   "host": "0.0.0.0",
#   "port": "5672",
#   "user": "indices_user",
#   "password": "indices_manager",
#   "exchange": "collectd-exchange",
#   "exchangetype": "direct",
#   "queue": "collectd_queue",
#   "bindingkey": "indices-perf-key",
#   "consumertag": "simple-consumer"
# }
with open('amqp_settings.json') as json_file:
    amqp_setting = json.load(json_file)

# {
#   "type": "influx",
#   "host": "localhost",
#   "port": "8086",
#   "user": "indices_user",
#   "password": "indices_manager",
#   "database": "temp_collectd_db"
# }


with open('influx_settings.json') as influxjson_file:
    influxdb_setting = json.load(influxjson_file)



amqpconnectionstring = "amqp://"+amqp_setting["user"]+":"+amqp_setting['password']+"@"+amqp_setting['host']+":"+amqp_setting['port']
print(amqpconnectionstring)

example = amqp_listener.AmqpListener(amqpconnectionstring, amqp_setting['exchange'],amqp_setting['exchangetype'] ,
                       amqp_setting['queue'], amqp_setting['bindingkey'], amqp_setting['consumertag'])

parsing_queue = queue.Queue();

influxdb = collectiondb_influx.CollectionDbInflux(host=influxdb_setting['host'],port=influxdb_setting["port"],user=influxdb_setting["user"],password=influxdb_setting["password"],database=influxdb_setting["database"])
influxdb.connect()
influxdb.create_database()
#
example.set_ParsingQueue(parsing_queue)

# Create new threads

for tName in range(0,15):
   collectd = collectd_parser.CollectdParser(parsing_queue, influxdb)
   collectd.start()
#
#
#
# collectd = collectd_parser.CollectdParser(parsing_queue,influxdb)
#
# collectd.start()
# # for i in range(0,1):
# #     parsing_queue.put('[{"values":[0,0],"dstypes":["derive","derive"],"dsnames":["rx","tx"],"time":1503025766.097,"interval":10.000,"host":"localhost","plugin":"interface","plugin_instance":"gretap0","type":"if_octets","type_instance":""}]');
# #     parsing_queue.put('[{"values":[0,0],"dstypes":["derive","derive"],"dsnames":["rx","tx"],"time":1503025766.097,"interval":10.000,"host":"localhost","plugin":"interface","plugin_instance":"gretap0","type":"if_octets","type_instance":""}]');
# #     parsing_queue.put('[{"values":[0,0],"dstypes":["derive","derive"],"dsnames":["rx","tx"],"time":1503025766.097,"interval":10.000,"host":"localhost","plugin":"interface","plugin_instance":"gretap0","type":"if_octets","type_instance":""}]');
# #     parsing_queue.put('[{"values":[0,0],"dstypes":["derive","derive"],"dsnames":["rx","tx"],"time":1503025766.097,"interval":10.000,"host":"localhost","plugin":"interface","plugin_instance":"gretap0","type":"if_octets","type_instance":""}]');
# #     parsing_queue.put('[{"values":[0,0],"dstypes":["derive","derive"],"dsnames":["rx","tx"],"time":1503025766.097,"interval":10.000,"host":"localhost","plugin":"interface","plugin_instance":"gretap0","type":"if_octets","type_instance":""}]');
# # print("done sending data")
example.start()
