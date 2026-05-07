import socket, dns.resolver
from geoip2fast import GeoIP2Fast

geo = GeoIP2Fast()

domain = input('Enter domain: ')
print(f'\n=== DNS Info: {domain} ===')
ip = None

for rtype in ['A', 'MX']:
    try:
        for r in dns.resolver.resolve(domain, rtype):
            print(f'{rtype}: {r}')
            if rtype == 'A' and ip is None:
                ip = str(r)
    except Exception as e:
        print(f'{rtype}: {e}')

if ip:
    try:
        rev, _, _ = socket.gethostbyaddr(ip)
        print(f'Reverse: {ip} → {rev}')
    except socket.herror:
        print(f'Reverse: {ip} → ไม่พบ PTR record') 
        
    match = geo.lookup(ip)
    if match:
        print(f'GeoIP: {match.country_name} ({match.country_code}) '
              f'CIDR: {match.cidr}')