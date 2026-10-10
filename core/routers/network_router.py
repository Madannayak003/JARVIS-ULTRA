NETWORK = {

    "turn wifi on":{"action":"wifi_on"},

    "turn wifi off":{"action":"wifi_off"},

    "wifi status":{"action":"wifi_status"},

    "show wifi":{"action":"wifi_status"},

    "list wifi":{"action":"wifi_list"},

    "turn bluetooth on":{"action":"bluetooth_on"},

    "turn bluetooth off":{"action":"bluetooth_off"},

    "bluetooth status":{"action":"bluetooth_status"},

    "show bluetooth devices":{"action":"bluetooth_devices"},

    "paired bluetooth devices":{"action":"bluetooth_devices"},

    "open bluetooth settings":{"action":"bluetooth_settings"}

}


def network_route(command):

    if command in NETWORK:

        return [NETWORK[command]]

    return None