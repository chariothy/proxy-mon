# For githook project
# @version 1.0

FROM python:3.9
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


CMD [ "python", "main.py" ]