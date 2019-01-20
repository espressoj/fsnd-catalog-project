# Catalog Web Site (Python)
This python application displays a database-drive website catalog using SQLite, Flask, and SQLAlchemy.  The project is a part of the Udacity.com Full Stack Web Developer Nanodegree program. The site integrates CRUD functionality, Google Sign-in for authentication, a database Users table where the Google sign-in process inserts new users, through which the logged in users receive authorization, and API endpoints for all pages listing catalog information from the database.

## Requirements
This is a python program and thus, you will need a python interpreter.  For more information, head on over to [https://www.python.org/about/](https://www.python.org/about/). The **Catalog Web Site** program has been tested in the following Python versions:
* 2.7.12
* 3.5.2

The following library(ies) must be installed to run the program.
* datetime
* flask
* httplib2
* logging
* json
* models
* oauth2client.client
* os
* random
* requests
* sqlalchemy
* sqlalchemy.orm
* string
* sys

**Library(ies) for Python2 install code**
```
pip install _library_name_
```
**Library(ies) for Python3 install code**
```
pip3 install _library_name_
```
**Note:**  *If installing the library(ies) on a virtual machine, you may need to include `--user` at the end of the pip/pip3 line(s) above.*

## Directions
1. From a console program use the following code to start the web server and run the web site.
$  ```python views.py``` or $  ```python3 views.py``` _(depending on the version of Python you want to use.)_
2. Open a web browser and go to http://localhost:5000.
3. If you would like to log in, click the log in button and use a Google account with the sign-in.
4. When logged in, add, edit, or delete any items of your own. _(You cannot modify any items except those you own.)_
5. The application also generates a log file in the same folder called "PythonLogs_Catalog.txt."


## Database Views
No views have been created for this application.

## License
[MIT License](https://opensource.org/licenses/MIT, "MIT License")
