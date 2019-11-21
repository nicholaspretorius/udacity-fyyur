## Fyyur

### Introduction

Fyyur is a musical venue and artist booking site that facilitates the discovery and bookings of shows between local performing artists and venues. This site lets you list new artists and venues, discover them, and list shows with artists as a venue owner.


### Instructions
-----

#### Pre-requisites

You need to have Git, Python3, pip3/pip and Postgresql already installed, setup and running on your local computer.

#### Code

You can checkout the project code from GitHub by: `git clone https://github.com/nicholaspretorius/udacity-fyyur.git`

Once the code is available, change into the project directory: `cd udacity-fyyur`

#### Database

To create the database, run: `createdb fyyur`

#### Project Setup

To run the app: 

* `python3 -m venv env` set the virtual environment for Pyhton // v3.7.4 for this example
* `source env/bin/activate` activate the venv
* `pip install -r requirements.txt` to install dependencies
* `export FLASK_ENV=development` to put app in debug mode [Optional]
* `python3 app.py` to run the app (http://127.0.0.1:5000/ or http://localhost:5000)
* Press Ctrl + C to quit the running app
* `deactivate` de-activate the venv when you are done
