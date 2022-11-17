# Huawei LTE/5G Router SMS to PushOver Notifications

This python script will read your text messages from Huawei router with HiLink then forward it to PushOver push notification. It's forked from [chenwei791129/Huawei-LTE-Router-SMS-to-E-mail-Sender](https://github.com/chenwei791129/Huawei-LTE-Router-SMS-to-E-mail-Sender) but with some changes:
- Instead of sending email, it will send a push notification using PushOver. PushOver is working fine on my Android Pixel, iPhone SE, and iPads
- Making sure that PushOver have received the notification before marking the SMS as read, by reading the HTTP response
- Hopefully it will also keep the SMS message unread if Internet connection is down, but I haven't tested that yet
- It should be executed periodically with cronjobs. In my case I'm running it every 20 seconds in a Raspberry Pi



Tested on:
* Huawei H112-372
* Huawei H112-370
* Huawei E3372
* Huawei E5573Cs-322
* Huawei E5373s-155
* Huawei E8372*
* Raspberry Pi 4 Bullseye 64-bit

If you have successfully run it on other Huawei routers, let me know to add it to the list.

(*) You have to wait for several minute before the script successfuly works on E8372.

## Operational content

1. Find an unread SMS
2. Send the SMS content via Pushover notification
3. Set this SMS as "read"


## How to use

1. copy .env.example to .env
```console
$ cp .env.example .env
$ nano .env
```

2. just run it!
```console
$ python3 check-sms.py
```

3. To periodically run it via crontab. I've set it to run to every minute
```console
$ sudo chmod u+x check-sms.sh
```

Then add at the end for every minute execution:
```console
* * * * * /PATH/Huawei-LTE-Router-SMS-to-PushOver/check-sms.sh
```
or check every 10 seconds:
```console
* * * * * ( /PATH/check-sms.sh )  
* * * * * ( sleep 20 ; /PATH/check-sms.sh )  
* * * * * ( sleep 40 ; /PATH/check-sms.sh )  
```
Don't forget to change PATH.

### Necessary Environment Variables
* `HUAWEI_ROUTER_PASSWORD` Huawei router login password (example: 123456). Leave empty if none
* `PUSHOVER_TOKEN` API Token you get when creating a new application in PushOver.net
* `PUSHOVER_USER` Your user key from PushOver

### Option Environment Variables
* `HUAWEI_ROUTER_IP_ADDRESS` Huawei router IP address (default: 192.168.8.1)
* `HUAWEI_ROUTER_ACCOUNT` Huawei router login account (default: admin)
* `ROUTER_NAME` Router name you will see as part of the forwarded message. It'll help distinguish your routers if you have multiple routers.
* `LOCALE` Set lang (default: en_US, support en_US, zh_TW, zh_HK, zh_CN)


## Related Projects

- [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) (used for non-docker environment)
- [Salamek/huawei-lte-api](https://github.com/Salamek/huawei-lte-api)

## License

The python script is open-sourced software licensed under the [MIT license](https://opensource.org/licenses/MIT).



