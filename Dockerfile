FROM gcr.io/iterativo/dockerdoo:12.0

ENV ODOO_EXTRA_ADDONS /var/lib/odoo/extra-addons

COPY . ${ODOO_EXTRA_ADDONS}

USER root

# Needed library to build requirements on IT-Projects-LLC submodule
RUN set -x; \
    apt-get -qq update && apt-get -qq install -y --no-install-recommends \
    libffi-dev \
    > /dev/null

RUN sudo chown -R 1000:1000 ${ODOO_EXTRA_ADDONS}

RUN ls -la ${ODOO_EXTRA_ADDONS}

USER 1000

RUN find ${ODOO_EXTRA_ADDONS} -name 'requirements.txt' -exec pip3 install --user -r {} \;
