# Crop Yield Prediction using Satellite Imaging and Climatic Conditions  

This project focuses on predicting crop yield based on climatic conditions, soil data, and satellite imaging parameters (NDVI) using machine learning models.  
Data was collected from Google Earth Engine (GEE) and publicly available datasets from 2019 to 2023.  

---

## Tech Stack  

- Python 3.x  
- Pandas  
- NumPy  
- Scikit-Learn  
- Ridge Regression  
- Matplotlib & Seaborn (for Visualization)  
- Google Earth Engine (Data Collection)

---

## Project Structure  

Crop-Yield-Prediction/ │ ├── plots/ # Output plots generated
│
├── 2024_params.csv # Climate parameters for prediction
├── crop_yield_climate_soil_data_2019_2023.csv # Main dataset
├── predict_crop_yield.py # Main Python model script
├── requirements.txt # Python dependencies
├── GEE_Chattisgarph.txt # Notes / Info from GEE data
└── README.md # Project Overview (this file)


---

## How to Run  

Clone the repo:

```bash
git clone https://github.com/Kevinbose/Crop-Yield-Prediction.git
cd Crop-Yield-Prediction

Install dependencies:
pip install -r requirements.txt

Run the model:
python predict_crop_yield.py


Sample Output
Plots generated will be saved in the plots/ folder.

Examples:

    -NDVI Trend Visualization

    -Predicted vs Actual Crop Yield

    -Feature Importance

DatasetSource
Data                Type	        Source
Climate & Soil      Data	        Google Earth Engine (MODIS, ERA5)
NDVI                Data	        MODIS NDVI Dataset
Crop                Yield Data	    Government Open Data Portals

License
This project is licensed under the MIT License - see the LICENSE file for details.

Author
Kevin Bose