from pyroute2 import IPRoute

def monitor_simple():
    with IPRoute() as ip:
        ip.bind()
        print("Suscrito a eventos de red. Cambia algo en tu configuración...")

        while True:
            for msg in ip.get():
                evento = msg.get('event')
                
                index = msg.get('index')
                attrs = dict(msg.get('attrs', []))
                ifname = attrs.get('IFLA_IFNAME') or f"índice {index}"

                if isinstance(ifname, str) and ifname.startswith(('lo', 'docker', 'veth')):
                    continue

                print(f"🔔 EVENTO: {evento} | INTERFAZ: {ifname}")

                print(msg)

if __name__ == '__main__':
    try:
        monitor_simple()
    except KeyboardInterrupt:
        print("\nMonitor detenido.")