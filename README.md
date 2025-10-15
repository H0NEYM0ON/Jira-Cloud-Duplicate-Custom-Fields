# 🛠️ Jira-Cloud-Duplicate-Custom-Fields - Easily Compare Custom Fields from Jira

[![Download](https://img.shields.io/badge/Download-v1.0-brightgreen)](https://github.com/H0NEYM0ON/Jira-Cloud-Duplicate-Custom-Fields/releases)

## 🚀 Getting Started

Welcome to the Jira-Cloud-Duplicate-Custom-Fields repository! This script helps you compare custom fields between two Jira Cloud sites. You can quickly see which fields are active and not trashed. 

## 📋 Features

- Fetches active custom fields from two Jira Cloud sites.
- Generates individual CSV files for each site.
- Creates a comparison CSV file by field name.
- Easy to use with no programming required.

## 📥 Download & Install

To get started, visit the [Releases page](https://github.com/H0NEYM0ON/Jira-Cloud-Duplicate-Custom-Fields/releases) to download the application.

1. Click on the link above to access the Releases page.
2. Locate the latest release version.
3. Download the appropriate file for your system.

## ⚙️ System Requirements

- Windows, macOS, or Linux.
- Python 3.x installed on your system.
- Access to the internet to connect to Jira Cloud sites.
  
## 📖 How to Run the Script

1. **Download the Script:**
   - Visit this [Releases page](https://github.com/H0NEYM0ON/Jira-Cloud-Duplicate-Custom-Fields/releases) and download the latest version.

2. **Install Python:**
   - Download and install Python from [python.org](https://www.python.org/downloads/).
   - During the installation, check the box to add Python to your PATH.

3. **Open Your Terminal or Command Prompt:**
   - For Windows, open Command Prompt.
   - For macOS or Linux, open Terminal.

4. **Navigate to the Script Location:**
   - Use the command `cd path-to-your-download-folder` to go to the folder where you saved the script.

5. **Run the Script:**
   - Type `python script_name.py` and press Enter. Replace `script_name.py` with the actual file name.

6. **Follow the Prompts:**
   - The script will ask you for necessary details like your Jira Cloud URLs and authentication. Follow the instructions displayed on the screen.

## 🔍 Understanding the Output

- After running the script, you will find three CSV files in the same folder:
  - `site1_custom_fields.csv`: Custom fields from the first site.
  - `site2_custom_fields.csv`: Custom fields from the second site.
  - `comparison.csv`: A comparison of custom fields between the two sites.

## 📂 Folder Structure

When you download the application, you will have a folder that contains:

```
/Jira-Cloud-Duplicate-Custom-Fields
    ├── script_name.py
    ├── requirements.txt
    └── README.md
```

## 🔧 Troubleshooting

If you encounter any issues:

- Ensure you have a stable internet connection.
- Make sure your Python installation is functioning properly.
- Check the Jira URL and authentication credentials.

## 🌐 Community and Support

Feel free to reach out to others using this script or share your own experiences. Support can be obtained through the issues section of this repository.

## 📅 Upcoming Features

- User interface for easier operation.
- Enhanced error handling.
- Ability to filter fields based on criteria.

Thank you for using Jira-Cloud-Duplicate-Custom-Fields!