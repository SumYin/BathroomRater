# Bathroom Rating App

A Flask web application that allows users to rate and review bathrooms, share their experiences, and help others find the best restrooms.

## Features

- User authentication (register/login)
- Rate bathrooms with detailed criteria:
  - Cleanliness
  - Privacy
  - Accessibility
  - Amenities
  - Overall rating
- Social features:
  - Share ratings
  - Favorite ratings
  - User profiles
- Modern, responsive UI
- Landing page with statistics

## Setup

1. Clone the repository:
```bash
git clone https://github.com/SumYin/BathroomRater.git
cd BathroomRater
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Technologies Used

- Flask
- SQLAlchemy
- Bootstrap 5
- SQLite

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 