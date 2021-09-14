# source: https://monero-python.readthedocs.io/en/latest/wallet.html
# source: https://github.com/monero-ecosystem/monero-python


# cd to daemon directory (this directory)

# Run this command first
$: ./monerod

# Then this one.
$: ./monero-wallet-rpc --wallet-file wallet --password "MoneroMarket wallet" --rpc-bind-port 28088 --disable-rpc-login --daemon-host node.moneroworld.com:18089










  GNU nano 5.4                                                              /etc/supervisor/conf.d/MoneroMarket.conf                                                                        
[program:moneromarket]
directory=/home/janoher/MoneroMarket
command=/home/janoher/MoneroMarket/virtual/bin/gunicorn -w 9 run:app
user=janoher
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/MoneroMarket/moneromarket.err.log
stdout_logfile=/var/log/MoneroMarket/moneromarket.out.log

[program:monerod]
directory=/home/janoher/MoneroMarket/daemon
command=sudo ./monerod --restricted-rpc --rpc-bind-ip 0.0.0.0 --rpc-bind-port 18081 --confirm-external-bind
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/MoneroMarket/monerod.err.log
stdout_logfile=/var/log/MoneroMarket/monerod.out.log

[program:orders]
directory=/home/janoher/MoneroMarket/sql
command=/home/janoher/MoneroMarket/virtual/bin/python3 orders.py
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/MoneroMarket/orders.err.log
stdout_logfile=/var/log/MoneroMarket/orders.out.log

[program:wallet]
directory=/home/janoher/MoneroMarket/daemon
command=sudo ./monero-wallet-rpc --wallet-file wallet --password "MoneroMarket wallet" --rpc-bind-port 28088 --disable-rpc-login
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/MoneroMarket/wallet.err.log
stdout_logfile=/var/log/MoneroMarket/wallet.out.log











# Source: https://whattheserver.com/how-to-setup-private-monero-remote-full-node/
# Source: https://www.monero.how/how-to-run-monero-node