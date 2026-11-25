
# [Project Name]: Health and Wellness App

## Team
- Name (GitHub: @username):
| Name | GitHub | Email |
|------|--------|-------|
| Armita Asghari | Armitaasghariardebili-stack | Armita.asghariardebili@sjsu.edu |
| Xuan Phuong Nguyen | xuanphuong2901 | xuanphuong.nguyen@sjsu.edu |
| Darren Vu | darrenvu2 | darren.vu@sjsu.edu |
| Michael Kim | michaelnathykim | Michael.n.kim@sjsu.edu|


## Project Description
## Problem Statement
Many people with chronic health issues are urged to change their lives, but have a hard time keeping up with good behaviors when they’re also trying to balance job, family, finances and medical demands. Current nutrition apps frequently involve manual food logging, and users may have trouble comprehending nutritional information, or receiving suggestions that meet their requirements. Our initiative is about making nutrition monitoring simple and providing digestible information to encourage healthy choices in daily life.


## Solution
Our Health and Wellness App is built on 6 pillars of Lifestyle Medicine, which are Diet, Physical Exercise, Sleep, Stress Management, Social Connection, and avoiding harmful medicines. Firstly, we include a nutrition section where users can search for goods, read nutrition information and calculate nutrients depending on portion size. Future studies will include photo-assisted meal journaling, Healthy Eating Index (HEI-2020) scoring and personalized nutrition coaching.

## Proof of Concept Scope
What the PoC demonstrates, which technical risk it addresses,
and what is intentionally not included yet.

- The PoC demonstrates the integration of a React Native frontend, Python FastAPI backend, and USDA FoodData Central API to search for foods, get nutritional information, and compute nutrients according to portion sizes. We also implemented some simple meal recording endpoints. The key technological issues include obtaining reliable food data, calculating nutrients based on portion sizes and processing the data for future HEI-2020 rating. Food recognition from images, HEI-2020 rating, individualized nutrition advice, and permanent meal storage are not yet implemented and are subject to future development.


## System Architecture: 
(docs/architecture.png)
Major components and how they communicate. A diagram is encouraged.
Our Health and Wellness App is built using React Native and Expo on the front end and Python FastAPI on the back end. The backend communicates with the USDA FoodData Central API to search for foods, obtain nutritional data, and perform calculations of nutrients based on serving sizes. The system that’s being designed will employ Gemini Vision to recognize meals from images. After users confirm meals and quantities, FastAPI matches foods to FNDDS and FPED data to prepare for HEI-2020 scoring. User profiles, Meals, & Scores will be stored in Supabase & PostgreSQL. Recommendation module will provide tailored nutritional advice. The current PoC provides food search, nutrition retrieval, portion calculations and basic meal tracking endpoints. Other components are expected to be developed in the future.



## Prerequisites
- Python 3 (compatible with the project's dependencies)
- Node.js and npm (compatible with the Expo project)
- Git
- USDA FoodData Central API key

## Installation
- Clone the GitHub repository:
git clone https://github.com/SJSU-CMPE-195/FA26-CMPE-195A_sr-project-Group-34-Michael-Fu.git
cd FA26-CMPE-195A_sr-project-Group-34-Michael-Fu
- Install the Python backend dependencies:
python3 -m pip install -r requirements.txt
Install the React Native/Expo frontend dependencies:
cd src
npm install
cd ..
- export FDC_API_KEY="mNRgFQTbpTPDNwWp8dKd9gMkzwLkmtqhFq7WdcmP"
## Running the PoC
1. Start the FastAPI backend
Open a terminal in the project root directory and run:
export FDC_API_KEY="mNRgFQTbpTPDNwWp8dKd9gMkzwLkmtqhFq7WdcmP"
python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000
Open the API documentation:
http://127.0.0.1:8000/docs
2. Start the React Native frontend
Open a second terminal in the project root directory and run:
cd src
npm run start -- --web
Open the application:
http://localhost:8081
3. Test the PoC
- Search for a food such as broccoli or salmon in the frontend.
- Select a food to view its nutritional information per 100 g.
- Use the FastAPI documentation to test portion-based nutrition calculations.
- Test the meal logging endpoints (GET, POST, PUT, DELETE) using Swagger UI.

## Testing
- Automated Testing
Run the backend API tests from the project root directory:
python3 -m pytest tests/test_api.py
- Manual Testing
+ Food Search: Search for foods such as broccoli or salmon in the React Native frontend.
+ Nutrition Data: Verify that calories, protein, carbohydrates, fat, fiber, and sodium are displayed.
+ Portion Calculation: Use Swagger UI to test nutrition calculations for different serving sizes.
+ Meal Logging: Test GET, POST, PUT, and DELETE endpoints using Swagger UI.
+ Frontend Integration: Confirm that the frontend successfully retrieves food data from the FastAPI backend.


## Demo
Screenshots, GIFs, logs and/or video link.

## Technical Stack
- Frontend: React Native, Expo, Expo Router, JavaScript/TypeScript.
- Backend: Python, FastAPI, Uvicorn.
- APIs and Data: USDA FoodData Central API for food searches and nutritional information.
- Testing: Pytest and FastAPI Swagger UI.
- Development Tools: Visual Studio Code, Git, GitHub, Node.js, npm.
- Hardware: Computer for development; smartphone camera planned for food identification.
# Planned Technologies:
- Gemini Vision API: Identify foods and estimate portions from images.
- FNDDS and FPED: Match food codes and retrieve food-group equivalents for nutrition scoring.
- HEI-2020: Calculate nutrition quality scores.
- Supabase and PostgreSQL: Manage user accounts and permanently store meal records.
- Hosted AI Model: Provide food identification without training a custom model using Food-101 or Nutrition5k.
## What's Next (195B)
Goals for Full Implementation
1. For at least 24 of the 30 new test photos (80%) prior to corrections, estimate the grams within 20% of the actual weighed portions. Use single foods, overhead photos, consistent lighting and a known size plate. This does not establish accuracy for unrestricted meal photos.
2. Return at least one eligible recipe for each of the 20 fictional profiles, with no violations of their listed ingredient exclusions. Use a fixed recipe list with complete ingredient information. Check that five additional recipes with incomplete ingredient information are excluded from allergy-filtered results. This test does not establish cross-contact safety.
3. HEI totals should be calculated within 1 point of independent references for at least 18 of the 20 new verified intake records (90%). The same confirmed inputs and source versions must be used for both calculations.
4. With 5 consenting adult volunteers using fictitious profiles, at least 4 complete the logging without assistance and correctly state both the score and one of the limitations. Median logging time must be at least 20% less than the time it would take to manually enter the same meals; alternate task order.
5. Block all 10 attempts by a second test account to read or change another account's records. Verify that deletion of a fictional profile results in the removal of its associated personal records in accordance with the deletion policy.



