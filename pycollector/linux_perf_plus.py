import collectd
import subprocess
import datetime, time
import os
import ConfigParser
import threading
import signal



# converts string for processing
def get_number(s):
    try:
        return float(s)
    except ValueError:
        return -1

def parse_and_set_result(file_name):
        all_vals = []
        try:
                with  open(file_name, 'r') as f:
                        count = 0
                        for line in f:
                                count += 1
                                
                                if count < 3:
                                        continue
                                #print("count",count)
                                linevals = line.split(',')
                                print(linevals[0])
                                all_vals.append(get_number(linevals[0]))
        except IOError:
                print "=================Error: File does not appear to exist."
                return 0                
        
        return all_vals


# refreshes the list of vms to check for new vms
def refresh_dockername_list():
        p = subprocess.Popen("docker ps" , shell=True,  stdout=subprocess.PIPE)
        out,err = p.communicate()
        global _vmmap
        _vmmap = {}
        counter =0
        for line in out.splitlines():
                counter+=1
                if(counter<2):
                        continue
                vmname = line.split()
                vmname = vmname[-1]
                # print vmname
                if vmname != "":
                        _vmmap[vmname] = None

# adds additional details for processing
def fill_docker_details():
        global _vmmap
        vmkeys = _vmmap.keys()
        print(_vmmap)
        for vmname in vmkeys:
                # assuming we are using libvirt to run the vms
                p = subprocess.Popen("docker inspect --format={{.Id}} " + vmname , shell=True,  stdout=subprocess.PIPE)
                vmid = p.communicate()[0]
                # print(vmid)
                _vmmap[vmname] = vmid.strip()



def get_vm_perf_copy_command():
        # _temp_out ="/home/vagrant/temp"
        command = []
        
        for vmname, data in _vmmap.iteritems():
                copycommand = "sudo cp " +_temp_out + "/"+ vmname + "_all.out " +" " + _temp_out + "/"+vmname + "_all.out_result"
                print(copycommand)                
                command.append(copycommand)

                # command_default =   comm_pre + vmname + "_all.out " + " -e  cs,page-faults,cycles,instructions " +  " --cgroup=docker/" + data + comm_post
                # command.append(command_default)
                # #command_cache =   comm_pre + vmname + "_cache.out " + " -e  cache-references,cache-misses " +  " --cgroup=docker/" + data + comm_post
                # command_cache =   comm_pre + vmname + "_cache.out " + " -e  cache-misses,cache-misses " +  " --cgroup=docker/" + data + comm_post
                # command.append(command_cache)
                # command_membw =   "echo 0,,mebw > " + _temp_out + "/" + vmname + "_membw.out "
                # command.append(command_membw)
                # command_kvm =   comm_pre + vmname + "_kvm.out " + " -e  sched:sched_switch,kvm:kvm_exit,sched:sched_stat_wait,sched:sched_stat_iowait" +  " --cgroup=docker/" + data + comm_post
                # command.append(command_kvm)
        return command
        

def get_vm_perf_command():
        # _temp_out ="/home/vagrant/temp"
        # _duration = "5"
        

        comm_pre =  "sudo perf stat -a -x , -o " + _temp_out + "/"
        comm_post =  " sleep " + _duration
        command = []
        
        for vmname, data in _vmmap.iteritems():
                command_default =   comm_pre + vmname + "_all.out " + " -e "+ _docker_perf_metric +  " --cgroup=docker/" + data + comm_post
                command.append(command_default)

                # command_default =   comm_pre + vmname + "_all.out " + " -e  cs,page-faults,cycles,instructions " +  " --cgroup=docker/" + data + comm_post
                # command.append(command_default)
                # #command_cache =   comm_pre + vmname + "_cache.out " + " -e  cache-references,cache-misses " +  " --cgroup=docker/" + data + comm_post
                # command_cache =   comm_pre + vmname + "_cache.out " + " -e  cache-misses,cache-misses " +  " --cgroup=docker/" + data + comm_post
                # command.append(command_cache)
                # command_membw =   "echo 0,,mebw > " + _temp_out + "/" + vmname + "_membw.out "
                # command.append(command_membw)
                # command_kvm =   comm_pre + vmname + "_kvm.out " + " -e  sched:sched_switch,kvm:kvm_exit,sched:sched_stat_wait,sched:sched_stat_iowait" +  " --cgroup=docker/" + data + comm_post
                # command.append(command_kvm)
        return command

class PerfRecorder(threading.Thread):
        def __init__(self):
                threading.Thread.__init__(self)
                self._stop_event = threading.Event()
                pass
        
        def stop(self):
                # print("calling stop!")
                collectd.info('Stopping the Recorder thread!.. ')

                self._stop_event.set()
        
        def stopped(self):
                return self._stop_event.is_set()

        def run(self):
            while not self._stop_event.is_set():
                # _temp_out ="/home/vagrant/temp"
                file_name = _temp_out+"/all.out"
                # _duration = "5"

                host_command =  "sudo perf stat -x , -o " +  _temp_out + "/all.out " + " -e "+_host_perf_metric
                
                #host_command =  "perf stat -x , -o " +  _temp_out + "/all.out " + " -e cs,page-faults,cycles,instructions,cache-references,cache-misses,"
                #host_command += "sched:sched_switch,sched:sched_stat_wait,sched:sched_stat_iowait" + " -a sleep " + _duration
                host_command += " -a sleep " + _duration

                commands = [host_command]
                
                if _collectvm:
                    print("calling refresh...")
                    collectd.info('calling refresh of the docker list!.. ')
                    refresh_dockername_list()
                    fill_docker_details()
                    vm_commands = get_vm_perf_command()
                    commands.extend(vm_commands)
    
                processes = [subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE) for cmd in commands]

                for p in processes:
                        p.wait()

                # ----------- Complete the execution of perf commands first and then start copying the  results
                file_name_save = file_name+"save"     
                copycommand = "sudo cp " + file_name+ " " + file_name_save

                commands = [copycommand]        
                # processes = [subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE) for cmd in commands]
                # for p in processes:
                #         p.wait()
                if _collectvm:
                    vm_copy_commands = get_vm_perf_copy_command()        
                    commands.extend(vm_copy_commands)

                # commands = [vm_copy_commands]
                processes = [subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE) for cmd in commands]
                for p in processes:
                        p.wait()

def shutdown():
    global collectd_thread
    collectd_thread.stop()


# initialize
def init():
        # collectd.debug('Initializing plugin')
        
        global collectd_thread 
        collectd_thread = PerfRecorder()
        collectd_thread.start()
        # collectd_thread.join()

        if _collectvm:
                if (not _isvmnamesupplied):
                        print("calling refresh dockername_list")
                        refresh_dockername_list()
                        # _refresh_time = time.time()
                # fill_vm_details()
                fill_docker_details()


# reads the initial configuration of the service
def configure(configobj):
    collectd.debug('Configuring plugin')
    config = {c.key: c.values for c in configobj.children}

    global _duration
    global _vmmap
    global _refresh_interval
    global _collectvm
    global _isvmnamesupplied
    global _refresh_time
    global _temp_out

    # should be comma seperated string to be appended to the perf -e "string"
    global _host_perf_metric
    global _docker_perf_metric

    # _host_perf_metric = "cs,page-faults,major-faults"
    # _host_perf_metric = "cs,page-faults,power/energy-cores/,power/energy-ram/,major-faults"
    # _host_perf_metric = "power/energy-cores/,power/energy-ram/"
    # _docker_perf_metric = "power/energy-cores/,power/energy-ram/,power/energy-pkg/"
    



    # _docker_perf_metric = "cs,page-faults"
    _host_perf_metric =config.get("host_perf_metric")[0]
    _duration = str(config.get("duration")[0])
    _temp_out = config.get("temp_output_dir")[0]
    _collectvm = config.get("collect_container")[0]

    if not os.path.exists(_temp_out):
        os.makedirs(_temp_out)
    
    # _duration = "5"
    # _temp_out = "/home/vagrant/temp"
    # _collectvm = True

    if _collectvm:
            _isvmnamesupplied = False
            _docker_perf_metric =config.get("docker_perf_metric")[0]
            _vmmap = {}

            # _refresh_time = time.time()
            
            # _refresh_interval = config.get("refresh_interval")[0]

            vmconfig = config.get("container_name")
            
            if vmconfig is not None:
                    _isvmnamesupplied = True
                    _vmmap = {config.get("container_name")[0] : None}



def reader(input_data=None):
        out_all = collectd.Values();
        out_all.plugin = 'linux_perf_plus'
        out_all.type = 'indices_perf_host'


        out_all.plugin_instance = "all"
        file_name = _temp_out+"/all.out"
        file_name_save = file_name+"save" 
        all_vals = parse_and_set_result(file_name_save)
        print(all_vals)

        out_all.values = all_vals
        collectd.info('dipatching: '+ str(out_all.plugin_instance) +": "+ str(out_all.values))
        out_all.dispatch()

        if _collectvm:

            filename_sfx_list = ["_all.out_result"]
            global _vmmap
            for vmname, data in _vmmap.iteritems():
                    all_vals = []
                    # out_all.plugin_instance = data[1]
                    out_all.plugin_instance = vmname
                    out_all.type = 'indices_perf_docker'
                    collectd.debug(vmname+":"+data)
                    # print(vmname,data)
                    for result_type in filename_sfx_list:
                            # print("Result_Type: ",result_type)
                            vmdata_filename =  _temp_out + "/" + vmname + result_type
                            vals = parse_and_set_result(vmdata_filename)
                            if vals==0:
                                vals =[0]
                            all_vals.extend(vals)

                            # print(vals)

                    out_all.values = all_vals
                    collectd.info('dipatching for: ' +str(out_all.plugin_instance) +": "+ str(out_all.values))
                    out_all.dispatch()

collectd.register_config(configure)
collectd.register_init(init)
collectd.register_read(reader)
collectd.register_shutdown(shutdown)

