# redfish-exporter
IDRAC redfish exporter
---

Requirements:
```
Server with IDRAC 8 / 9
Redfish service enabled on IDRAC
IDRAC user configured with specific rights
Prometheus and Pushgateway service protected with nginx by basic auth
Debian 10
Python 3.7
```

### Follow [thoses steps](./IDRAC_USER_CREATION.md) for iDRAC user creation

### Installation
Go into prometheus VM
Clone project in `/var/lib/` directory:
```
cd /var/lib
git clone https://github.com/42School/redfish_exporter
```

Create user for running exporter (or take existing `node-exp`):
```
useradd my_new_user -s /sbin/nologin
```

Give new directory specific rights for particular user (`node-exp` or previous created)
```
chown node-exp:node-exp -R redfish-exporter
```

Copy `config.yaml.sample` and create a custom config file:
```
cp config.yaml.sample config.yaml
```

Add your iDRAC configuration (ip, protocol, https verification, version, username, password)

Install debian package for python virtualenv
```
sudo apt install python3-virtualenv
```

Create virtualenv and install dependencies:
```
python3.7 -m venv venv
source venv/bin/activate
python setup.py install
```

Run the exporter to make sure everything's good:
```
python -m redfish_exporter --config ./config.yaml \
			   --port 9091 \
			   --ip 127.0.0.1 \
			   --user pushgateway \
			   --password <pushgateway-basic-password>
```

Copy systemd file in right place:
```
sudo cp redfish_exporter.service /etc/system/systemd/
```

Enable and start service:
```
sudo systemct enable redfish_exporter
sudo systemct start redfish_exporter
```

Check status, ensure everything's good:
```
systemctl status redfish_exporter
```

You can import grafana dashboard from [this one](https://grafana.com/grafana/dashboards/12403)

Common problems:
- Bad project ownership
- Invalid project path
