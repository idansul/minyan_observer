import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines


class MinyanObserver:

    def __init__(self, data):
        self.data = data
        self.preprocessing()

    def preprocessing(self):
        # Parse date correctly
        self.data['date'] = pd.to_datetime(self.data['date'], format='%d/%m/%Y')
        
        # Ensure data is sorted
        self.data = self.data.sort_values("date").reset_index(drop=True)
        
        # Count how many times day==1 (Sunday) has appeared so far
        self.data["week_number"] = (self.data["day_of_week"] == 1).cumsum() + 1

    def get_duration(self, data):
        # Determine duration type for each day
        duration = data[["until_kdusha", "until_titkabal", "until_the_end"]].idxmax(axis=1)
        duration_map = {"until_kdusha": "▲", "until_titkabal": "■", "until_the_end": "★"}
        return duration, duration_map

    def get_week_data(self):
        max_week = self.data["week_number"].max()
        week_data = self.data[self.data["week_number"] == max_week]
        return week_data

    def get_recent_weeks(self, n_weeks=2):
        max_week = self.data["week_number"].max()
        min_week = max_week - n_weeks + 1
        recent_weeks = self.data[self.data["week_number"].between(min_week, max_week)]
        return recent_weeks

    def subplot_legend(self):
        # create handles for bar colors
        handles_colors = [
            mpatches.Patch(color="steelblue", label="מתפללים קבועים"[::-1]),
            mpatches.Patch(color="skyblue", label="מזדמנים מהשכונה"[::-1]),
            mpatches.Patch(color="lightcyan", label="מזדמנים מבחוץ"[::-1]),
        ]
        
        # create handles for the shapes (markers only)
        handles_shapes = [
            mlines.Line2D([], [], color="black", marker="^", linestyle="None", markersize=10, label="עד קדושה"[::-1]),
            mlines.Line2D([], [], color="black", marker="s", linestyle="None", markersize=10, label="עד תתקבל"[::-1]),
            mlines.Line2D([], [], color="black", marker="*", linestyle="None", markersize=10, label="עד הסוף"[::-1]),
        ]
        
        # combine and place the legend outside the axes
        all_handles = handles_colors + handles_shapes
        return all_handles

    def plot(self, data=None, save=False):
        if data is None:
            data = self.data

        # Get the week number from the first row of the current data slice
        week_num = data["week_number"].iloc[0]

        fig, ax = plt.subplots(figsize=(8, 5))

        # Stacked bars with blue shades
        ax.bar(data["date"], data["core_members"], color="steelblue", label="מתפללים קבועים"[::-1])
        ax.bar(data["date"], data["occasional_members_inside"],
               bottom=data["core_members"], color="skyblue", label="מזדמנים מהשכונה"[::-1])
        ax.bar(data["date"], data["occasional_members_outside"],
               bottom=data["core_members"] + data["occasional_members_inside"],
               color="lightcyan", label="מזדמנים מבחוץ"[::-1])

        # Red dashed line for minyan threshold
        ax.axhline(10, color="red", linestyle="--", linewidth=1)

        # Bar tops for placing symbols
        bar_tops = data["core_members"] + data["occasional_members_inside"] + data["occasional_members_outside"]

        # Determine duration type for each day
        duration, duration_map = self.get_duration(data)

        # Add symbols above each bar
        for x, y, dur, total in zip(data["date"], bar_tops, duration, data["sum"]):
            if total >= 10:
                ax.text(x, y + 0.5, duration_map[dur], ha="center", va="bottom", fontsize=14, color="black")

        # Adjust y-axis to make room for symbols
        ax.set_ylim(top=bar_tops.max() + 3)

        hebrew_days = {"Sun": "א", "Mon": "ב", "Tue": "ג", "Wed": "ד", "Thu": "ה", "Fri": "ו"}

        hebrew_title = "נוכחות מניין ומשך התפילה - שבוע"[::-1]
        ax.set_title(f"#{week_num} {hebrew_title}")
        ax.set_ylabel("מספר מתפללים"[::-1])
        ax.grid(axis='y', linewidth=0.3)

        # Add text annotation on the plot (top-left corner)
        ax.text(
            0.87, 0.98,
            f"Mean: {data['sum'].mean():.2f}\nStd: {data['sum'].std():.2f}",
            transform=ax.transAxes,
            ha="left", va="top",
            fontsize=10, color="black",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
        )

        ax.set_xticks(data["date"])
        ax.set_xticklabels([f"א\n{d.strftime('%d-%m-%Y')}" if d.strftime("%a") == "Sun" else hebrew_days[d.strftime("%a")] for d in data["date"]])

        y_max = int(ax.get_ylim()[1])
        ax.set_yticks(range(0, y_max + 1, 2))

        # make room on the right so legend won't touch bars
        fig.subplots_adjust(right=0.78)   # reduce axes width, leave space on the right
        ax.legend(handles=self.subplot_legend(), loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True)
        
        plt.tight_layout(rect=[0, 0, 1.2, 1])
        
        # plt.tight_layout()
        if save:
            sunday_date = data.loc[data["date"].dt.dayofweek == 6, "date"].iloc[0].strftime("%d-%m-%Y")
            plt.savefig(f"weekly_reports/minyan_plot_{sunday_date}.jpg", dpi=200, bbox_inches="tight")  # save as JPG
        plt.show()

    def plot_this_week(self, save=False):
        week_data = self.get_week_data()
        self.plot(week_data, save)

    def plot_recent_weeks(self, n_weeks=2):
        recent_data = self.get_recent_weeks(n_weeks)
        self.plot(recent_data)

    def plot_recent_weeks_stats(self, n_weeks=2, var="day"):
        data = self.get_recent_weeks(n_weeks)
        self.plot_global_stats(var, data)

    def plot_global_stats(self, var="day", data=None, save=False):
        # Calculate mean and std per week/day
        if data is None:
            data = self.data
        if var == "day":
            stats = data.groupby("day_of_week")["sum"].agg(["mean", "std"])
            xlabel = "יום"[::-1]
            heb_var = "יום"
        elif var == "week":
            stats = data.groupby("week_number")["sum"].agg(["mean", "std"])
            xlabel = "מספר שבוע"[::-1]
            heb_var = "שבוע"
    
        fig, ax = plt.subplots(figsize=(8, 5))
    
        # Plot means with error bars for std
        ax.errorbar(
            stats.index,
            stats["mean"],
            yerr=stats["std"],
            fmt="o-", capsize=5, color="steelblue", ecolor="gray"
        )
        ax.axhline(10, color="red", linestyle="--", linewidth=1)
        
        # Axis settings
        ax.set_xticks(stats.index)  # show only integer week numbers
        ax.set_yticks(range(5, int(ax.get_ylim()[1]) + 1))
    
        ax.set_title(f"נוכחות מנין לפי {heb_var} )ממוצע ± סטיית("[::-1])
        ax.set_xlabel(xlabel)
        ax.set_ylabel("מספר מתפללים"[::-1])
        ax.grid(axis="y", linewidth=0.3)
    
        plt.tight_layout()
        if save:
            plt.savefig(f"weekly_reports/global_{var}s_stats.jpg", dpi=200, bbox_inches="tight")  # save as JPG
        plt.show()

