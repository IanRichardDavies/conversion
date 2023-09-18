"""
Python script to run Dash app from the command line
"""

# First Party Imports
from dash_app.director.director import Director

def main():
	director = Director()
	director.import_data()
	director.transform()
	director.visualize()

if __name__ == "__main__":
	main()