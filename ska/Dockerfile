FROM nexus.engageska-portugal.pt/ska-docker/ska-python-buildenv:latest AS buildenv
FROM nexus.engageska-portugal.pt/ska-docker/ska-python-runtime:latest AS runtime

EXPOSE 5004
ENV PYTHONUNBUFFERED 1
ENV PYTANGO_GREEN_MODE asyncio

CMD ["/venv/bin/python3", "-m", "tangogql"]
