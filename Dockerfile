FROM  gcr.io/iterativo/dockerdoo:17.0
ENV ODOO_EXTRA_ADDONS /mnt/extra-addons
USER root
RUN sudo mkdir -p ${ODOO_EXTRA_ADDONS}
COPY . ${ODOO_EXTRA_ADDONS}
RUN apt-get -qq update && apt-get -qq install -y --no-install-recommends build-essential \
    && find ${ODOO_EXTRA_ADDONS} -name 'requirements.txt' -exec pip3 --progress-bar off --no-cache-dir install -r {} \; \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*
RUN sudo chown -R 1000:1000 ${ODOO_EXTRA_ADDONS}
USER 1000