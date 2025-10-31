import os

import pandas as pd
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.dates as mdates

if __name__ == "__main__":
    C_BASE_PATH_OUT_CSV = "csv_expo/"

    assert os.path.exists(C_BASE_PATH_OUT_CSV), f"Output path {C_BASE_PATH_OUT_CSV} does not exist."

    # Get CSV Filepaths
    csv_filepaths = [
        os.path.join(C_BASE_PATH_OUT_CSV, f) for f in os.listdir(C_BASE_PATH_OUT_CSV)
        if f.endswith('.csv') and not f.startswith('~$')  # Exclude temporary files
    ]

    print("CSV Filepaths:", csv_filepaths)


    def load_csv(filepath):
        import pandas as pd
        return pd.read_csv(filepath)


    # Load all CSV files into a list of DataFrames
    dataframes = [load_csv(fp) for fp in csv_filepaths]

    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(dataframes, ignore_index=True)
    del dataframes  # Free memory

    print("Combined DataFrame columns:", combined_df.columns)

    print("First Date before conversion:", combined_df['utc_start'].head(1))

    combined_df['utc_start'] = pd.to_datetime(combined_df['utc_start'], errors='coerce')
    combined_df['utc_stop'] = pd.to_datetime(combined_df['utc_stop'], errors='coerce')

    print("First Date after conversion:", combined_df['utc_start'].head(1))

    # Sort by utc_start
    combined_df.sort_values(by='utc_start', inplace=True)

    # # TODO
    # combined_df['dur_s'].hist(bins=50)
    # plt.title("Duration Histogram")
    # plt.show()
    # plt.close("all")
    #
    # # TODO
    # combined_df['dB'].hist(bins=50)
    # plt.title("dB Histogram")
    # plt.show()
    # plt.close("all")

    # First and Last Detection utc_start
    first_detection = combined_df['utc_start'].min()
    last_detection = combined_df['utc_start'].max()
    print(f"First Detection: {first_detection}")
    print(f"Last Detection: {last_detection}")


    def plot_det_per_hour(df):
        df = df.copy()

        # Neue Spalte mit nur Jahr-Monat-Tag-Stunde
        df['hour'] = df['utc_start'].dt.floor('h')

        # Gruppieren nach Stunde und zählen
        detections_per_hour = df.groupby('hour').size()

        # Plotten
        plt.figure(figsize=(12, 6))
        detections_per_hour.plot(kind='bar')
        plt.xlabel('UTC Detektionen (pro Stunde)')
        plt.ylabel('Anzahl Detektionen')
        plt.title('Detektionen pro Stunde')
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.show()


    # TODO
    # plot_det_per_hour(combined_df)

    def plot_det_per_day(df):
        df = df.copy()

        # Neue Spalte mit nur Jahr-Monat-Tag
        df['day'] = df['utc_start'].dt.floor('d')

        # Gruppieren nach Tag und zählen
        detections_per_day = df.groupby('day').size()

        # Plotten
        plt.figure(figsize=(12, 6))
        detections_per_day.plot(kind='bar')
        plt.xlabel('Datum')
        plt.ylabel('Anzahl Detektionen')
        plt.title('Detektionen pro Tag')
        # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        # plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.grid(True)
        plt.show()
        plt.close("all")


    # TODO
    # plot_det_per_day(combined_df)

    def plot_det_per_hour_plotly(df, filename="detektionen_pro_stunde.html"):
        df = df.copy()

        # Neue Spalte mit nur Jahr-Monat-Tag-Stunde
        df['hour'] = df['utc_start'].dt.floor('h')

        # Gruppieren nach Stunde und zählen
        detections_per_hour = df.groupby('hour').size()

        # Erstellen des Barplots
        fig = go.Figure(data=[
            go.Bar(
                x=detections_per_hour.index.astype(str),
                # Konvertiere Timestamp zu String für bessere Achsenbeschriftung
                y=detections_per_hour.values
            )
        ])

        fig.update_layout(
            title="Detektionen pro Stunde",
            xaxis_title="UTC Start (pro Stunde)",
            yaxis_title="Anzahl Detektionen",
            xaxis_tickangle=-90,
            template="plotly_white"
        )

        # Speichern als HTML-Datei
        fig.write_html(filename)
        print(f"Plot gespeichert unter: {filename}")


    # TODO
    # plot_det_per_hour_plotly(
    #     df=combined_df,
    #     filename=os.path.join(C_BASE_PATH_OUT_CSV, "detektionen_pro_stunde.html")
    # )

    def plot_hour_day_heatmap(df):
        df = df.copy()

        # Sicherstellen, dass 'utc_start' ein datetime-Objekt ist
        df['utc_start'] = pd.to_datetime(df['utc_start'])

        df = df[df['utc_start'].notna()]

        # Neue Spalten für Stunde und Datum
        df['hour'] = df['utc_start'].dt.hour.astype(int)
        df['date'] = df['utc_start'].dt.date  # Nur das Datum, ohne Uhrzeit

        # Gruppieren nach Datum und Stunde
        heatmap_data = df.groupby(['date', 'hour']).size().unstack(fill_value=0)

        # Optional: sortieren nach Datum (falls nicht schon sortiert)
        heatmap_data = heatmap_data.sort_index()

        # Filter from 2025-06-06 to 2025-06-23
        start_date = pd.to_datetime("2025-06-06").date()
        end_date = pd.to_datetime("2025-06-23").date()

        heatmap_data = heatmap_data.loc[(heatmap_data.index >= start_date) & (heatmap_data.index <= end_date)]

        heatmap_data.index = pd.to_datetime(heatmap_data.index).strftime('%d.%m.%Y')

        # Plotten
        plt.figure(figsize=(14, max(6, 0.3 * len(heatmap_data))))  # Höhe dynamisch anpassen
        sns.heatmap(heatmap_data, cmap='viridis', annot=True, linewidths=0.01, linecolor='grey')
        # plt.title('Detektionen pro Stunde und Tag')
        plt.xlabel('Hour (UTC)')
        plt.ylabel('Date')
        plt.tight_layout()
        plt.savefig("heatmap.pdf")
        plt.show()
        plt.close("all")


    # TODO
    plot_hour_day_heatmap(
        df=combined_df
    )
