!#/bin/bash

apt update && apt upgrade
apt install curl, wget

curl -L https://raw.githubusercontent.com/openobserve/openobserve/main/downloadO2.sh | sh -s o2-enterprise v0.90.3
export ZO_ROOT_USER_EMAIL=user@system
export ZO_ROOT_USER_PASSWORD=supersecretpassword
adduser openobserve
mkdir /opt/openobserve
chown -R openobserve:openobserve /opt/openobserve/
mv openobserve /opt/openobserve/
cp openobserve.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable openobserve
systemctl start openobserve
systemctl status openobserve

wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.153.0/otelcol-contrib_0.153.0_linux_amd64.deb
dpkg -i otelcol-contrib_0.153.0_linux_amd64.deb
cp otelcol-contrib_config.yaml /etc/otelcol-contrib/config.yaml
systemctl start otelcol-contrib
systemctl status otelcol-contrib
