# For githook project
# @version 1.0

FROM chariothy/pydata:3.10
LABEL maintainer="chariothy@gmail.com"

ENV PROXY_MON_MAIL_FROM="Henry TIAN <chariothy@gmail.com>"
ENV PROXY_MON_MAIL_TO="Henry TIAN <chariothy@gmail.com>"

ENV PROXY_MON_SMTP_HOST=smtp.gmail.com
ENV PROXY_MON_SMTP_PORT=25
ENV PROXY_MON_SMTP_USER=chariothy@gmail.com
ENV PROXY_MON_SMTP_PWD=password

WORKDIR /app
COPY ./requirements.txt .
#COPY ./dl_v2ray.py .
#COPY ./utils.py .

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
  && echo 'Asia/Shanghai' > /etc/timezone \
  && apt-get update \
	#&& apt-get install -y --no-install-recommends shadowsocks-libev \
  && apt-get autoclean \
  && rm -rf /var/lib/apt/lists/* \
  && pip install -U pip \
  && pip install --no-cache-dir -r ./requirements.txt
  #&& python /app/dl_v2ray.py

ARG UNAME=henry
ARG UID=1000
ARG GID=1000

RUN groupadd -g $GID -o $UNAME \
  && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME \
  && usermod -G root $UNAME
  
USER $UNAME

CMD [ "python", "main.py" ]