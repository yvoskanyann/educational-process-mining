# Petri Net–Based Educational Process Mining System

This project demonstrates a **Petri net–based educational process mining** workflow using Python and [PM4Py](https://pm4py.fit.fraunhofer.de/). It is suitable as a reference for diploma projects titled *“Design and Implementation of a Petri Net–Based Educational Process Mining System.”*

## Features
1. **Load Event Log** from a CSV file (`event_log_synthetic.csv`).
2. **Process Discovery** using Inductive Miner, yielding a Petri net model.
3. **Conformance Checking** (alignments) to measure how well the log fits the model.
4. **Performance Analysis** to identify durations and potential bottlenecks.
5. **Visualization** of the Petri net with frequency and performance overlays.
6. **Suggestions** based on discovered patterns and deviations.

## Requirements

- Python 3.7+
- [PM4Py](https://pm4py.fit.fraunhofer.de/) (`pm4py==2.7.3`)
- `pandas==1.5.3`
- `graphviz==0.20.1`

You can install these using:

```bash
pip install -r requirements.txt