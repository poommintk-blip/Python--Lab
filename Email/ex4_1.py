import socket

hostname = socket.gethostname()

ip = socket.gethostbyname(hostname)

print(f'Hostname: {hostname}')
print(f'IP: {ip}')
print('---------------------------------------')

for target in ['8.8.8.8', '1.1.1.1']:
    try:
        name, _, _ = socket.gethostbyaddr(target)
        print(f'{target} → {name}')
    except socket.herror as e:
        print(f'{target} → Error: {e}')