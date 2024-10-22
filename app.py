from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import io
import os
import base64
import csv
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

# Configuring the database connection using DATABASE_URL from Heroku
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')  # Fallback to SQLite for local testing
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the model for storing search logs
class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Function for logging the search to the database
def log_search(name):
    new_search = SearchLog(name=name)
    db.session.add(new_search)
    db.session.commit()

# Function to get the evolution of a given French first name and return the plot as a base64 image
def plot_name_evolution(name: str, csv_file: str = 'french_first_names.csv'):
    # Load the data
    df = pd.read_csv(csv_file, sep=';')
    
    # Filter the dataframe for the given name
    name_data = df[df['name'].str.lower() == name.lower()]
    
    if name_data.empty:
        return None
    
    # Sort the data by year for correct plotting
    name_data = name_data.sort_values(by='year')

    # Create the plot
    plt.figure(figsize=(8, 6))
    plt.plot(name_data['year'], name_data['count'], marker='o', linestyle='-', color='b', label=name)
    
    # Add title and labels
    plt.xlabel('Année')
    plt.ylabel('Nombre')
    
    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    
    # Convert the image to base64 so it can be embedded in HTML
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        name = request.form['name']
        log_search(name)  # Enregistrer le prénom recherché
        return redirect(url_for('show_plot', name=name))
    return render_template('index.html')

# Route to display the plot
@app.route('/plot/<name>')
def show_plot(name):
    plot_url = plot_name_evolution(name)
    if plot_url is None:
        return f"No data found for the name: {name.capitalize()}"
    return render_template('plot.html', name=name.capitalize(), plot_url=plot_url)

if __name__ == '__main__':
    app.run(debug=True)

