import logging
import sushy

class systemScrape:
    def __init__(self, scrape_ip, username, password):
        self._conn = None
        self._username = username
        self._password = password
        self._scrape_ip = scrape_ip
        self._get_conn()

    def _get_conn(self):
        self._conn = sushy.Sushy(
                'https://' + self._scrape_ip + '/redfish/v1',
                username=self._username,
                password=self._password,
                verify=False)

    def get_processor(self):
        # Instantiate a SystemCollection object
        sys_col = self._conn.get_system_collection()

        # Instantiate a system object
        sys_inst = sys_col.get_member(sys_col.members_identities[0])
        sys_col.refresh()

        # Get the memory summary
        print(sys_inst.memory_summary)
        
        # Get the processor summary
        print(sys_inst.processors.summary)
