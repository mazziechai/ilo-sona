# no support for 3.10 in cchardet
FROM python:3.9-slim AS pybuilder
RUN python -m pip --no-cache-dir install pdm
RUN pdm config python.use_venv false

COPY pyproject.toml pdm.lock /project/
COPY src/ /project/src/
WORKDIR /project
RUN pdm install --prod

FROM python:3.9-slim
ENV PYTHONPATH=/project/pkgs
COPY --from=pybuilder /project/__pypackages__/3.9/lib /project/pkgs
COPY src/ /project/src/

ENTRYPOINT ["python", "/project/src/ilo/__main__.py"]
