# Process data PDF into markdown

## Introduction

This project requires a specific folder structure for data organization. Since data folders are not pushed to GitHub, you'll need to set up the data structure manually.

## Data Organization

Create the following folder structure in the project root:

```
data/
├── raw/       # Place your raw data files here
├── processed/ # Processed data will be stored here
└── output/    # Output files will be stored here
```

**Note:** The `data/` directory is excluded from version control via `.gitignore` to avoid pushing large data files to GitHub.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <project-directory>
   ```

2. Create the data folder structure:
   ```
   mkdir -p data/raw data/processed data/output
   ```

3. Place your raw data files in the `data/raw/` directory.

## Running the Application

1. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Edit the `run.sh` script to include your actual application execution command.

3. Run using the shell script:
   ```
   chmod +x run.sh
   ./run.sh
   ```

## Shell Script

The `run.sh` file is provided for convenience. It automates the process of running the application and checks if your data folders are set up correctly. Before using it:

1. Open the file and replace the placeholder with your actual command to run the application
2. Make it executable:
   ```
   chmod +x run.sh
   ```

## Additional Notes

- Make sure your data files follow the expected format
- Check the logs in the console for any errors during execution
- Output files will be saved to the `data/output/` directory
