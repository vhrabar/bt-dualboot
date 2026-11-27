ARG ARG_PYTHON_VERSION
FROM python:$ARG_PYTHON_VERSION

COPY ./docker /docker/
ARG ARG_UID ARG_USER
RUN /docker/add-user $ARG_UID $ARG_USER \
  && apt install -y chntpw

USER $ARG_USER

# NOTE: overwrite: the default .bashrc returns early for non-interactive shells
RUN echo 'PATH=/usr/sbin:$PATH' > /home/$ARG_USER/.bashrc

# pre-build dependencies
COPY ./dev/bootstrap ./pyproject.toml ./uv.lock   /src/
RUN /docker/prebuild-dependencies $ARG_USER /src
