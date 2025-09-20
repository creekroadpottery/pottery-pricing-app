Pottery Cost Analysis App
A comprehensive web application built for potters to understand the true costs behind every piece of work. Calculate precise pricing from clay weight to firing costs, glaze recipes, labor, overhead, and shipping.
🎯 Purpose
This app was created to help potters make informed business decisions by accurately tracking all costs involved in pottery production. It transforms the complex task of pottery costing from guesswork into data-driven decision making.
Guided by gratitude, generosity, and empathy.

Gratitude for the teachers and makers who showed the way
Generosity in making this tool free for anyone who needs it
Empathy for potters balancing time, resources, and creativity

✨ Features
🏺 Quick Start

Get pricing in under 2 minutes
Pre-loaded form library (mugs, bowls, plates, etc.)
Smart defaults based on real pottery data
Confidence scoring for estimate reliability

📊 Comprehensive Cost Tracking

Clay & Materials: Bag pricing, yield calculations, packaging costs
Glaze Recipes: Material catalog, percentage-based recipes, batch calculators
Energy Costs: Electric, propane, natural gas, and wood firing support
Labor & Overhead: Hourly rates, studio expenses, monthly production
Other Materials: Project-specific items (handles, corks, hardware)

🔥 Production Planning

Timeline estimation for orders
Kiln loading calculations
Hands-on vs. process time breakdown
Delivery date forecasting

💰 Flexible Pricing Models

2x2x2 rule (materials → wholesale → retail → distributor)
Custom margin calculations
Regional pricing benchmarks

🚚 Shipping & International Trade

Domestic shipping calculator with dimensional weight
International shipping with tariffs, VAT, and customs fees
Multiple currency support

💾 Data Management

Save/load complete setups as JSON
Export/import form presets as CSV
Unified form database with clay, glaze, and timing data
Privacy-first: all data stays in your browser

🚀 Getting Started
Prerequisites

Python 3.8+
pip or conda package manager

Installation

Clone the repository

bash   git clone https://pottery-cost-analysis-app-e2dnvzfnfaqsu9hjnfvujd.streamlit.app/

Install dependencies

bash   pip install streamlit pandas

Run the application

bash   streamlit run staging_pottery_pricing_app.py

Open in browser

App will automatically open at http://localhost:8501
Or manually navigate to the URL shown in terminal



Quick Demo

Go to Quick Start tab
Select "Mug (12 oz)" from the form dropdown
Enter your clay bag cost and labor rate
See instant wholesale and retail pricing!

📱 Usage Guide
For New Users
Start with the Quick Start tab for immediate results, then explore other tabs for detailed control.
For Experienced Potters
Jump to Per Unit tab for complete cost customization and the Glaze Recipe tab for precise material costing.
Key Workflows
🎯 Single Piece Costing

Per Unit → choose form preset or enter custom data
Glaze Recipe → build your recipe and set grams per piece
Energy → configure your kiln costs
Pricing → set margins and see final prices

📦 Production Planning

Production Planning → select form and quantity
See timeline, kiln loads needed, and cost estimates
Apply settings to cost calculator for detailed breakdown

🌍 International Sales

Calculate base costs in main tabs
Shipping & Tariffs → add shipping and customs costs
Export complete cost breakdown

🏺 Form Preset Library
Includes 100+ pre-configured pottery forms with real-world data:

Functional pottery (mugs, bowls, plates)
Serving pieces (platters, casseroles, pitchers)
Decorative items (vases, planters, sculptures)
Bakeware and specialty forms

Each preset includes:

Clay weight (wet throwing weight)
Glaze amount (grams needed)
Production timing estimates
Kiln loading data

🔧 Technical Details

Framework: Streamlit (Python web framework)
Data: Pandas for data manipulation
Storage: Local JSON files (privacy-first approach)
Dependencies: Minimal - just Streamlit and Pandas
Deployment: Can run locally or deploy to Streamlit Cloud

🗺️ Roadmap
Phase 1: Core Stability ✅

Solid cost calculation engine
Form preset system
Save/load functionality

Phase 2: Practical Helpers 🔲

Enhanced shrink rate tools
PDF report exports
Expanded form library

Phase 3: User Experience 🔲

Mobile optimization
Improved visual design
Performance enhancements

Phase 4: Advanced Features 🔲

Project mode for whole firings
Collaborative preset sharing
Mobile app version

🤝 Contributing
Contributions are welcome! This project is built for the pottery community.
Ways to Help

Pottery Knowledge: Share your costing data, form specifications, regional pricing
Code: Bug fixes, feature improvements, performance optimization
Testing: Try the app with your pottery workflow and report issues
Documentation: Improve guides, add tutorials, translate content

Getting Started

Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Make your changes and test thoroughly
Commit with clear messages (git commit -m 'Add amazing feature')
Push to your branch (git push origin feature/amazing-feature)
Open a Pull Request

Code Style

Follow PEP 8 for Python code
Use meaningful variable names
Comment complex pottery calculations
Test with real pottery data when possible

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgments

Sharon - Mentor and source of the original form data
Al Wayman - Real-world pottery data and testing
The pottery community - Inspiration and feedback
Streamlit team - For making web apps accessible to non-web developers

📞 Contact
Alford Wayman
Artist and Owner
Creek Road Pottery LLC

GitHub: Your GitHub Profile
Website: [Your pottery website]
Email: [Your contact email]


🔒 Privacy
Your pottery data stays private:

All calculations happen in your browser
No data sent to external servers
Settings saved as local files only
Use offline after initial load

🆘 Support
Having trouble? Check these common solutions:
App won't start?

Ensure Python 3.8+ is installed
Try pip install --upgrade streamlit pandas
Check firewall settings for localhost:8501

Form presets not loading?

Check CSV file format matches expected columns
Ensure numeric fields contain valid numbers
Try the built-in fallback presets first

Calculations seem wrong?

Verify all input units (lb vs kg, hours vs minutes)
Check clay yield percentage (0.9 = 90% yield)
Confirm energy usage matches your actual kiln data

Need help with pottery-specific questions?

Consult with experienced potters in your area
Join online pottery communities for benchmarking
Start with conservative estimates and adjust based on experience


Built with ❤️ for the pottery community
