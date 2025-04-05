import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_synthetic_log(num_cases=500):
    # Define base activities and typical order
    activities = ["Login", "View_Content", "Attempt_Quiz", "Submit_Quiz", "Logout"]

    # Prepare list for events
    events = []
    base_date = datetime(2025, 4, 1, 8, 0, 0)

    for case_id in range(1, num_cases + 1):
        current_time = base_date + timedelta(minutes=np.random.randint(0, 600))
        # Always start with Login
        events.append({
            "case:concept:name": case_id,
            "concept:name": "Login",
            "time:timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
        })

        # Decide randomly if the student views content (80% chance)
        if np.random.rand() < 0.8:
            delay = np.random.randint(1, 10)  # delay in minutes
            current_time += timedelta(minutes=delay)
            events.append({
                "case:concept:name": case_id,
                "concept:name": "View_Content",
                "time:timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        # Decide randomly if the student attempts the quiz (90% chance)
        if np.random.rand() < 0.9:
            delay = np.random.randint(1, 5)
            current_time += timedelta(minutes=delay)
            events.append({
                "case:concept:name": case_id,
                "concept:name": "Attempt_Quiz",
                "time:timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })

            # Decide randomly if the student submits the quiz (80% chance among those who attempted)
            if np.random.rand() < 0.8:
                delay = np.random.randint(2, 15)  # more variability here
                current_time += timedelta(minutes=delay)
                events.append({
                    "case:concept:name": case_id,
                    "concept:name": "Submit_Quiz",
                    "time:timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                })
        # Logout is always last
        delay = np.random.randint(1, 5)
        current_time += timedelta(minutes=delay)
        events.append({
            "case:concept:name": case_id,
            "concept:name": "Logout",
            "time:timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Create DataFrame and sort
    df = pd.DataFrame(events)
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
    df = df.sort_values(["case:concept:name", "time:timestamp"])
    return df


if __name__ == "__main__":
    df_big = generate_synthetic_log(num_cases=500)
    # Save to CSV
    df_big.to_csv("big_synthetic_event_log.csv", index=False)
    print("Big synthetic event log generated and saved as 'big_synthetic_event_log.csv'.")