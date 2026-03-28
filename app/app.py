import os
import sys
from Flask import Flask, render_template, request, redirect, url_for

# Application class that sets up a Flask web application with routes for the index page and a submit action. It also includes a main method to run the application.
class App:
    def __init__(self):
        self.app = Flask(__name__)

        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/submit', methods=['POST'])
        def submit():
            data = request.form['data']
            print(data)
            return redirect(url_for('index'))

    def run(self):
        self.app.run(debug=True)

    def main(self):
        self.run()

    def __main__(self):
        pass

# Main class that initializes the App class and calls its main method to start the application.
class Main:
    def __init__(self):
        self.app = App()

    def main(self):
        self.app.main()