from tensorhive.core.monitors.MonitoringBehaviour import MonitoringBehaviour
from tensorhive.core.utils.decorators.override import override
from typing import Dict, List
from tensorhive.core.utils.NvidiaSmiParser import NvidiaSmiParser
from pssh.exceptions import Timeout, UnknownHostException, ConnectionErrorException, AuthenticationException


class GPUMonitoringBehaviour(MonitoringBehaviour):
    _base_command = 'nvidia-smi --query-gpu='
    _format_options = '--format=csv'
    _available_commands = [
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

    @property
    def available_commands(self) -> List:
        return self._available_commands

    def _execute_all_commands(self, group_connection) -> Dict:
        '''
        Merges all commands into a single nvidia-smi query 
        and executes them on all hosts within connection group
        '''
        # Example:nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,utilization.memory --format=csv
        query = ','.join(self.available_commands)
        command = '{base_command}{query} {format_options}'.format(
            base_command=self._base_command, query=query, format_options=self._format_options
        )  # type: str

        # stop_on_errors=False means that single host failure does not raise an exception
        # it only it to the output
        output = group_connection.run_command(command, stop_on_errors=False)
        group_connection.join(output)
        return output

    def _format_result(self, data: Dict) -> Dict:
        '''
        Creates a dictionary of results, based on hosts' outputs
        Keys = hosts
        Values = (result on success) or (exit code on failure) or (exception name on failure)
        '''
        formatted_data = {}
        for host, host_out in data.items():
            if host_out.exit_code is 0:
                '''Command executed successfully'''
                gpus_info = NvidiaSmiParser.gpus_info_from_stdout(
                    host_out.stdout
                )
                formatted_data[host] = gpus_info
            else:
                '''Command execution failed'''
                if host_out.exit_code:
                    message = {
                        'exit_code': host_out.exit_code
                    }
                elif host_out.exception:
                    message = {
                        'exception': host_out.exception.__class__.__name__
                    }
                # TODO Make sure there are no other possibilities than exit_code/exception
                else:
                    message = 'Unknown failure'
                formatted_data[host] = message
        return formatted_data

    @override
    def update(self, group_connection) -> Dict:
        output = self._execute_all_commands(group_connection)  # type: Dict
        result = self._format_result(output)  # type: Dict
        return result