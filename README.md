# redfish-exporter
IDRAC redfish exporter

Copy `config.yaml.sample` and create a custom config file:
```
cp config.yaml.sample config.yaml
```

Add your iDRAC ip and credentials

Then run the exporter:
```
python app.py start -i 127.0.0.1 -p 9111 -f config.yaml
```
