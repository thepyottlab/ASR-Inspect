import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import filedialog, ttk
from scipy.signal import find_peaks


def select_csv_file():
    """
    Opens a dialog to select a CSV file and returns the selected file path.
    """
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select dataset",
                                           filetypes=[("CSV files", "*.csv")])
    root.destroy()
    return file_path


def load_csv(file_path):
    """
    Loads a CSV file into a Pandas DataFrame.
    """
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        print(f"Error loading the file: {e}")
        return None


def add_accepted_status_column(df):
    """
    Adds a 'Status' column to the DataFrame, defaulting to 'Accepted'.
    """
    if 'Status' not in df.columns:
        df['Status'] = 'Accepted'
    df.loc[df['TrialName'].str.contains('wav', case=False, regex=True), 'Status'] = 'Rejected'
    return df


def sort_dataframe(df):
    """
    Sorts the DataFrame based on specified columns.
    """
    return df.sort_values(
        by=['Session', 'TrialNo'])


# noinspection PyMethodMayBeStatic,PyAttributeOutsideInit
class TrialApp(tk.Tk):
    """
    A Tkinter application for analyzing and validating trial data.
    """

    def __init__(self, df, original_file_name):
        super().__init__()
        self.data_frame = df
        self.original_file_name = original_file_name
        self.current_trial_index = 0
        self.rejected_trials_list = []
        self.enclosure_max = 1
        self.enclosure_min = -0.5
        self.y_max_variable = tk.StringVar(value=str(self.enclosure_max))
        self.y_min_variable = tk.StringVar(value=str(self.enclosure_min))
        self.is_autoscale_enabled = False
        self.style = ttk.Style()
        self.default_font = 'Segoe UI'
        self.configure_styles(self.style)
        self.initialize_user_interface()
        self.protocol("WM_DELETE_WINDOW", self.close_application)

    def configure_styles(self, style):
        """
        Configures the styles used in the application.
        """
        if "azure-light" not in style.theme_names():
            self.tk.call("source", "azure/azure.tcl")
        self.tk.call("set_theme", "light")
        style.configure('TLabel', font=(self.default_font, 10))
        style.configure('TLabelframe.Label',
                        font=(self.default_font, 13, 'bold'))
        style.configure('TButton', font=(self.default_font, 11))
        style.configure('Accent.TButton', font=(self.default_font, 10, 'bold'),
                        foreground='white')
        style.configure('Switch.TCheckbutton', font=(self.default_font, 10))
        style.configure("Treeview", font=(self.default_font, 9), rowheight=25)
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def initialize_user_interface(self):
        """
        Initializes the user interface elements of the application.
        """
        self.title("GPIAS Trial Marker")
        screen_width, screen_height = (self.winfo_screenwidth(),
                                       self.winfo_screenheight())
        self.geometry(f"{screen_width}x{screen_height}")

        style = ttk.Style()
        self.configure_styles(style)

        self.create_main_container()
        self.create_left_panel()
        self.create_plot_frame()
        self.create_rejected_trials_frame()

        self.bind_event_handlers()

    def create_main_container(self):
        """
        Creates the main container frame.
        """
        self.container = ttk.Frame(self, style='TFrame')
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1, uniform="group1")
        self.container.grid_columnconfigure(1, weight=4, uniform="group1")
        self.container.grid_columnconfigure(2, weight=1, uniform="group1")

    def create_left_panel(self):
        """
        Creates the left panel with control elements.
        """
        left_panel = ttk.Frame(self.container, style='TFrame', padding=(5, 5))
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5),
                        pady=(10, 30))

        self.create_instructions_frame(left_panel)
        self.create_scale_panel(left_panel)
        self.create_navigation_panel(left_panel)
        self.create_control_panel(left_panel)

    def create_instructions_frame(self, left_panel):
        """
        Creates the instructions frame.
        """
        instructions_frame = ttk.LabelFrame(left_panel, text="Instructions")
        instructions_frame.pack(fill="both", expand=True, padx=10, pady=(6, 5))

        instructions_text = ("Use arrow keys to navigate between trials. "
                             "Press space bar to change the trial status. "
                             "Use the button to remove rejected trials. "
                             "Save your progress using the save button.")
        instructions_label = ttk.Label(instructions_frame,
                                       text=instructions_text, anchor="nw",
                                       style='TLabel',
                                       wraplength=250)
        instructions_label.pack(side="top", fill="both", expand=True,
                                padx=(10, 5), pady=10)

        load_file_button = ttk.Button(instructions_frame, text="Load File",
                                      command=self.load_new_file,
                                      style="Accent.TButton")
        load_file_button.pack(side="bottom", fill="x", padx=15, pady=15)

    def create_scale_panel(self, left_panel):
        """
        Creates the scale adjustment panel.
        """
        scale_panel = ttk.LabelFrame(left_panel, text="Y Scale Adjustment")
        scale_panel.pack(fill="both", expand=True, padx=10, pady=5)

        scale_label_upper = ttk.Label(scale_panel,
                                      text="Upper limit Y scale (N):",
                                      style='TLabel')
        scale_label_upper.pack(side="top", padx=5, pady=(10, 5))
        self.y_max_entry = ttk.Entry(scale_panel,
                                     textvariable=self.y_max_variable,
                                     style="TEntry")
        self.y_max_entry.pack(side="top", fill="x", padx=5, pady=2)
        self.y_max_entry.bind('<Return>', self.on_y_axis_entry_change)

        scale_label_lower = ttk.Label(scale_panel,
                                      text="Lower limit Y scale (N):",
                                      font=(self.default_font, 10))
        scale_label_lower.pack(side="top", padx=5, pady=(10, 5))
        self.y_min_entry = ttk.Entry(scale_panel,
                                     textvariable=self.y_min_variable)
        self.y_min_entry.pack(side="top", fill="x", padx=5, pady=2)
        self.y_min_entry.bind('<Return>', self.on_y_axis_entry_change)

        scale_button = ttk.Checkbutton(scale_panel, text="Autoscale",
                                       command=self.toggle_autoscale,
                                       style='Switch.TCheckbutton')
        scale_button.pack(side="bottom", fill="x", padx=80, pady=15)

    def create_navigation_panel(self, left_panel):
        """
        Creates the trial navigation panel.
        """
        navigation_panel = ttk.LabelFrame(left_panel, text="Navigate Trials")
        navigation_panel.pack(fill="both", expand=True, padx=10, pady=5)

        self.trial_info_label = ttk.Label(navigation_panel,
                                          font=(self.default_font, 10))
        self.trial_info_label.pack(side="top", padx=5, pady=(10, 5))
        self.update_trial_info_label()

        self.trial_number_var = tk.StringVar()
        self.trial_number_entry = ttk.Entry(navigation_panel,
                                            textvariable=self.trial_number_var,
                                            style="TEntry")
        self.trial_number_entry.pack(side="top", fill="x", padx=5, pady=2)
        self.trial_number_entry.bind('<Return>', self.on_trial_number_entry)

    def create_control_panel(self, left_panel):
        """
        Creates the control panel with operation buttons.
        """
        control_panel = ttk.LabelFrame(left_panel, text="Operations")
        control_panel.pack(fill="both", expand=True, padx=10, pady=(5, 17))

        remove_rejected_button = ttk.Button(control_panel,
                                            text="Remove Rejected Trials",
                                            command=self.remove_rejected,
                                            style="Accent.TButton")
        remove_rejected_button.pack(side="top", fill="x", padx=15,
                                    pady=(15, 10))
        export_button = ttk.Button(control_panel, text="Save",
                                   command=self.export_df,
                                   style="Accent.TButton")
        export_button.pack(side="top", fill="x", padx=15, pady=0)
        self.export_status_label = ttk.Label(control_panel, text="",
                                             font=(self.default_font, 10))
        self.export_status_label.pack(side="top", fill="x", padx=(15, 0),
                                      pady=5)

    def create_plot_frame(self):
        """
        Creates the frame for plotting trial data.
        """
        self.plot_frame = ttk.Frame(self.container)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20),
                             pady=(32, 53))

    def create_rejected_trials_frame(self):
        """
        Creates the frame for displaying rejected trials.
        """
        self.rejected_trials_frame = ttk.Labelframe(self.container,
                                                    text="Rejected trials")
        self.rejected_trials_frame.grid(row=0, column=2, sticky="nsew",
                                        padx=(0, 20), pady=(21, 53))

    def bind_event_handlers(self):
        """
        Binds key event handlers to the application.
        """
        self.bind("<space>", lambda event: self.toggle_status())
        self.bind("<Left>", lambda event: self.prev_trial())
        self.bind("<Right>", lambda event: self.next_trial())

    def update_plot(self, y_min=None, y_max=None):
        """
        Updates the plot based on the current state of the application.
        """
        if hasattr(self, 'fig'):
            plt.close(self.fig)

        if self.data_frame.empty:
            self.fig, ax = plt.subplots()
            ax.set_title('No Data Loaded', fontsize=14)
            ax.set_xlabel('X-axis')
            ax.set_ylabel('Y-axis')
        else:
            trial_data = self.data_frame.iloc[self.current_trial_index:
                                              self.current_trial_index + 500]
            self.update_trial_info_label()
            self.fig = self.create_trial_plot(trial_data)

            if hasattr(self, 'plot_canvas'):
                self.plot_canvas.get_tk_widget().pack_forget()
                self.plot_canvas.get_tk_widget().destroy()

            self.plot_canvas = FigureCanvasTkAgg(self.fig,
                                                 master=self.plot_frame)
            self.plot_canvas.draw()
            self.plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True,
                                                  padx=0, pady=0)

    def create_trial_plot(self, trial_data):
        """
        Creates a plot for the given trial data segment with transformed data to show peaks.
        """
        median_encl1 = trial_data['Encl 1'].median()
        net_force = trial_data['Encl 1'] - median_encl1

#        peak_to_trough_amplitudes = self.calculate_peak_to_trough_amplitudes(
#            net_force)
#        baseline_to_peak_amplitudes = self.calculate_baseline_to_peak_amplitudes(
 #           net_force)

        plt.style.use('seaborn-v0_8-whitegrid')
        #fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
        fig, (ax1) = plt.subplots(1, 1, figsize=(12, 15), sharex=True)
        fig.subplots_adjust(left=0.075, right=0.925, top=0.95, bottom=0.05)

        ax1.plot(trial_data['Time(ms)'], net_force,
                 color='dodgerblue', linestyle='-', linewidth=2.5)
        ax1.set_ylabel('Amplitude (N)', fontsize=12, fontname="Segoe UI")
        ax1.grid(True, linestyle='--', linewidth=0.25, color='grey', alpha=0.5)
        ax1.axvspan(300, 320, color='gray', alpha=0.5, label='Time Range 300-320 ms')

        #        ax2.plot(trial_data['Time(ms)'], peak_to_trough_amplitudes,
 #                color='dodgerblue', linestyle='-', linewidth=2.5)
  #      ax2.set_ylabel('Peak to Trough Amplitude (N)', fontsize=12,
   #                    fontname="Segoe UI")
    #    ax2.grid(True, linestyle='--', linewidth=0.25, color='grey', alpha=0.5)
#
 #       ax3.plot(trial_data['Time(ms)'], baseline_to_peak_amplitudes, color='dodgerblue', linestyle='-', linewidth=2.5)
  #      ax3.set_xlabel('Time (ms)', fontsize=12, fontname="Segoe UI")
   #     ax3.set_ylabel('Baseline to Peak Amplitude (N)', fontsize=12, fontname="Segoe UI")
    #    ax3.grid(True, linestyle='--', linewidth=0.25, color='grey', alpha=0.5)"""
#
        y_min1, y_max1 = self.calculate_y_axis_limits(net_force)
  #      y_min2, y_max2 = self.calculate_y_axis_limits(peak_to_trough_amplitudes)
   #     y_min3, y_max3 = self.calculate_y_axis_limits(baseline_to_peak_amplitudes)

        ax1.set_ylim(y_min1, y_max1)
#        ax2.set_ylim(y_min2, y_max2)
 #       ax3.set_ylim(y_min3, y_max3)

        self.set_plot_titles(ax1, trial_data)
        return fig

    def calculate_peak_to_trough_amplitudes(self, trial):
        positive_peaks, _ = find_peaks(trial.values, width=1,
                                       prominence=0.025)
        negative_peaks, _ = find_peaks(-trial.values, width=1,
                                       prominence=0.025)

        # Initialize an array of zeros for the amplitudes
        peak_to_trough_amplitudes = np.zeros_like(trial)

        for peak in positive_peaks:
            left_troughs = negative_peaks[negative_peaks < peak]
            right_troughs = negative_peaks[negative_peaks > peak]

            left_trough = left_troughs[-1] if left_troughs.size > 0 else None
            right_trough = right_troughs[0] if right_troughs.size > 0 else None

            # Make sure we're within bounds when accessing the series
            if left_trough is not None and right_trough is not None:
                amplitude_left = trial.iloc[peak] - trial.iloc[left_trough]
                amplitude_right = trial.iloc[peak] - trial.iloc[right_trough]
                amplitude = max(amplitude_left, amplitude_right)
            elif left_trough is not None:
                amplitude = trial.iloc[peak] - trial.iloc[left_trough]
            elif right_trough is not None:
                amplitude = trial.iloc[peak] - trial.iloc[right_trough]
            else:
                amplitude = trial.iloc[peak]

            # Set the peak-to-trough amplitude at the peak position
            peak_to_trough_amplitudes[peak] = amplitude

        return peak_to_trough_amplitudes

    def calculate_baseline_to_peak_amplitudes(self, trial):
        positive_peaks, _ = find_peaks(trial.values,
                                       height=0, width=1,
                                       prominence=0.025)
        baseline_to_peak_amplitudes = np.zeros_like(trial)

        for peak in positive_peaks:
            amplitude = trial.iloc[peak]
            baseline_to_peak_amplitudes[peak] = amplitude

        return baseline_to_peak_amplitudes
    def calculate_y_axis_limits(self, trial_data):
        """
        Calculates the Y-axis limits for the plot.
        """
        if self.is_autoscale_enabled:
            data_min, data_max = trial_data.min(), trial_data.max()
            data_range = data_max - data_min
            return data_min - data_range * 0.1, data_max + data_range * 0.1
        else:
            return float(self.y_min_variable.get()), float(
                self.y_max_variable.get())

    def set_plot_titles(self, ax, trial_data):
        """
        Sets titles and other information for the plot.
        """
        first_row = trial_data.iloc[0]

        ax.set_title(f'Status: {first_row["Status"]}', fontsize=14,
                     fontname="Segoe UI")

        ax.text(0.025, 0.98,
                f'{first_row["Session"]} - No. {first_row["TrialNo"]} - '
                f'{first_row["TrialName"]}',
                fontsize=10, fontweight='bold', fontname="Segoe UI", ha='left',
                va='top', transform=ax.transAxes)

        if hasattr(self, 'trial_info_label'):
            trial_info_text = self.trial_info_label.cget("text")
            ax.text(0.975, 0.98, trial_info_text,
                    fontsize=10, fontweight='bold', fontname="Segoe UI",
                    ha='right', va='top', transform=ax.transAxes)

    def calculate_autoscale_limits(self, data):
        """
        Calculates autoscale limits for the given data.
        """
        data_min, data_max = data.min(), data.max()
        data_range = data_max - data_min
        return data_min - data_range * 0.1, data_max + data_range * 0.1

    def update_rejected_trials_list(self):
        """
        Updates the list of rejected trials based on the current DataFrame.
        """
        self.rejected_trials_list.clear()
        if not self.data_frame.empty:
            unique_trials = self.data_frame.drop_duplicates(
                subset=['TrialIndex', 'Session'])
            trial_index = 0
            for idx, row in unique_trials.iterrows():
                trial_index += 1
                if self.data_frame.loc[idx, 'Status'] == 'Rejected':
                    trial_info = self.construct_trial_info(trial_index, row)
                    self.rejected_trials_list.append(trial_info)

        self.populate_rejected_trials_treeview()

    def update_trial_info_label(self):
        """
        Updates the information label with the current trial number.
        """
        total_trials = len(self.data_frame) // 500
        self.current_trial_number = self.current_trial_index // 500 + 1 \
            if not self.data_frame.empty else 0
        self.trial_info_label.config(
            text=f"Displayed trial: {self.current_trial_number} / "
                 f"{total_trials}")

    def on_trial_number_entry(self, event):
        """
        Handles the event when a trial number is entered for navigation.
        """
        self.current_trial_number = int(self.trial_number_var.get())
        total_trials = len(self.data_frame) // 500
        if 1 <= self.current_trial_number <= total_trials:
            self.current_trial_index = (self.current_trial_number - 1) * 500
            self.update_plot()

    def on_y_axis_entry_change(self, event=None):
        """
        Handles the change of Y-axis scale entries.
        """
        y_min = float(
            self.y_min_variable.get()) if self.y_min_variable.get() else None
        y_max = float(
            self.y_max_variable.get()) if self.y_max_variable.get() else None
        self.update_plot(y_min=y_min, y_max=y_max)

    def toggle_status(self):
        """
        Toggles the status of the current trial between 'Accepted' and
        'Rejected'.
        """
        current_block = self.data_frame.iloc[
                        self.current_trial_index:
                        self.current_trial_index + 500]
        new_status = 'Rejected' if current_block.iloc[0][
                                       'Status'] == 'Accepted' else 'Accepted'
        self.data_frame.loc[current_block.index, 'Status'] = new_status

        trial_info = self.construct_trial_info(self.current_trial_number,
                                               current_block.iloc[0])
        if new_status == 'Rejected':
            if trial_info not in self.rejected_trials_list:
                self.rejected_trials_list.append(trial_info)
        else:
            if trial_info in self.rejected_trials_list:
                self.rejected_trials_list.remove(trial_info)

        self.populate_rejected_trials_treeview()
        self.update_plot()

    def construct_trial_info(self, trial_index, trial_row):
        """
        Constructs a string with trial information.
        """
        return (
            f'Trial {trial_index}: {trial_row["Session"]} - '
            f'Trial {trial_row["TrialIndex"]} '
            f'{trial_row["TrialName"]}')

    def toggle_autoscale(self):
        """
        Toggles the autoscaling feature for the Y-axis of the plot.
        """
        self.is_autoscale_enabled = not self.is_autoscale_enabled
        self.update_plot()

    def next_trial(self):
        """
        Navigates to the next trial.
        """
        self.current_trial_index = min(self.current_trial_index + 500,
                                       len(self.data_frame) - 500)
        self.update_plot()

    def prev_trial(self):
        """
        Navigates to the previous trial.
        """
        self.current_trial_index = max(0, self.current_trial_index - 500)
        self.update_plot()

    def load_new_file(self):
        """
        Loads a new CSV file and updates the application with the new data.
        """
        new_csv_file = select_csv_file()
        if new_csv_file:
            new_df = load_csv(new_csv_file)
            if new_df is not None:
                new_df = add_accepted_status_column(new_df)
                new_df = sort_dataframe(new_df)
                self.data_frame = new_df
                self.current_trial_index = 0
                self.update_enclosure_limits()
                self.update_plot()
                self.update_rejected_trials_list()
                self.original_file_name = new_csv_file

    def select_csv_file(self):
        """
        Opens a dialog to select a CSV file and returns the selected file path.
        """
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select dataset",
                                               filetypes=[
                                                   ("CSV files", "*.csv")])
        root.destroy()
        return file_path

    def load_csv(self, file_path):
        """
        Loads a CSV file into the class's DataFrame attribute.
        """
        try:
            self.data_frame = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error loading the file: {e}")
            self.data_frame = None



    def sort_dataframe(self):
        """
        Sorts the class's DataFrame based on specified columns.
        """
        self.data_frame = self.data_frame.sort_values(
            by=['Session', 'TrialIndex'])

    def update_enclosure_limits(self):
        """
        Updates the max y scale value based on the dataset.
        """
        if not self.data_frame.empty:
            self.enclosure_max = round(self.data_frame['Encl 1'].max() * 0.6,
                                       1)
            self.y_max_variable.set(str(self.enclosure_max))

    def export_df(self):
        """
        Exports the current DataFrame to a CSV file.
        """
        self.export_status_label.config(text="Saving file...")
        original_name = os.path.basename(
            self.original_file_name) if self.original_file_name else ''
        default_name = os.path.splitext(original_name)[
                           0] + " - marked.csv" if original_name else \
            'exported_data.csv'

        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[
                                                     ("CSV files", "*.csv")],
                                                 initialfile=default_name)
        if file_path:
            self.data_frame.to_csv(file_path, index=False)
            self.export_status_label.config(text="File saved successfully.")
        else:
            self.export_status_label.config(text="")

    def remove_rejected(self):
        """
        Removes all rejected trials from the DataFrame and updates the
        application.
        """
        if self.data_frame is not None:
            self.data_frame = self.data_frame[
                self.data_frame['Status'] != 'Rejected']
            self.current_trial_index = 0
            self.update_plot()
            self.update_rejected_trials_list()

    def populate_rejected_trials_treeview(self):
        """
        Populates the treeview with the titles of rejected trials.
        """
        for widget in self.rejected_trials_frame.winfo_children():
            widget.destroy()

        tree = ttk.Treeview(self.rejected_trials_frame, selectmode='none',
                            show="tree")
        tree['columns'] = 0
        tree.column("#0", width=0, stretch=tk.NO, anchor="w")

        for title in self.rejected_trials_list:
            tree.insert("", tk.END, values=(title,))

        scrollbar = ttk.Scrollbar(self.rejected_trials_frame,
                                  command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", pady=(8, 12))
        tree.pack(side="left", fill="both", expand=True, pady=(2, 5))

    def close_application(self):
        """
        Closes the application and performs necessary cleanup operations.
        """
        plt.close('all')

        self.destroy()


def main():
    """
    The main function to start the TrialApp application.
    """
    initial_data_frame = pd.DataFrame()
    app = TrialApp(initial_data_frame, '')
    app.iconbitmap('icon.ico')
    app.mainloop()


if __name__ == "__main__":
    main()
