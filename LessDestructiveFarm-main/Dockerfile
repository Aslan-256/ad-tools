FROM node:16 
#esempio: FROM python:3.14-slim

WORKDIR /usr/src/app
# COPY requirements.txt ./  that inlcudes the dependencies for the project, and install them
# RUN pip install --upgrade pip && pip install -r requirements.txt
#buona abitudine mettere tutti i run all'inizio del dockerfile, in questo modo si evita di dover ricostruire l'immagine ogni volta che si modifica un file, e si sfrutta la cache di docker per velocizzare la build
#soprattutto, cercare di scrivere il minor numero di righe possibile, in questo modo si riduce il numero di layer dell'immagine e si velocizza la build

#COPY . .  #copia tutto il contenuto della cartella corrente (dove si trova il Dockerfile) nella cartella /usr/src/app dell'immagine, ma è meglio evitare di copiare tutto, soprattutto se ci sono file che non servono per l'applicazione, come ad esempio i file di configurazione di git, o i file di log, o i file di test, ecc... quindi è meglio copiare solo i file necessari per l'applicazione, come ad esempio il package.json e il package-lock.json, e poi installare le dipendenze, e poi copiare il resto dei file, in questo modo si sfrutta la cache di docker per velocizzare la build
ADD ./package.json .
ADD ./package-lock.json .

RUN npm i
RUN npx next telemetry disable

ADD . .
RUN npm run build

ENV NODE_ENV production
RUN npm prune --production

EXPOSE 3001
#expose serve per indicare a docker che l'applicazione ascolta sulla porta 3000, in questo modo quando si esegue il container, si può mappare la porta 3000 del container alla porta 3000 del host, in questo modo si può accedere all'applicazione tramite http://localhost:3000

CMD [ "npm", "start" ]
