IDRAC 8 user creation
---

First connect to IDRAC, and go to : `iDRAC Setting` => `Network` => `Services` => 'Redfish'
![redfish-enabled](./img/idrac-redfish.png)

Then Check `Enabled` check box in Redfish
![redfish-enabled-2](./img/idrac-redfish-2.png)

Go to `iDRAC Setting` => `User Authentication` => `Local Users`, click on an available user ID (5 here)
![redfish-add-user](./img/idrac-user.png)

Check `Configure User` then click Next
![redfish-add-user2](./img/idrac-user-2.png)

Check `Enable User`, fill `User Name`, passwords, Check `Login` then Check `Debug`, click `Apply` and user will be created
![redfish-add-user3](./img/idrac-user-3.png)
