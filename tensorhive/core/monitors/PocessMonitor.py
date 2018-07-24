from tensorhive.core.monitors.Monitor import Monitor
from tensorhive.core.utils.decorators.override import override
from typing import Dict, List
from tensorhive.core.utils.NvidiaSmiParser import NvidiaSmiParser


class ProcessMonitor(Monitor):
    base_command: str = 'pgrep -f'
    _available_resources: List = [
        'name',
        'uuid'
    ]
    #TODO
    _process_names: List = [
        'TODO',
    ]

    @property
    def available_commands(self) -> List:
        return self._available_commands

    @property
    def process_names(self) -> List:
        return self._process_names

    @property
    def name(self) -> str:
        return 'Process'

    @property
    def gathered_data(self) -> Dict:
        '''Getter for the protected, inherited variable'''
        return self._gathered_data

    @gathered_data.setter
    def gathered_data(self, new_value) -> None:
        '''Setter for the protected, inherited variable'''
        self._gathered_data = new_value


    @override
    def update(self, connection_group):
        query = ' '.join(self.process_names)
        command = '{base_command}{query} '.format(
            base_command=self._base_command, query=query
        )
        output = connection_group.run_command(command)

        connection_group.join(output)

        for host, host_out in output.items():
            if host_out.exit_code is 0:
                process_info = host_out.stdout
                self.gathered_data[host] = process_info
            else:
                self.gathered_data[host] = []
