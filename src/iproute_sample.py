from pyroute2 import IPRoute

def monitor_simple():
    # Nos conectamos al kernel
    with IPRoute() as ip:
        # Escuchamos cambios de enlaces, IPs y rutas
        ip.bind()
        print("Suscrito a eventos de red. Cambia algo en tu configuración...")

        while True:
            # Esta línea se bloquea y no consume CPU hasta que llega un evento
            for msg in ip.get():
                # Obtenemos el tipo de evento (ej: RTM_NEWADDR, RTM_NEWLINK)
                evento = msg.get('event')
                
                # Buscamos el nombre de la interfaz dentro de los atributos del mensaje
                index = msg.get('index')
                attrs = dict(msg.get('attrs', []))
                ifname = attrs.get('IFLA_IFNAME') or f"índice {index}"

                # Filtramos para no ver ruido de interfaces virtuales
                if isinstance(ifname, str) and ifname.startswith(('lo', 'docker', 'veth')):
                    continue

                print(f"🔔 EVENTO: {evento} | INTERFAZ: {ifname}")
                
                # Si quieres ver todo lo que el kernel envía (es mucho), descomenta esto:
                print(msg) 

if __name__ == '__main__':
    try:
        monitor_simple()
    except KeyboardInterrupt:
        print("\nMonitor detenido.")