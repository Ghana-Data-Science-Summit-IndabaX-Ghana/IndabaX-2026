# 04 Bonus: Orchestrating the Pipeline with Apache Airflow

> **Optional capstone.** This is *not* part of the core 3-hour workshop and is not
> needed to finish the notebook or `src/run_pipeline.py`. Run it as an
> instructor-led **demo** if time allows. Do **not** ask a beginner room to install
> Airflow live - it is heavy and will eat your schedule.

## Why this matters

Our `src/run_pipeline.py` is **automation**: one command runs the stages in order.
A production system adds **orchestration** on top:

- **scheduling** - run automatically when a new monthly workbook lands
- **dependencies** - run `clean` only after `reshape` succeeds
- **failure handling** - if `validate` fails, stop and don't publish; retry transient errors
- **lineage** - a visible graph of which inputs and steps produced each output

Airflow gives all of that. And because every stage in `src/` is already a small,
pure function, we **wrap them as tasks** instead of rewriting anything. That is the
lesson: good structure pays off the moment you orchestrate.

## What the DAG does

`dags/agrivoltaics_pipeline.py` defines four tasks that mirror the modules:

```text
reshape  ->  clean  ->  validate  ->  insights
```

Two design choices worth calling out to the room:

1. **Tasks pass file paths, not DataFrames.** Airflow's XCom is for *small* values.
   Each task writes its result to disk (`long.parquet`, `clean.parquet`) and passes
   the next task a path. That is exactly how real pipelines hand off between stages -
   and it gives you materialised, inspectable intermediates.
2. **A failed `validate` task stops everything downstream automatically.** An unknown
   plot code raises -> the task fails -> `insights` never runs -> nothing bad gets
   published. The "stop the pipeline" rule from Module 5, enforced by the scheduler.

## Prerequisites

Airflow supports roughly Python **3.9-3.12**. It will **not** install in a 3.13/3.14
environment, so use a separate interpreter for this bonus.

## Path A - Docker Compose (recommended, one command)

`docker-compose.yaml` runs Airflow in a single container, so you don't need a
separate Python 3.12 environment at all - Docker provides the right interpreter.
From the project root:

```bash
docker compose up            # first run pulls the image + installs deps (~1-2 min)
```

- Open the UI at http://localhost:8080.
- Get the admin login: `docker compose logs airflow | grep -i password`
  (username is `admin`).
- Unpause **agrivoltaics_pipeline**, trigger a run, watch the tasks go green.
- Stop with `docker compose down`.

The compose file mounts this project's `dags/`, `src/`, `data/`, and `outputs/`
into the container and sets `AGRI_PROJECT=/opt/airflow`, so the DAG finds the same
code and data you run locally - results land back in your local `data/processed/`
and `outputs/reports/`. It installs `pandas`/`openpyxl`/`pyarrow` on start (fine
for a demo; bake them into a custom image for real use). Pin a different Airflow
version with `AIRFLOW_IMAGE_NAME=apache/airflow:3.0.x docker compose up`.

## Path B - local: `airflow standalone` (single process, SQLite)

Best for a quick local demo without Docker. From the project root:

```bash
# 1) A separate Python 3.12 environment (do NOT reuse the 3.14 .venv)
python3.12 -m venv .venv-airflow
source .venv-airflow/bin/activate

# 2) Install Airflow with its constraints file, plus our deps
export AIRFLOW_VERSION=3.0.2
export PY=3.12
pip install "apache-airflow==${AIRFLOW_VERSION}" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PY}.txt"
pip install pandas openpyxl pyarrow

# 3) Point Airflow at THIS project's dags/ and data, hide the examples
export AIRFLOW_HOME="$PWD/.airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AGRI_PROJECT="$PWD"

# 4) Launch (prints a generated admin password; UI at http://localhost:8080)
airflow standalone
```

Open http://localhost:8080, find **agrivoltaics_pipeline**, unpause it, and trigger
a run.

## Path C - reproducible: Astro CLI (Docker, Postgres + LocalExecutor)

Best if you want a clean, shareable container setup. Install the
[Astro CLI](https://www.astronomer.io/docs/astro/cli/install-cli), then:

```bash
mkdir airflow-demo && cd airflow-demo
astro dev init
# copy our DAG and source into the Astro project:
cp "../dags/agrivoltaics_pipeline.py" dags/
cp -r ../src ../data ../outputs include/        # then set AGRI_PROJECT=/usr/local/airflow/include
echo -e "pandas\nopenpyxl\npyarrow" >> requirements.txt
astro dev start          # UI at http://localhost:8080
```

(With Astro, set `AGRI_PROJECT` to wherever you mounted `src/`, `data/`, and
`outputs/` - e.g. `include/` becomes `/usr/local/airflow/include`.)

## What to point out in the demo (2-3 minutes)

1. **Graph view** - the four tasks and their arrows. "This picture *is* the lineage."
2. **Trigger a run** - watch tasks turn green left to right.
3. **Break it on purpose** - temporarily map a plot to an unknown prefix, or tighten a
   range so `validate` fails. Show that `validate` goes red and **`insights` never
   runs** - no bad output is published.
4. **Schedule** - the DAG is `@monthly`, matching the cadence of a new workbook. Mention
   `catchup=False` so it doesn't backfill every past month on first run.
5. **Outputs** - the same `data/processed/*.csv` and `outputs/reports/validation_report.csv`
   the script produces, now produced by orchestrated tasks.

## Caveats to mention honestly

- Airflow is **heavy**: a scheduler, a metadata database, and a web server. Overkill for
  five files on a laptop - we use it to *learn the shape* of production orchestration.
- **XCom is not for big data.** That is why tasks pass parquet paths, not DataFrames.
- If you want the same idea with far less weight, look at **Prefect** or **Dagster**
  (Dagster's "asset" model maps neatly onto "each output is an asset").

## Files

- `docker-compose.yaml` - one-command Airflow demo (Path A)
- `dags/agrivoltaics_pipeline.py` - the DAG (wraps the real `src/` functions)
- `requirements-airflow.txt` - Airflow + deps, for a separate 3.12 environment (Path B)
