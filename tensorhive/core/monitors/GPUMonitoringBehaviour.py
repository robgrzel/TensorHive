from tensorhive.core.monitors.MonitoringBehaviour import MonitoringBehaviour
from tensorhive.core.utils.decorators.override import override
from typing import Dict, List
from tensorhive.core.utils.NvidiaSmiParser import NvidiaSmiParser
from pssh.exceptions import Timeout, UnknownHostException, ConnectionErrorException, AuthenticationException


class GPUMonitoringBehaviour(MonitoringBehaviour):
    _base_command = 'nvidia-smi --query-gpu='
    _format_options = '--format=csv,nounits'
    _available_queries = [
        'name',
        'uuid',
        'fan.speed',
        'memory.free',
        'memory.used',
        'memory.total',
        'utilization.gpu',
        'utilization.memory',
        'temperature.gpu',
        'power.draw'
    ]

    @override
    def update(self, group_connection) -> Dict:
        metrics = self._current_metrics(group_connection)  # type: Dict
        processes = self._current_processes(group_connection)  # type: Dict
        
        #Mock 
        metrics = {
            "DGX_STATION_HOST_MOCK": {
                # DGX Station Mock
                "GPU": [
                    {"name": "Tesla V100 GPU0"},
                    {"name": "Tesla V100 GPU1"},
                    {"name": "Tesla V100 GPU2"},
                    {"name": "Tesla V100 GPU3"}
                ]
            },
            "GALILEO_MOCK": {
                "GPU": [
                    {"name": "TITAN X 12 GB"},
                    {"name": "GeForce GTX 750 Ti"}
                ]
            }
        }


        #Mock
        processes = {
            'DGX_STATION_HOST_MOCK': {
                'GPU': {
                    'processes': [
                        {'gpu': 0, 'pid': 1,'command': 'DGX_COMMAND_A'},
                        {'gpu': 0, 'pid': 2,'command': 'DGX_COMMAND_B_'},
                        {'gpu': 0, 'pid': 3,'command': 'DGX_COMMAND_C'},

                        {'gpu': 1, 'pid': 11,'command': 'DGX_COMMAND_D'},
                        {'gpu': 1, 'pid': 12,'command': 'DGX_COMMAND_E'},
                        {'gpu': 1, 'pid': 13,'command': 'DGX_COMMAND_F'},

                        {'gpu': 2, 'pid': 111,'command': 'DGX_COMMAND_G'},
                        {'gpu': 2, 'pid': 112,'command': 'DGX_COMMAND_H'},
                        {'gpu': 2, 'pid': 113,'command': 'DGX_COMMAND_I'},

                        {'gpu': 3, 'pid': 1111,'command': 'DGX_COMMAND_J'},
                        {'gpu': 3, 'pid': 1112,'command': 'DGX_COMMAND_K'},
                        {'gpu': 3, 'pid': 1113,'command': 'DGX_COMMAND_L'},
                    ]    
                }
            },
            'GALILEO_MOCK': {
                'GPU': {
                    'processes': [
                        {'gpu': 0, 'pid': 2221,'command': 'GALILEO_COMMAND_A'},
                        {'gpu': 0, 'pid': 2222,'command': 'GALILEO_COMMAND_B'},
                        # No processes on gpu 1
                    ]    
                }
            }
        }
        result = self._combine_outputs(metrics, processes)  # type: Dict
        return result

    @property
    def available_queries(self) -> List:
        return self._available_queries

    def _current_metrics(self, group_connection) -> Dict:
        '''
        Merges all commands into a single nvidia-smi query 
        and executes them on all hosts within connection group
        '''

        # Example: nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,utilization.memory --format=csv
        query = ','.join(self.available_queries)
        command = '{base_command}{query} {format_options}'.format(
            base_command=self._base_command, query=query, format_options=self._format_options
        )  # type: str

        # stop_on_errors=False means that single host failure does not raise an exception,
        # instead simply adds them to the output.
        output = group_connection.run_command(command, stop_on_errors=False)
        group_connection.join(output)

        for host, host_out in output.items():
            if host_out.exit_code is 0:
                '''Command executed successfully'''
                metrics = NvidiaSmiParser.gpus_info_from_stdout(
                    host_out.stdout)
            else:
                '''Command execution failed'''
                if host_out.exit_code:
                    message = {'exit_code': host_out.exit_code}
                elif host_out.exception:
                    message = {
                        'exception': host_out.exception.__class__.__name__}
                else:
                    message = 'Unknown failure'
                # May want to assign None
                metrics = message
        result = {
            host: {
                'GPU': metrics
            }
        }
        return result

    def _get_process_owner(self, pid: int, hostname: str, group_connection) -> str:
        '''Use single-host connection to acquire process owner'''
        # TODO Move common to SSHConnectionManager
        connection = group_connection.host_clients[hostname]
        command = 'ps --no-headers -o user {}'.format(pid)

        output = connection.run_command(command)
        channel, hostname, stdout, stderr, _ = output

        result = list(stdout)
        if not result:
            # Empty output -> Process with such pid does not exist
            return None
        # Extract owner from list ['example_owner']
        return result[0]

    def _current_processes(self, group_connection) -> Dict:
        '''
        Fetches the information about all active gpu processes using nvidia-smi pmon

        Example result:
        {
            'example_host_0': {
                'GPU': {
                    'processes': [
                        {
                            'gpu': 0, 
                            'pid': 1958, 
                            'type': 'G', 
                            'sm': 0, 
                            'mem': 3, 
                            'enc': 0, 
                            'dec': 0, 
                            'command': 'X'
                        }
                    ]    
                }
            }
        }
        '''
        command = 'nvidia-smi pmon --count 1'
        output = group_connection.run_command(command, stop_on_errors=False)
        group_connection.join(output)

        for host, host_out in output.items():
            if host_out.exit_code is 0:
                processes = NvidiaSmiParser.parse_pmon(host_out.stdout)

                # Find each process owner
                for process in processes:
                    process['owner'] = self._get_process_owner(
                        process['pid'], host, group_connection)
            else:
                # Not Supported
                processes = []
        result = {
            host: {
                'GPU': {
                    'processes': processes
                }
            }
        }
        return result

    def _combine_outputs(self, metrics: Dict, processes: Dict) -> Dict:
        '''
        Merges dicts from 
        > nvidia-smi --query
        > nvidia-smi pmon

        Example result:
        {
            "example_host_0": {
                "GPU": [
                {
                    "name": "GeForce GTX 1060 6GB",
                    "uuid": "GPU-56a30ac8-fcac-f019-fb0a-1e2ffcd58a6a",
                    "fan.speed [%]": 76,
                    ...
                    "processes": [
                        {
                            "gpu": 0,
                            "pid": 1992,
                            ...
                            "command": "X",
                            "owner": "root"
                        },
                        {
                            "gpu": 0,
                            "pid": 22170,
                            ...
                            "command": "python3",
                            "owner": "143344sm"
                        }
                    ]
                }
                ]
            }
        }
        '''
        for hostname, _ in processes.items():
            gpu_processes_on_host = processes[hostname]['GPU']['processes']
                
            for gpu_device_idx, gpu_device in enumerate(metrics[hostname]['GPU']):
                metrics[hostname]['GPU'][gpu_device_idx]['processes'] = []    
            
            for process in gpu_processes_on_host:
                # Put 'process' element at particular index in array
                # FIXME Replace with pythonic code :) Author's intentions are unreadable
                metrics[hostname]['GPU'][process['gpu']]['processes'].append(process)
        return metrics
