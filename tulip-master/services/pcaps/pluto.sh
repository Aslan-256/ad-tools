while true; do
    rsync -rtzvP -e "ssh -i ~/.ssh/id_ed25519 -q" root@10.60.5.1:/var/log/tcpdump/ /home/ADTools-main/tulip-master/services/pcaps/tcpdump/3000/
    sleep 60
done
