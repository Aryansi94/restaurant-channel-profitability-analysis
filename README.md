# Restaurant Channel Profitability Analysis

## Project Overview
This project analyzes the cost structure and channel-wise profitability of multi-channel restaurants using Python and data analytics. It examines revenue, recorded net profit, profit margins, restaurant segments, cuisine types, and ordering channels to identify business opportunities and profitability risks.

## Objectives
- Analyze revenue and recorded net profit across ordering channels.
- Compare profitability across restaurant segments and cuisine types.
- Evaluate restaurant-level financial performance.
- Identify restaurants with negative aggregator profit and low overall margins.
- Examine estimated channel-wise costs.
- Present insights through an interactive Streamlit dashboard.

## Technologies Used
- Python
- Pandas and NumPy
- Matplotlib and Seaborn
- Plotly
- Streamlit

## Dashboard Features
- Interactive filters for restaurant segment, cuisine, and subregion.
- Key performance indicators for restaurants, monthly orders, revenue, profit, and overall profit margin.
- Channel-wise revenue and profit margin comparisons.
- Restaurant segment and cuisine profitability analysis.
- Searchable restaurant-level performance explorer.
- Aggregator risk analysis.
- Estimated channel cost structure.
- Downloadable analysis results.

## Dataset
The project uses the `SkyCity Auckland Restaurants & Bars.csv` dataset.

The dataset contains 1,696 restaurant records and 30 columns covering restaurant characteristics, ordering channels, revenue, costs, and profitability.

## Key Findings
- Total recorded revenue: approximately 77.74 million currency units.
- Total recorded net profit: approximately 7.87 million currency units.
- Overall recorded profit margin: approximately 10.12%.
- In-store profit margin: approximately 26.80%.
- Uber Eats profit margin: approximately 0.84%.
- DoorDash profit margin: approximately 0.90%.
- Self-delivery profit margin: approximately 22.89%.
- 538 restaurants have negative combined aggregator profit.
- 148 high-revenue restaurants have an overall profit margin below 5%.

**Note:** The dataset does not specify its currency. Estimated channel costs should be interpreted as estimates rather than independently verified accounting figures.

## Project Structure
```text
restaurant-channel-profitability-analysis/
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── SkyCity Auckland Restaurants & Bars.csv
└── project_outputs/
```

## Installation and Usage

### 1. Clone the repository
```bash
git clone https://github.com/Aryansi94/restaurant-channel-profitability-analysis.git
cd restaurant-channel-profitability-analysis
```

### 2. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Run the analysis
```bash
python main.py
```

### 4. Launch the dashboard
```bash
python -m streamlit run app.py
```

## Business Recommendations
- Review commission expenses and pricing for third-party delivery platforms.
- Investigate restaurants with negative aggregator profitability.
- Prioritize restaurants with high revenue but low profit margins.
- Compare performance by cuisine and restaurant segment before making operational decisions.
- Monitor delivery costs, operating expenses, and profitability regularly.

## Author
Aryan Singh

## License
No open-source license has been specified for this project.
