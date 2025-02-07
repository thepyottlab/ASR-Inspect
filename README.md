# ASR Inspect
<p align="center">
  <img src="https://github.com/user-attachments/assets/453c917e-1993-4bcb-8975-7978d5cbd17b" width="800" height="448">
</p>

ASR Inspect is a graphical tool for analyzing and classifying Acoustic Startle Reflex (ASR) measurements. It allows you to load datasets exported from the PCT software for the Kinder Scientific Startle Reflex System, visualize individual trials, and classify them as accepted or rejected.

## Features
- Load ASR measurement datasets (CSV files).
- Navigate between trials using arrow keys.
- Manually or automatically adjust the scale.
- Toggle trial status (Accepted ↔ Rejected) using the space bar.
- Remove rejected trials from the dataset.
- Export datasets before or after filtering or classifying.

## Installation
1. Navigate to [Releases](https://github.com/thepyottlab/ASR-Inspect/releases).
2. [Download](https://github.com/thepyottlab/ASR-Inspect/releases/download/ASR-Inspect-v1.0-06-Feb-2025/ASR_Inspect_Setup.exe) the `ASR Inspect Setup.exe` file.
3. Run the installer.

## Usage
1. Run the application.
2. Load a dataset (CSV exported from PCT software using the 'Reduce' functionality).
3. Navigate trials using arrow keys or enter a trial number.
4. Mark trials as rejected using the space bar.
5. Adjust Y-scale manually or enable auto-scaling.
6. Export the dataset before or after removing rejected trials.

To test the application, you can download a sample dataset:
[Sample Data - Kinder Scientific ASR Assay.csv](https://github.com/thepyottlab/ASR-Inspect/blob/main/Sample%20Data%20-%20Kinder%20Scientific%20ASR%20Assay.csv)

## Keyboard Shortcuts

| Key         | Action                   |
|------------|--------------------------|
| **→ / ←**  | Next/Previous trial    |
| **Space**  | Toggle Accept/Reject     |
