FROM gcr.io/iterativo/dockerdoo:12.0

ENV ODOO_EXTRA_ADDONS /var/lib/odoo/extra-addons

COPY . ${ODOO_EXTRA_ADDONS}

USER root

# Needed library to build requirements on IT-Projects-LLC submodule
RUN set -x; \
    apt-get -qq update && apt-get -qq install -y --no-install-recommends \
    libffi-dev \
    libappindicator1 ibnss3 libnss3-tools libfontconfig1 wget ca-certificates apt-transport-https inotify-tools unzip \
    fonts-liberation libpangocairo-1.0-0 libx11-xcb-dev libxcomposite-dev libxcursor1 libxdamage1 libxi6 libgconf-2-4 libxtst6 libcups2-dev \
    libxss-dev libxrandr-dev libasound2-dev libatk1.0-dev libgtk-3-dev ttf-ancient-fonts chromium-codecs-ffmpeg-extra libappindicator3-1 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
    > /dev/null

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install google-chrome*.deb && \
    rm google-chrome-stable_current_amd64.deb

RUN sudo chown -R 1000:1000 ${ODOO_EXTRA_ADDONS}

RUN ls -la ${ODOO_EXTRA_ADDONS}

USER 1000

RUN find ${ODOO_EXTRA_ADDONS} -name 'requirements.txt' -exec pip3 install --user -r {} \;
