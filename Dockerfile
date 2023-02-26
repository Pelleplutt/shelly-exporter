FROM python:3.11.0

RUN addgroup prometheus
RUN adduser --disabled-password --no-create-home --home /app  --gecos '' --ingroup prometheus prometheus

COPY requirements.txt /app/
RUN /usr/local/bin/pip install -r /app/requirements.txt

COPY shelly-exporter.py /app/
COPY shelly/* /app/shelly/

EXPOSE 9109

USER prometheus

CMD ["/usr/local/bin/python",  "/app/shelly-exporter.py"]
