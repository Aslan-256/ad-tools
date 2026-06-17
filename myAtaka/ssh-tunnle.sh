#!/bin/bash

#Da eseguire in locale per creare un tunnel ssh verso il server remoto, in modo da poter accedere ai servizi che girano su quel server come se fossero in locale.
SSH_USER="team"
SSH_HOST_VPS="46.225.151.253"

#ssh -N -L 8000:localhost:8000 \
#      -L 8080:localhost:8080 \
#      $SSH_USER@$SSH_HOST_VPS

#Ataka port
ssh -N -L 8000:localhost:8000 \
       -L 5432:localhost:5432 \
       -L 5672:localhost:5672 \
       -L 8080:localhost:8080 \
       -L 3000:localhost:3000 \
       $SSH_USER@$SSH_HOST_VPS

#firegex proxy
#VULNBOX_IP=""
#VULNBOX_USER=""
#ssh -N -L 4444:localhost:4444 \
#       $VULNBOX_USER@$VULNBOX_IP

