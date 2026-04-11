# Methodology

## Overview

Our workflow begins with data ingestion and cleaning, followed by text preprocessing, representation building, and retrieval. Module descriptions and job advertisements are first normalised so that formatting noise does not dominate the comparison. We then build searchable representations that allow us to retrieve modules from jobs and jobs from modules through a shared text-based pipeline.

## Pipeline

The current implementation consists of a Python retrieval layer and a browser-based chat interface. The retrieval layer is responsible for indexing and search, while the web interface allows users to explore module-job matches interactively. This separation helps us keep the core retrieval logic auditable while making the outputs easier to inspect.

## Example Evaluation Dimensions

| Dimension | Description |
| --- | --- |
| Relevance | Whether the retrieved module or job is meaningfully related to the query |
| Coverage | Whether important skills or concepts are represented in the results |
| Interpretability | Whether the match can be explained using understandable text evidence |

## Notes For Final Report

When you expand this section, you will likely want to add one pipeline diagram, one preprocessing table, and a short explanation of your retrieval or ranking approach. If you later run multiple baselines, this section should also justify why the chosen method is appropriate for the task.
