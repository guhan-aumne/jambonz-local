#!/bin/sh
cat <<EOF > /etc/drachtio.conf.xml
<drachtio>
  <admin port="9023" secret="cymru" />
</drachtio>
EOF
exec drachtio -f /etc/drachtio.conf.xml
