import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def load_csv_files(region, app_type):
    data = {}
    results_dirs = sorted([d for d in os.listdir() if d.startswith('results_')])

    for dir_name in results_dirs:
        date = dir_name.split('_')[1]
        file_path = f"{dir_name}/app_store_top_100_{region}_{app_type}.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(date)
            df = df.set_index('name')
            data[date] = df

    return data

def analyze_ranking_changes(data, top_n=10):
    all_apps = set()
    for df in data.values():
        all_apps.update(df.index)

    ranking_changes = {app: [] for app in all_apps}
    dates = sorted(data.keys())

    for date in dates:
        df = data[date]
        for app in all_apps:
            rank = df.loc[app]['rank'] if app in df.index else None
            ranking_changes[app].append(rank)

    # Sort apps by their average rank (excluding None values)
    top_apps = sorted(ranking_changes.items(),
                      key=lambda x: sum(r for r in x[1] if r is not None) / len([r for r in x[1] if r is not None]))[:top_n]

    return top_apps, dates

def plot_ranking_changes(top_apps, dates, region, app_type):
    plt.figure(figsize=(12, 8))
    for app, ranks in top_apps:
        plt.plot(dates, ranks, marker='o', label=app)

    plt.gca().invert_yaxis()  # Invert y-axis so that rank 1 is at the top
    plt.xlabel('Date')
    plt.ylabel('Rank')
    plt.title(f'Top {len(top_apps)} App Ranking Changes - {region.upper()} {app_type.capitalize()}')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # Save the plot
    plot_dir = 'ranking_plots'
    os.makedirs(plot_dir, exist_ok=True)
    plt.savefig(f'{plot_dir}/ranking_changes_{region}_{app_type}.png')
    plt.close()

def main():
    regions = ['us', 'gb', 'jp', 'kr', 'cn', 'hk', 'tw', 'th', 'sg', 'my', 'ph', 'id', 'in', 'ru']
    app_types = ['free', 'paid']

    for region in regions:
        for app_type in app_types:
            print(f"Analyzing {region} {app_type} apps...")
            data = load_csv_files(region, app_type)
            if data:
                top_apps, dates = analyze_ranking_changes(data)
                plot_ranking_changes(top_apps, dates, region, app_type)
                print(f"Plot saved for {region} {app_type} apps")
            else:
                print(f"No data found for {region} {app_type} apps")

if __name__ == "__main__":
    main()