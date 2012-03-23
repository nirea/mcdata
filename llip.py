from ipaddr import IPAddress, IPNetwork

ll_ranges = (
    "8.2.32.0/22",
    "8.4.128.0/22",
    "8.10.144.0/21",
    "63.210.156.0/22",
    "64.129.40.0/21",
    "64.154.220.0/22",
    "66.150.244.0/23",
    "69.25.104.0/23",
    "72.5.12.0/22",
    "216.82.0.0/18"
    )

# Instantiate classes once instead of on each call.
ll_ranges = [IPNetwork(r) for r in ll_ranges]

def lindenip(addr):
    #True if address is in one of LL's IP ll_ranges, else False
    ip = IPAddress(addr)
    return any([ip in r for r in ll_ranges])


