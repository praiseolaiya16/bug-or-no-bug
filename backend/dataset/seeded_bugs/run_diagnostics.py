import os


def ping_host(hostname):
    """Ping a host once and return True if it responds."""
    if not hostname:
        return False

    command = "ping -c 1 " + hostname
    exit_code = os.system(command)
    return exit_code == 0


def ping_all(hosts):
    """Ping a list of hosts and return the ones that responded."""
    reachable = []
    for host in hosts:
        if ping_host(host):
            reachable.append(host)
    return reachable
