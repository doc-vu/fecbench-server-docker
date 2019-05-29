import json
import datetime
import time
import threading
from amqp_collector import collectiondb_influx
from datetime import datetime


class CollectdParser(threading.Thread):

    def __init__(self,parsingQ,dbconn):
        """
      :param parsingQ: Parsing Queue(instance) shared with Rabbitmq
      :type parsingQ: object
      :param dbconn: Database connection
      :type dbconn: collectiondb_influx.CollectionDbInflux
      
       """
        self.parsingQ = parsingQ
        threading.Thread.__init__(self)
        self.count = 0
        self.dbconnection =dbconn
        pass

    def parse(self, msgJSON):

        # {
        #     "dsnames": [
        #         "rx",
        #         "tx"
        #     ],
        #     "dstypes": [
        #         "derive",
        #         "derive"
        #     ],
        #     "host": "129.59.234.236",
        #     "interval": 10.0,
        #     "plugin": "interface",
        #     "plugin_instance": "eno3",
        #     "time": 1508606511.426,
        #     "type": "if_packets",
        #     "type_instance": "",
        #     "values": [
        #         null,
        #         null
        #     ]
        # }

        self.count+=1
        # print(self.count)
        if type(msgJSON) is bytes:
            msg = json.loads(msgJSON.decode("utf-8"))
        elif type(msgJSON) is str:
            msg = json.loads(msgJSON.encode().decode("utf-8"))

        # this is going to parse the message
        # msg = json.loads(msgJSON.encode().decode("utf-8") )
        # print(json.dumps(msg))
        data = msg[0]
        # print(json.dumps(data, sort_keys=True, indent=4))

        pointValue = {}

        try:
            measurement = "host_metrics"

            tag = {
                'host': data["host"],
                'instance': data["plugin_instance"]
            }
            plugin_type = data['plugin']
            field = {}
            field["interval"] = float(data["interval"])

            if plugin_type == 'cuda':
                #print("cuda---------------------")
                measurement = 'host_gpu_metrics'
                tag['instance'] = data['plugin_instance']
                for ds_name in range(len(data['dsnames'])):
                    field_str = data['type']
                    if data['type_instance'] != "":
                        field_str += "_" + data['type_instance']
                    field_str +=  "_" + data['dsnames'][ds_name]
                    field[field_str] = float(data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;

            elif plugin_type == 'intel_pmu':
                measurement = 'host_metrics_micro'
                # tag['instance'] = data["plugin_instance"]
                tag['instance'] = "all" #data["plugin_instance"]
                if(len(data['dsnames'])>1):
                    print("New Parameter")
                # for ds_name in range(len(data['dsnames'])):
                    # field[data['type'] + "_" + data['dsnames'][ds_name]] = data["values"][ds_name] if data["values"][ds_name] != None else 0 ;
                if((data["values"][0] == "nan")):
                    print("error nan")
                field[data['type_instance']] = float(data["values"][0]) if (data["values"][0] != None) and (data["values"][0] != "nan") else 0.0;
                #print(field[data['type_instance']])
            # print(json.dumps(tag, sort_keys=True, indent=4))
            # print(json.dumps(field, sort_keys=True, indent=4))


            elif plugin_type == 'cpu':
                measurement = 'host_metrics'
                tag['instance'] = "all" #data["plugin_instance"]
                # field = {}
                # field["cpu"+"_"+data['type_instance']+"_"+ data["type"]] = float(data["values"][0]) if data["values"][0] != None else 0.0;
                field['cpu'] = float(data["values"][0]) if data["values"][0] != None else 0.0;

            elif plugin_type == 'load':
                measurement = 'host_metrics'
                tag['instance'] = "all" #data["plugin_instance"]
                # field = {}
                field["load"+"_"+"short"] = float(data["values"][0]) if data["values"][0] != None else 0.0;
                field["load" + "_" + "med"] = float(data["values"][1]) if data["values"][1] != None else 0.0;
                field["load" + "_" + "long"] = float(data["values"][2]) if data["values"][2] != None else 0.0;

            elif plugin_type == 'memory':
                measurement = 'host_metrics'
                tag['instance'] = "all"#data["plugin_instance"]
                # field = {}
                # field["memory"+"_"+data['type_instance']] = float(data["values"][0]) if data["values"][0] != None else 0.0;
                if data['type_instance']== 'used':
                    field["memory"] = float(data["values"][0]) if data["values"][0] != None else 0.0;
                else:
                    field["memory"+"_"+data['type_instance']] = float(data["values"][0]) if data["values"][0] != None else 0.0;


            elif plugin_type == 'numa-group':
                measurement = 'numa'
                tag['instance'] = data["plugin_instance"]
                # field = {}
                #print(data)
                field[data["type_instance"]] = float(data["values"][0]) if data["values"][0] != None else 0.0;

            elif plugin_type == 'intel_rdt':
                # For the Intel_rdt we could use this either on a numa_group basis
                # or for an aggregate basis only!
                # So if it report for all core using Core "0-15" --> then we store it to the host_metrics stats.
                numa_string =data["plugin_instance"]


                if numa_string.find("0,") != -1:
                    measurement = 'numa'
                    tag['instance'] = 0
                    # tag['node'] = data["plugin_instance"]
                elif numa_string.find("1,") != -1:
                    measurement = 'numa'
                    tag['instance'] = 1
                    # tag['node'] = data["plugin_instance"]
                elif numa_string.find("0-")!=-1:
                    measurement = 'host_metrics'
                    #print(data)
                    tag['instance'] = "all"  # data["plugin_instance"]
                # field = {}
                # field[data['type']+"_"+data['type_instance']] = float(data["values"][0]) if data["values"][0] != None else 0.0;

                field_str = data['type']
                if data['type_instance'] != "":
                    field_str += "_"+data['type_instance']

                field[field_str] = float(data["values"][0]) if data["values"][0] != None else 0.0;
                #print(field)

            elif plugin_type == 'disk':
                measurement = 'host_metrics'
                # tag['instance'] = "all"#data["plugin_instance"]
                tag['instance']= "all"
                # label = "elegant_noether[federation=federationA,federate=taskName]"
                # field = {}

                for ds_name in range(len(data['dsnames'])):
                    field_str = data['type']
                    if data['type_instance'] != "":
                        field_str += "_" + data['type_instance']
                    field_str +=  "_" + data['dsnames'][ds_name]
                    field[field_str] = float(data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;


            elif plugin_type == 'docker':
                measurement = 'container_metrics'
                # tag['instance'] = "all"#data["plugin_instance"]
                tag['instance']= data['plugin_instance']
                # label = "elegant_noether[federation=federationA,federate=taskName]"
                label = data['plugin_instance']
                label = label.replace("[", ",")
                label = label.replace("]", "")
                list = label.split(",")
                # first label is the container name
                container_name = list[0]
                # print(container_name)

                d = dict(s.split('=') for s in list[1:])
                # print(d)
                if(d):
                    if 'federation' in d:
                        # print(d['federation'])
                        tag['federation'] = d['federation']
                    if 'federate' in d:
                        # print(d['federation'])
                        tag['federate'] = d['federate']
                else:
                    tag['instance'] = data['plugin_instance']
                # if 'federate' in d:
                #     # print(d['federate'])
                #     instance = instance +"-" +d['federate']

                # field = {}

                for ds_name in range(len(data['dsnames'])):
                    field_str = data['type']
                    if data['type_instance'] != "":
                        field_str += "_" + data['type_instance']
                    field_str +=  "_" + data['dsnames'][ds_name]
                    field[field_str] = float(data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;

            elif plugin_type == 'aggregation':
                measurement = 'host_metrics'
                # field = {}
                tag['instance']= 'all'
                if data['plugin_instance']== "cpu-average":
                    field['cpu'] = float(data["values"][0]) if data["values"][0] != None else 0.0;

            # elif plugin_type == 'indices_uptime':
            #     measurement = 'host_metrics'
            #     tag['instance'] = 'all'
            #     field['uptime'] = int(data["values"][0]) if data["values"][0] != None else 0

            elif plugin_type == 'interface':
                # print(data)
                measurement = 'host_metrics'
                # field = {}
                tag['instance']= 'all'
                for ds_name in range(len(data['dsnames'])):
                    # if(data['dsnames'][ds_name]=="l3_bw" or data['dsnames'][ds_name]=="mem_bw"):
                        # print("l3_bw or mem_bw")
                    field[data['type'] + "_" + data['dsnames'][ds_name]] = float(
                        data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;    

            elif plugin_type == 'contextswitch':
                measurement = 'host_metrics'
                # field = {}
                tag['instance']= 'all'
                field['contextswitch'] = float(data["values"][0]) if data["values"][0] != None else 0.0;

            elif plugin_type == 'linux_perf':
                measurement = 'host_metrics'
                # field = {}
                tag['instance'] = 'all'
                # 10733, 7705, -1, -1, -1, -1, 10755, 682929524, 5515004
                # field['page-faults'] = float(data["values"][1]) if data["values"][1] != None else 0.0;
                # field['sched-switch'] = float(data["values"][6]) if data["values"][6] != None else 0.0;
                # field['sched-wait'] = float(data["values"][7]) if data["values"][7] != None else 0.0;
                # field['sched-iowait'] = float(data["values"][8]) if data["values"][8] != None else 0.0;

                for ds_name in range(len(data['dsnames'])):
                    # print(ds_name)
                    # if(data['dsnames'][ds_name]=="l3_bw" or data['dsnames'][ds_name]=="mem_bw"):
                        # print("l3_bw or mem_bw")
                    field_str =  data['dsnames'][ds_name]
                    field[field_str] = float(data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;   


            elif plugin_type == 'linux_perf_plus':
                #b'[{"values":[921156,12806,0],"dstypes":["gauge","gauge","gauge"],"dsnames":["cs","page-faults","major-faults"],"time":1516046622.650,"interval":5.000,"host":"localhost","plugin":"linux_perf_plus","plugin_instance":"all","type":"indices_perf_host","type_instance":""}]'
                # b'[{"values":[10,12845],"dstypes":["gauge","gauge"],"dsnames":["cs","page-faults"],"time":1516046622.650,"interval":5.000,"host":"localhost","plugin":"linux_perf_plus","plugin_instance":"img_server","type":"indices_perf_docker","type_instance":""}]'

                label = data['type']

                if label=='indices_perf_host':
                    measurement = 'host_metrics'
                    tag['instance'] = 'all'


                elif label=='indices_perf_docker':
                    measurement = 'container_metrics'
                    tag['instance'] = data['plugin_instance']
                
                field_str=""
                for ds_name in range(len(data['dsnames'])):
                    field_str =  data['dsnames'][ds_name]
                    field[field_str] = float(data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;
            elif plugin_type == 'likwid-perf':
#b'[{"values":[0,0,0,0],"dstypes":["gauge","gauge","gauge","gauge"],"dsnames":["mem_bw","l1_2_bw","l2_3_bw","l3_bw"],"time":1517344008.593,"interval":5.000,"host":"129.59.234.236","plugin":"likwid-perf","plugin_instance":"all","type":"likwid_memory_bw","type_instance":""}]'
                label = data['type']
                measurement = 'host_metrics_micro'
                tag['instance'] = 'all'
                field_str=""
                # print(data['dsnames'])
                # print(data["values"])
                for ds_name in range(len(data['dsnames'])):
                    # print(ds_name)
                    # if(data['dsnames'][ds_name]=="l3_bw" or data['dsnames'][ds_name]=="mem_bw"):
                        # print("l3_bw or mem_bw")
                    field_str =  data['dsnames'][ds_name]
                    field[field_str] = float(data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;         

            else:
                #print("UNKNOWWWWW-*****")
                measurement = 'unknown'
                # tag['instance'] = "all"#data["plugin_instance"]
                tag['instance'] = data['plugin_instance']

                # field = {}

                for ds_name in range(len(data['dsnames'])):
                    field[data['type'] + "_" + data['type_instance'] + "_" + data['dsnames'][ds_name]] = float(
                        data["values"][ds_name]) if data["values"][ds_name] != None else 0.0;

#            print(plugin_type,datetime.utcfromtimestamp(float(data["time"]+0.5)).strftime('%Y-%m-%d %H:%M:%S'), float(data["time"]+0.5),(data["time"]))
#             if plugin_type == 'cuda':
#                 print(plugin_type, measurement, field)

            pointValue = {
                "measurement" : measurement,
                "fields" : field,
                "tags" : tag,
                "time": datetime.utcfromtimestamp(float(data["time"]+0.5)).strftime('%Y-%m-%d %H:%M:%S')
#
#                "time": datetime.fromtimestamp(float(data["time"]+0.5)).strftime('%Y-%m-%d %H:%M:%S')

            }
            #print(pointValue)

        except Exception:
             print("error is:",Exception)
             pass

        return pointValue

    

    def run(self):
        from threading import Lock
        lock = Lock()
        print("waiting for the queue:")
        end=0
        start=0
        current =time.time()
        last = 0
        while True:
            if not self.parsingQ.empty():
                msg = self.parsingQ.get()
                lock.acquire()
                parsed_data = self.parse(msg)              # queueLock.release()
                lock.release()

                # print(json.dumps(parsed_data, sort_keys=True, indent=4))
                points = []
                points.append(parsed_data)
                self.dbconnection.insert_data(points)
                last = time.time()
            else:
                #if last != 0:
                   #print(last-current)
                current = time.time()
                last = 0




        # jsonObj1 = '{"values":[0,0],"dstypes":["derive","derive"],"dsnames":["rx","tx"],"time":1503025766.097,"interval":10.000,"host":"localhost","plugin":"interface","plugin_instance":"gretap0","type":"if_octets","type_instance":""}'
        # print("time is: ", datetime.datetime.fromtimestamp(msg['time']).strftime('%Y-%m-%d %H:%M:%S'))
