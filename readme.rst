This is an advanced poll app project to learn about Class Based Views and Testing

Installation
$ virtualenv /path/virtualenv/polls
$ source /path/virtualenv/polls/bin/activate
$ pip install -r requirements.txt
$ python manage.py syncdb
$ python manage.py runserver
#link

Running Tests
coverage run --source='.' manage.py test polls
coverage html
open htmlcov/index.html in a browser to see coverage

Test are located in polls/test.py
