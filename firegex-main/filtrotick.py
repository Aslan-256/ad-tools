from firegex.nfproxy import pyfilter, ACCEPT, DROP
from firegex.nfproxy.models import RawPacket

# Inizializziamo il contatore globale per questa connessione
# Questa parte viene eseguita una sola volta all'inizio della connessione TCP
pkt_count = 0

@pyfilter
def drop_third_long_packet(packet: RawPacket):
    global pkt_count
    
    # Incrementiamo il contatore ogni volta che arriva un pacchetto
    pkt_count += 1
    
    # Controlliamo se è il terzo pacchetto (pkt_count == 3)
    if pkt_count == 3:
        # Verifichiamo la lunghezza del payload (l4_size)
        if packet.l4_size > 17:
            print(f"[!] Dropping 3rd packet: size {packet.l4_size} > 17")
            return DROP
            
    return ACCEPT
