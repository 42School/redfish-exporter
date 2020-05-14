# redfish-exporter
IDRAC redfish exporter

Copy `config.yaml.sample` and create a custom config file:
```
cp config.yaml.sample config.yaml
```

Add your iDRAC ip and credentials

Then run the exporter:
```
gunicorn -b 127.0.0.1:9111 --reload redfish_exporter:app_dispatch
```
