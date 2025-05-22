"""
Stock Suggester GUI application.

This application provides a user interface to find stock suggestions based on
predefined patterns analyzed from historical stock data.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from main_analyzer import get_stock_suggestions, DATA_DIRECTORY # For error message

def run_analysis_and_display_results(results_text_widget):
    """
    Handles the button click event to run stock analysis and display results.
    Calls main_analyzer.get_stock_suggestions() and formats the output for the GUI.
    """
    # Clear previous results
    results_text_widget.config(state=tk.NORMAL)
    results_text_widget.delete('1.0', tk.END)

    try:
        next_bday_obj, signals = get_stock_suggestions()

        if next_bday_obj is None:
            results_text_widget.insert(tk.END, "Error: Could not determine the next business day.\n"
                                               "This might be due to missing holiday data or other internal issues.\n"
                                               "Please check the console output from main_analyzer for more details.")
            results_text_widget.config(state=tk.DISABLED)
            return

        output_str = ""
        if signals:
            output_str += f"--- Stock Suggestions for Next Business Day: {next_bday_obj} ---\n"
            # Sort by probability (descending), then by ticker for consistent ordering
            signals_sorted = sorted(signals, key=lambda x: (x['prob'], x['ticker']), reverse=True)
            
            for signal in signals_sorted:
                output_str += (f"  Ticker: {signal['ticker']}, "
                               f"Pattern: {signal['pattern']}, "
                               f"Probability: {signal['prob']:.2f}, "
                               f"Occurrences: {signal['occ']}\n")
        else:
            output_str += f"No strong buy signals found for {next_bday_obj} based on current criteria.\n"
        
        results_text_widget.insert(tk.END, output_str)

    except FileNotFoundError:
        error_msg = (f"Error: The stock data directory '{DATA_DIRECTORY}' was not found.\n"
                     f"Please ensure the directory exists and contains the necessary CSV files.")
        results_text_widget.insert(tk.END, error_msg)
    except Exception as e:
        # Catch any other exceptions from get_stock_suggestions or GUI logic
        error_msg = f"An unexpected error occurred:\n{type(e).__name__}: {e}\n\n"
        error_msg += "Please check the console for more detailed error messages from the analysis script."
        results_text_widget.insert(tk.END, error_msg)
    
    results_text_widget.config(state=tk.DISABLED)


def main_gui():
    """
    Sets up and runs the main Tkinter GUI application.
    """
    root = tk.Tk()
    root.title("Stock Pattern Suggester")
    root.geometry("700x500") # Adjusted for better readability

    # Style
    style = ttk.Style()
    style.theme_use('clam') # Using a theme for a slightly more modern look

    # Main frame
    main_frame = ttk.Frame(root, padding="10 10 10 10")
    main_frame.pack(expand=True, fill=tk.BOTH)

    # Button to trigger analysis
    # Making button text more descriptive
    analyze_button = ttk.Button(
        main_frame,
        text="Find Stock Suggestions for Next Business Day",
        command=lambda: run_analysis_and_display_results(results_display_area)
    )
    analyze_button.pack(pady=10)

    # ScrolledText widget for displaying results
    results_display_area = scrolledtext.ScrolledText(
        main_frame,
        wrap=tk.WORD,
        state=tk.DISABLED, # Start as read-only
        height=20, # Adjusted height
        bg="white", fg="black" # Explicit colors
    )
    results_display_area.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    
    # Add a label for clarity
    results_label = ttk.Label(main_frame, text="Analysis Results:")
    # This is a bit tricky to place with pack, might need another frame or grid.
    # For simplicity, let's pack it before the text area.
    # To do this, we need to re-order packing or use another frame.
    # Re-packing `analyze_button` and adding label before `results_display_area`:
    analyze_button.pack_forget()
    results_display_area.pack_forget()

    analyze_button.pack(pady=(5,10)) # top, bottom padding
    results_label.pack(anchor='w', padx=5) # anchor west
    results_display_area.pack(expand=True, fill=tk.BOTH, padx=5, pady=(0,5)) # bottom padding

    root.mainloop()

if __name__ == "__main__":
    main_gui()
