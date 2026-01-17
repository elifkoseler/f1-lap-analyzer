# 🏎️ F1 Lap Time Analyzer & Pit Stop Strategy Predictor

A full-stack application that analyzes Formula 1 lap times and predicts optimal pit stop strategies using machine learning.

![C#](https://img.shields.io/badge/C%23-239120?style=for-the-badge&logo=csharp&logoColor=white)
![.NET 8](https://img.shields.io/badge/.NET_8-512BD4?style=for-the-badge&logo=dotnet&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![OpenF1 API](https://img.shields.io/badge/OpenF1_API-E10600?style=for-the-badge&logo=f1&logoColor=white)

## 🌐 Live Demo

**[Try it live!](https://f1-lap-analyzer.vercel.app/)**

| Service | URL |
|---------|-----|
| Frontend | https://f1-lap-analyzer.vercel.app/ |
| API | https://f1-api-x7di.onrender.com |
| ML Service | https://f1-ml-service-zsno.onrender.com |

---

## ✨ Features

- **User-Friendly Race Selection** — Cascading Year → Race → Session dropdowns
- **Driver Standings** — Complete standings with clickable driver names (Google search)
- **ML-Powered Pit Stop Prediction** — Optimal pit window recommendations using machine learning
- **Interactive Tooltips** — Hover explanations for all metrics and predictions
- **Tabbed Interface** — Session Analysis, Pit Stop Predictor, Driver Comparison (coming soon)
- **Real-time F1 Data** — Live lap times and driver data from the OpenF1 API
- **Responsive Dark Theme** — F1-inspired styling that works on all devices

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | C# / .NET 8 Web API |
| **ML Service** | Python / FastAPI / scikit-learn |
| **Frontend** | HTML / CSS / JavaScript |
| **Data Source** | OpenF1 API |

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   C# API    │────▶│  Python ML  │
│  (HTML/JS)  │     │  (.NET 8)   │     │  (FastAPI)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ OpenF1 API  │
                   └─────────────┘
```

**Data Flow:**
1. Frontend selects Year → Race → Session via OpenF1 API
2. C# API fetches lap times and driver data from OpenF1
3. Analysis service calculates standings and gaps
4. For pit predictions, C# API calls Python ML service
5. ML service analyzes tire degradation and returns optimal pit window

## 📸 Screenshots

*Screenshots coming soon...*

## 🚀 How to Run

### Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- [Python 3.11](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/) (for frontend dev server)

### Step 1: Start the ML Service

```bash
cd ml-service
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --port 8000
```

The ML service will be available at `http://localhost:8000`

### Step 2: Start the C# API

```bash
cd src/F1LapAnalyzer.Api
dotnet run
```

The API will be available at `http://localhost:5109`

### Step 3: Start the Frontend

```bash
cd frontend
npx serve .
```

Open `http://localhost:3000` in your browser

### Quick Start Summary

| Service | Port | Command |
|---------|------|---------|
| ML Service | 8000 | `uvicorn main:app --port 8000` |
| C# API | 5109 | `dotnet run` |
| Frontend | 3000 | `npx serve .` |

## 📡 API Endpoints

### Drivers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/drivers/session/{sessionKey}` | Get all drivers in a session |

### Laps

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/laps/session/{sessionKey}` | Get all lap times for a session |
| GET | `/api/laps/session/{sessionKey}/driver/{driverNumber}` | Get lap times for a specific driver |
| GET | `/api/laps/session/{sessionKey}/fastest` | Get the fastest lap of the session |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analysis/session/{sessionKey}/summary` | Get full session summary with driver standings |

### Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prediction/pitstop/session/{sessionKey}/driver/{driverNumber}` | Get ML-powered pit stop prediction |

### Example Response

**GET** `/api/prediction/pitstop/session/9636/driver/1`

```json
{
  "optimal_pit_lap": 24,
  "windowStart": 22,
  "windowEnd": 26,
  "confidence": 0.78,
  "degradation_rate": 0.045,
  "recommendation": "Moderate tire degradation (0.045s/lap) - pit window around lap 24",
  "tire_compound": "MEDIUM",
  "laps_analyzed": 18
}
```

## 🤖 ML Model

The pit stop prediction model uses **linear regression** to analyze tire degradation patterns:

### How It Works

1. **Data Collection** — Gathers lap times for a driver's current stint
2. **Outlier Removal** — Filters out pit in/out laps and safety car periods
3. **Degradation Analysis** — Fits a linear regression model to `stint_lap` vs `lap_duration`
4. **Prediction** — Calculates when lap time will exceed acceptable threshold

### Key Metrics

| Metric | Description |
|--------|-------------|
| **Degradation Rate** | Seconds lost per lap (slope of regression) |
| **Optimal Pit Lap** | When degradation exceeds 2.0s threshold |
| **Confidence** | R² score adjusted for degradation reasonableness |
| **Pit Window** | ±2 laps around optimal pit lap |

### Model Validation

- Typical F1 degradation: 0.01 - 0.10 s/lap
- High confidence (>70%): Consistent lap times, clear trend
- Medium confidence (40-70%): Some variability in data
- Low confidence (<40%): Inconsistent data or unusual conditions

## 🗂️ Project Structure

```
f1-lap-analyzer/
├── src/
│   ├── F1LapAnalyzer.Api/           # ASP.NET Core Web API
│   │   ├── Controllers/
│   │   │   ├── AnalysisController.cs
│   │   │   ├── DriversController.cs
│   │   │   ├── LapsController.cs
│   │   │   └── PredictionController.cs
│   │   └── Program.cs
│   │
│   └── F1LapAnalyzer.Core/          # Core library
│       ├── Models/
│       │   ├── Driver.cs
│       │   ├── LapTime.cs
│       │   ├── PitStopPrediction.cs
│       │   └── SessionSummary.cs
│       └── Services/
│           ├── ILapAnalysisService.cs
│           ├── IOpenF1Service.cs
│           ├── IPitStopPredictionService.cs
│           ├── LapAnalysisService.cs
│           ├── OpenF1Service.cs
│           └── PitStopPredictionService.cs
│
├── ml-service/                       # Python ML Service
│   ├── main.py                       # FastAPI application
│   ├── model.py                      # TireDegradationModel
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                         # Web Frontend
│   ├── index.html
│   └── package.json
│
├── F1LapAnalyzer.sln
└── README.md
```

## 🔮 Future Improvements

- **Kubernetes Deployment** — Container orchestration for scalable cloud deployment
- **Real-time WebSocket Updates** — Live lap time streaming during sessions
- **Historical Race Comparisons** — Compare driver performance across multiple races
- **Weather Impact Analysis** — Factor weather conditions into predictions
- **Multi-Stint Strategy Optimization** — Plan complete race strategy with multiple stops
- **Driver Comparison Tool** — Head-to-head performance analysis

## 🙏 Acknowledgments

- [OpenF1 API](https://openf1.org/) — Free, open-source Formula 1 data API
- [scikit-learn](https://scikit-learn.org/) — Machine learning library for Python
- Formula 1® — For the exciting sport that inspires this project

## 📄 License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Made with ❤️ for F1 fans
</p>
