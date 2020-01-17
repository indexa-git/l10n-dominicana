FROM gcr.io/iterativo/dockerdoo:11.0

ENV ODOO_EXTRA_ADDONS /var/lib/odoo/extra-addons

COPY . ${ODOO_EXTRA_ADDONS}

USER root

# Needed library to build requirements on IT-Projects-LLC submodule
RUN set -x; \
    apt-get -qq update && apt-get -qq install -y --no-install-recommends \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
    > /dev/null

RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get -qq update && apt-get -qq install -y google-chrome-stable

RUN sudo chown -R 1000:1000 ${ODOO_EXTRA_ADDONS}

RUN ls -la ${ODOO_EXTRA_ADDONS}

USER 1000

RUN pip3 install --user websocket-client

RUN find ${ODOO_EXTRA_ADDONS} -name 'requirements.txt' -exec pip3 install --user -r {} \;
