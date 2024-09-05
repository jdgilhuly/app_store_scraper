import os
import pandas as pd
from collections import defaultdict

def load_csv_files(region, app_type):
    data = {}
    results_dirs = sorted([d for d in os.listdir('results') if d.isdigit()])

    for date_dir in results_dirs:
        file_path = f"results/{date_dir}/{region}_app_store_top_100_{app_type}.csv"
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(date_dir)
            df = df.set_index('name')
            data[date_dir] = df

    return data

def analyze_ranking_changes(data):
    all_apps = set()
    for df in data.values():
        all_apps.update(df.index)

    ranking_changes = defaultdict(lambda: defaultdict(lambda: None))
    dates = sorted(data.keys())

    for date in dates:
        df = data[date]
        for app in all_apps:
            if app in df.index:
                ranking_changes[app][date] = df.loc[app]['rank']

    return ranking_changes, dates

def get_top_movers(ranking_changes, dates, top_n=5):
    daily_changes = []

    for i in range(1, len(dates)):
        prev_date, curr_date = dates[i-1], dates[i]
        changes = []

        for app, ranks in ranking_changes.items():
            prev_rank, curr_rank = ranks[prev_date], ranks[curr_date]
            if prev_rank is not None and curr_rank is not None:
                change = prev_rank - curr_rank
                changes.append((app, change, prev_rank, curr_rank))

        changes.sort(key=lambda x: abs(x[1]), reverse=True)
        daily_changes.append((prev_date, curr_date, changes[:top_n], changes[-top_n:][::-1]))

    return daily_changes

def print_ranking_changes(daily_changes, region, app_type):
    print(f"\nRanking Changes for {region.upper()} {app_type.capitalize()}:")
    print(f"\nDate range: {daily_changes[0][0]} to {daily_changes[-1][1]}\n")

    for prev_date, curr_date, top_risers, top_fallers in daily_changes:
        print(f"Changes from {prev_date} to {curr_date}:")

        print("\nTop Risers:")
        for app, change, prev_rank, curr_rank in top_risers:
            print(f"  {app}: +{change} (from {prev_rank} to {curr_rank})")

        print("\nTop Fallers:")
        for app, change, prev_rank, curr_rank in top_fallers:
            print(f"  {app}: {change} (from {prev_rank} to {curr_rank})")

        print("\n" + "-"*50 + "\n")

def calculate_global_score(app_data, regions):
    total_score = 0
    valid_regions = 0
    for region in regions:
        if region in app_data and app_data[region] is not None:
            total_score += 101 - app_data[region]  # Invert rank so higher is better
            valid_regions += 1

    # Return average score only if the app has rankings in at least one region
    return total_score / valid_regions if valid_regions > 0 else 0

def get_global_rankings(data, regions, date, top_n=10):
    global_scores = defaultdict(dict)

    for region in regions:
        if region in data and date in data[region]:
            df = data[region][date]
            for app, row in df.iterrows():
                if app not in global_scores:
                    global_scores[app] = {r: None for r in regions}
                global_scores[app][region] = row['rank']

    app_scores = [(app, calculate_global_score(scores, regions)) for app, scores in global_scores.items()]
    app_scores.sort(key=lambda x: x[1], reverse=True)

    return app_scores[:top_n]

def print_global_rankings(global_rankings, date):
    print(f"\nGlobal Rankings for {date}:")
    for rank, (app, score) in enumerate(global_rankings, 1):
        print(f"{rank}. {app}: {score:.2f}")
    print("\n" + "-"*50 + "\n")

def main():
    regions = ['us', 'gb', 'jp', 'kr', 'cn', 'hk', 'tw', 'th', 'sg', 'my', 'ph', 'id', 'in', 'ru']
    app_types = ['free_apps', 'paid_apps', 'free_games', 'paid_games']

    for app_type in app_types:
        print(f"\nAnalyzing global rankings for {app_type}...")
        global_data = {region: load_csv_files(region, app_type) for region in regions}

        all_dates = set()
        for region_data in global_data.values():
            all_dates.update(region_data.keys())
        all_dates = sorted(all_dates)

        for date in all_dates:
            global_rankings = get_global_rankings(global_data, regions, date)
            print_global_rankings(global_rankings, date)

        for region in regions:
            print(f"\nAnalyzing {region} {app_type}...")
            data = global_data[region]
            if data:
                ranking_changes, dates = analyze_ranking_changes(data)
                daily_changes = get_top_movers(ranking_changes, dates)
                print_ranking_changes(daily_changes, region, app_type)
            else:
                print(f"No data found for {region} {app_type}")

if __name__ == "__main__":
    main()