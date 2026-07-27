# GEP Calculator

A web application for calculating **Gross Ecosystem Product (GEP)** — a monetary measure of the value ecosystems provide across four categories of services: **Provisioning**, **Regulating**, **Cultural**, and **Fauna**. The app supports manual, formula-based calculation as well as machine-learning-based prediction, and can export results as PDF or Excel reports.

## Features

- **Manual GEP Calculation** — Enter raw data (crop value, water quantity, carbon sequestration, tourism spend, etc.) across Provisioning, Regulating, Cultural, and Fauna categories, or use a combined estimation method. The app computes each component's value and the total GEP.
- **ML-Based Prediction** — A `RandomForestRegressor` trained on synthetic ecological data predicts Provisioning, Regulating, and Cultural values from basic inputs (area, population, forest %, wetland %, agricultural %).
- **Report Generation** — Export calculation results as a formatted PDF or Excel (`.xlsx`) report.
- **Wildlife Species Census** — Search and browse real species data (Mammals, Birds, Reptiles, Amphibians, Fish, Insects) live from the [GBIF](https://www.gbif.org/) taxonomic backbone API, with pagination.
- **AI Chatbot** — An optional assistant (via [Ollama](https://ollama.com/), running `llama3.2:3b` locally) that answers questions about GEP and ecosystem services.

## Project Structure

```
.
├── app.py                  # Flask application and API routes
├── model.py                 # ML model training, loading, and prediction logic
├── train_model.py           # Standalone script to (re)train the model
├── model.pkl                 # Trained RandomForestRegressor (generated)
├── scaler.pkl                # Fitted StandardScaler (generated)
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html            # Frontend UI (calculator, dashboard, chatbot)
└── utils/
    └── report_generator.py   # PDF/Excel report generation helpers
```

> **Note:** `templates/index.html` and `utils/report_generator.py` are imported by `app.py` but must be added to the repository structure above — they are referenced by the app but not included in this initial upload.

## Requirements

- Python 3.9+
- (Optional) [Ollama](https://ollama.com/) installed locally, with the `llama3.2:3b` model pulled, if you want the AI chatbot feature to work.

Install dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:

```
Flask==2.3.2
scikit-learn==1.3.0
pandas==2.0.3
numpy==1.24.3
joblib==1.3.1
reportlab==4.2.2
openpyxl==3.1.2
```

## Getting Started

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Train the model**

   A `model.pkl` and `scaler.pkl` are already included, but you can retrain them at any time on freshly generated synthetic data:

   ```bash
   python train_model.py
   ```

   If `model.pkl` / `scaler.pkl` are missing, `app.py` will train and save them automatically on first prediction request.

4. **Run the app**

   ```bash
   python app.py
   ```

   By default the server runs on `http://0.0.0.0:5000`. Configure the host, port, and debug mode with environment variables:

   | Variable      | Default   | Description                          |
   |---------------|-----------|---------------------------------------|
   | `HOST`        | `0.0.0.0` | Interface to bind to                   |
   | `PORT`        | `5000`    | Port to listen on                      |
   | `FLASK_DEBUG` | `0`       | Set to `1` to enable Flask debug mode  |
   | `OLLAMA_URL`  | `http://localhost:11434/api/chat` | Ollama endpoint for the chatbot |

5. Open your browser at `http://localhost:5000`.

## API Endpoints

| Method | Endpoint             | Description                                                        |
|--------|-----------------------|----------------------------------------------------------------------|
| GET    | `/`                    | Serves the main UI                                                    |
| POST   | `/api/calculate`       | Calculates GEP from manually entered inputs                          |
| POST   | `/api/predict`         | Predicts EPV/ERV/ECV from area, population, and land-use percentages |
| POST   | `/api/report`          | Generates and downloads a PDF report                                  |
| POST   | `/api/export-excel`    | Generates and downloads an Excel (`.xlsx`) report                     |
| GET    | `/api/species`         | Searches the GBIF species directory (supports `q`, `class`, `offset`, `limit` query params) |
| POST   | `/api/chat`            | Sends a message to the local Ollama-powered chatbot                   |

## Machine Learning Model

The prediction model is a `RandomForestRegressor` (100 estimators) trained on synthetic data generated in `model.py`. Features are scaled with a `StandardScaler` before training/inference.

- **Inputs:** `area_km2`, `population`, `forest_pct`, `wetland_pct`, `agri_pct`
- **Outputs:** `epv` (Provisioning value), `erv` (Regulating value), `ecv` (Cultural value)

Since the training data is synthetically generated, predictions are illustrative rather than empirically validated — swap in real regional data for production use.

## License

Add your preferred license here (e.g., MIT, Apache 2.0).

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.
