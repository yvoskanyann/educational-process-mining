import pandas as pd
import os

# PM4Py imports
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.conformance.alignments.petri_net import algorithm as align_algo
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.petri_net import visualizer as pn_vis
from pm4py.objects.conversion.process_tree import converter as pt_converter


def load_event_log(csv_path="big_synthetic_event_log.csv"):
    """
    Loads the event log from a CSV into a pandas DataFrame,
    then converts it to a PM4Py EventLog object.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Could not find event log file: {csv_path}")

    df = pd.read_csv(csv_path)
    # Convert timestamp to datetime type if not already
    df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
    # Sort by case ID and time just in case
    df = df.sort_values(["case:concept:name", "time:timestamp"])

    # Convert DataFrame to an EventLog
    df = dataframe_utils.convert_timestamp_columns_in_df(df)
    log = log_converter.apply(df, parameters={
        "case_id_key": "case:concept:name",
        "activity_key": "concept:name",
        "timestamp_key": "time:timestamp"
    })
    return df, log


def discover_petri_net(log):
    """
    Discovers a Petri net using the Inductive Miner algorithm
    from the provided event log.
    Returns (net, initial_marking, final_marking).
    """
    # Obtain a ProcessTree from the log using the Inductive Miner
    process_tree = inductive_miner.apply(log, variant=inductive_miner.Variants.IM)

    # Convert the ProcessTree to a Petri net
    net, im, fm = pt_converter.apply(process_tree)

    return net, im, fm

def visualize_petri_net(net, im, fm, output_file=None):
    """
    Visualizes the Petri net and, if output_file is provided,
    saves it as a .png.
    """
    gviz = pn_visualizer.apply(net, im, fm)
    if output_file:
        pn_visualizer.save(gviz, output_file)
    else:
        pn_visualizer.view(gviz)


def conformance_check(log, net, im, fm):
    """
    Performs alignment-based conformance checking and returns
    alignments plus an average fitness score.
    """
    alignments = align_algo.apply_log(log, net, im, fm)
    fitness_values = [al["fitness"] for al in alignments]
    avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0
    return alignments, avg_fitness


def frequency_overlay(log, net, im, fm, output_file="petri_net_frequency.png"):
    """
    Generates a Petri net image with frequency overlay.
    """
    gviz = pn_vis.apply(
        net, im, fm,
        parameters={"log": log, "variant": pn_vis.Variants.FREQUENCY}
    )
    pn_vis.save(gviz, output_file)


def performance_overlay(log, net, im, fm, output_file="petri_net_performance.png"):
    """
    Generates a Petri net image with performance overlay (time metrics).
    """
    gviz = pn_vis.apply(
        net, im, fm,
        parameters={"log": log, "variant": pn_vis.Variants.PERFORMANCE}
    )
    pn_vis.save(gviz, output_file)


def performance_analysis(df):
    """
    Example performance analysis:
      - Case durations
      - Quiz completion times
    Returns a dictionary with some metrics.
    """
    # Ensure datetime
    df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])

    # 1. Case durations (from first event to last event)
    case_durations = df.groupby("case:concept:name")["time:timestamp"].agg(lambda x: x.max() - x.min())
    avg_duration = case_durations.mean()

    # 2. Quiz completion times (if activity Attempt_Quiz and Submit_Quiz exist)
    quiz_events = df[df["concept:name"].isin(["Attempt_Quiz", "Submit_Quiz"])]
    if not quiz_events.empty:
        quiz_pivot = quiz_events.pivot_table(
            index="case:concept:name",
            columns="concept:name",
            values="time:timestamp",
            aggfunc='first'
        )
        quiz_pivot['quiz_time'] = quiz_pivot["Submit_Quiz"] - quiz_pivot["Attempt_Quiz"]
        avg_quiz_time = quiz_pivot['quiz_time'].mean()
    else:
        avg_quiz_time = None

    analysis_results = {
        "case_durations": case_durations,
        "avg_duration": avg_duration,
        "avg_quiz_time": avg_quiz_time
    }
    return analysis_results


def generate_suggestions(analysis_results, alignments, threshold=1.0):
    """
    Generate some suggestions based on conformance results and performance metrics.
    threshold=1.0 -> perfect conformance required for no flags.
    """
    # Flag traces that didn't perfectly fit the model
    flagged_cases = []
    for i, alignment in enumerate(alignments):
        trace_fitness = alignment["fitness"]
        case_id = f"Trace_{i}"
        if trace_fitness < threshold:
            flagged_cases.append((case_id, trace_fitness))

    suggestions = []
    if flagged_cases:
        suggestions.append(f"**Deviating Cases** (fitness < {threshold}):")
        for cid, fit in flagged_cases:
            suggestions.append(f"- Case {cid} with fitness {fit:.2f} -> Might have skipped or repeated steps.")

    # Look at average quiz time from performance analysis
    if analysis_results["avg_quiz_time"] is not None:
        quiz_mins = analysis_results["avg_quiz_time"].total_seconds() / 60
        if quiz_mins > 10:
            suggestions.append("Average quiz completion > 10 minutes. Consider splitting the quiz or adding hints.")
        else:
            suggestions.append(f"Quiz completion time is about {quiz_mins:.1f} mins on average. This seems reasonable.")

    avg_duration_mins = analysis_results["avg_duration"].total_seconds() / 60
    if avg_duration_mins > 20:
        suggestions.append("Overall session duration is high. Check if learning content is too long or quiz is difficult.")
    else:
        suggestions.append(f"Overall session duration is about {avg_duration_mins:.1f} mins on average.")

    if not suggestions:
        suggestions.append("No major deviations or bottlenecks found. The process seems well-aligned.")
    return suggestions


def main():
    print("\n--- 1) Load Event Log ---")
    df, log = load_event_log("big_synthetic_event_log.csv")
    print(f"Loaded log: {len(log)} traces, {sum(len(t) for t in log)} total events.\n")

    print("--- 2) Discover Petri Net Using Inductive Miner ---")
    net, im, fm = discover_petri_net(log)
    print("Petri net discovered with transitions:")
    labeled_transitions = [t.label for t in net.transitions if t.label]
    print(labeled_transitions, "\n")

    # Optionally visualize & save
    print("--- Visualize raw Petri net ---")
    visualize_petri_net(net, im, fm, output_file="petri_net_discovered.png")
    print("Raw Petri net saved to 'petri_net_discovered.png'.\n")

    print("--- 3) Conformance Checking (Alignments) ---")
    alignments, avg_fitness = conformance_check(log, net, im, fm)
    print(f"Average fitness: {avg_fitness:.2f}\n")

    # Show first few alignment details
    for i, al in enumerate(alignments[:2]):
        for i, al in enumerate(alignments):
            # Use i as the trace index
            current_trace = log[i]
            case_id = current_trace.attributes.get("concept:name", f"Trace_{i}")

            print(f"Trace {case_id} fitness = {al['fitness']:.2f}")
        print(" Moves on Log:", [m for m in al["alignment"] if m[0] != '>>' and m[1] == '>>'])
        print(" Moves on Model:", [m for m in al["alignment"] if m[0] == '>>' and m[1] != '>>'])
        print()

    print("--- 4) Performance Analysis ---")
    analysis_results = performance_analysis(df)
    print("Case durations:")
    print(analysis_results["case_durations"])
    print(f"\nAverage duration: {analysis_results['avg_duration']}")
    if analysis_results["avg_quiz_time"] is not None:
        print(f"Average quiz time: {analysis_results['avg_quiz_time']}")
    print()

    print("--- Generate Frequency and Performance Overlays ---")
    frequency_overlay(log, net, im, fm, output_file="petri_net_frequency.png")
    performance_overlay(log, net, im, fm, output_file="petri_net_performance.png")
    print("Saved frequency overlay => 'petri_net_frequency.png'")
    print("Saved performance overlay => 'petri_net_performance.png'\n")

    print("--- 5) Suggestions & Insights ---")
    suggestions = generate_suggestions(analysis_results, alignments, threshold=1.0)
    for line in suggestions:
        print(line)

    print("\nDone. Check the generated PNG files and console output for results.")


if __name__ == "__main__":
    main()