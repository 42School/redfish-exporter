IDRAC8_REDFISH_BASE_URL = '/redfish/v1'
RAID_CTRL_URL = "/Systems/System.Embedded.1/Storage/Controllers"

class Raid(object):
    def __init__(self, conn):
        self._conn = conn

    """ list and parse controllers """
    def _list(self):
        ret = self._conn.get(RAID_CTRL_URL)
        try:
            raid_ctrl = list()

            """ parse raid controller name """
            for member in ret['Members']:

                raid_ctrl_url = member['@odata.id']
                raid_ctrl.append(raid_ctrl_url.replace(IDRAC8_REDFISH_BASE_URL + RAID_CTRL_URL + '/', ''))

        except KeyError as e:
            raise "Invalid dict key from redfish response: " + e

        return raid_ctrl

    """ """
    def get_raid_metrics(self):

        raids_ctrl = {}
        metrics = {}
        metrics['raid_controller'] = dict()
        metrics['disk'] = dict()

        """ list controllers """
        raid_ctrl = self._list()
        for ctrl in raid_ctrl:
            ret = self._get_disks(ctrl)
            metrics['raid_controller'][ctrl] = ret[0]
            metrics['disk'] = { **metrics['disk'], **ret[1] }

        return metrics

    def _get_disks(self, ctrl_name):

        """ get controllers info """
        ctrl_status = self._conn.get(RAID_CTRL_URL + '/' + ctrl_name)

        try:
            ctrl = ctrl_status['Status']
            if ctrl['Health'] and ctrl['State']:
                status = {
                    'health': ctrl['Health'],
                    'state': ctrl['State']
                }
            else:
                status = { 'health': '', 'state': ''}

            disks = {}
            """ get disk list by controller """
            for disk in ctrl_status['Devices']:

                disk_name = disk['Name']
                disk_status = disk['Status']
                disks[disk_name] = {
                    'health': disk_status['Health'],
                    'state': disk_status['State']
                }
        except KeyError as e:
            raise "Invalid dict key from redfish response: " + e

        return [status, disks]
