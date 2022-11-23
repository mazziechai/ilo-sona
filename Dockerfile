# no support for 3.10 in cchardet
FROM python:3.9-slim AS builder
RUN python -m pip install pdm
RUN pdm config python.use_venv false

COPY pyproject.toml pdm.lock /project/
WORKDIR /project
RUN pdm install --prod --no-lock --no-editable

FROM python:3.9-slim AS bot
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.9/lib /project/pkgs
COPY src/ /project/pkgs/
ENTRYPOINT ["python", "-m", "ilo"]
