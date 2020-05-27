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

### Installation
Go into prometheus VM
Clone project in `/var/lib/` directory:
```
cd /var/lib
git clone https://github.com/42School/redfish_exporter
```

Create user for running exporter (or take existing `node-exp`):
```
```

Give new directory specific rights for particular user (`node-exp` or previous created)
```
chown node-exp:node-exp -R redfish_exporter
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
pip install -r requirements.txt
```

Run the exporter to make sure everything's good:
```
python __init__.py	--config ./config.yaml \
			--port 9091 \
			--ip 127.0.0.1 \
			--user pushgateway \
			--password pushgateway-password
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

Common problems:
- Bad project ownership
- Invalid project path
