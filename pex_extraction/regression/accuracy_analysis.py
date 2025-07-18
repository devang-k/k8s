import pandas as pd
import matplotlib.pyplot as plt
import os
from sklearn.metrics import r2_score, mean_absolute_error

# Define the directories
ground_truth_dir = 'ground_truth_sample'
prediction_dir = 'prediction_sample'

# Iterate over the ground truth files
for gt_file in os.listdir(ground_truth_dir):
    if gt_file.endswith('.csv'):
        # Extract cell type from the ground truth file name
        cell_type = gt_file.split('_')[0]
        
        # Construct the corresponding prediction file name
        pred_file = f"{cell_type}_GDS_PEX_PREDICTION_ML.csv"
        
        # Check if the prediction file exists
        pred_file_path = os.path.join(prediction_dir, pred_file)
        if not os.path.exists(pred_file_path):
            print(f"Prediction file for {cell_type} does not exist. Skipping...")
            continue
        
        # Load the ground truth and prediction data
        gt_data = pd.read_csv(os.path.join(ground_truth_dir, gt_file))
        pred_data = pd.read_csv(pred_file_path)
        
        # Match columns considering A_to_B is the same as B_to_A
        gt_columns = set(gt_data.columns)
        pred_columns = set(pred_data.columns)
    
        # Create a mapping for column names
        def simplify_node_name(node_name):
            return node_name.replace('_', '').replace('#', '')

        column_mapping = {}
        for col in pred_columns:
            simplified_col = '_to_'.join([simplify_node_name(node) for node in col.split('_to_')])

            if simplified_col in gt_columns:
                column_mapping[col] = simplified_col
            else:
                # Check for reverse match
                reverse_col = '_to_'.join(simplified_col.split('_to_')[::-1])
                if reverse_col in gt_columns:
                    column_mapping[col] = reverse_col

        # Rename prediction dataframe columns to match ground truth
        pred_data_filtered = pred_data.rename(columns=column_mapping)

        # Filter and align the data
        gt_data_filtered = gt_data[list(column_mapping.values())]
        pred_data_filtered = pred_data_filtered[list(column_mapping.values())]
        
        # Assuming there is a column 'File' in both dataframes that identifies the files
        common_files = set(gt_data['File']).intersection(set(pred_data['File']))
        
        # Filter both dataframes to only include rows with common files
        gt_data_filtered = gt_data[gt_data['File'].isin(common_files)]
        pred_data_filtered = pred_data_filtered[pred_data_filtered['File'].isin(common_files)]
        
        # Align columns based on the mapping
        gt_data_filtered = gt_data_filtered[list(column_mapping.values())]
        pred_data_filtered = pred_data_filtered[list(column_mapping.values())]
        
        # Calculate differences
        differences = gt_data_filtered.drop(columns=['File']) - pred_data_filtered.drop(columns=['File'])

        # Calculate R² score and MAE
        r2_scores = {}
        mae_scores = {}
        for col in gt_data_filtered.columns:
            if col != 'File':  # Ensure 'File' column is not included
                r2_scores[col] = r2_score(pred_data_filtered[col],gt_data_filtered[col])
                mae_scores[col] = mean_absolute_error(gt_data_filtered[col], pred_data_filtered[col])
        print(f"Cell Type: {cell_type}")
        # Print R² scores and MAE
        print("R² Scores:")
        for col, score in r2_scores.items():
            print(f"{col}: {score}")

        print("Mean Absolute Error (MAE):")
        for col, score in mae_scores.items():
            print(f"{col}: {score}")
        print('\n')
        # Plotting
        plt.figure(figsize=(10, 6))
        for i, col in enumerate(gt_data_filtered.columns):
            if col != 'File':
                plt.scatter(range(len(gt_data_filtered)), gt_data_filtered[col], color='red', label='Ground Truth' if i == 0 else "")
                plt.scatter(range(len(pred_data_filtered)), pred_data_filtered[col], color='blue', label='Prediction' if i == 0 else "")

        plt.title(f'Ground Truth vs Prediction for {cell_type}')
        plt.xlabel('File Index')
        plt.ylabel('Values')
        plt.legend()
        plt.savefig(f'pex_extraction/regression/accuracy_analysis_plots/{cell_type}_ground_truth_vs_prediction.png')
        plt.close()
        gt_data_filtered.to_csv(f'pex_extraction/regression/accuracy_analysis_plots/{cell_type}_ground_truth.csv', index=False)
        pred_data_filtered.to_csv(f'pex_extraction/regression/accuracy_analysis_plots/{cell_type}_prediction.csv', index=False)
        differences.to_csv(f'pex_extraction/regression/accuracy_analysis_plots/{cell_type}_differences.csv', index=False)
