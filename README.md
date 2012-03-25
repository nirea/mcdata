mcdata
=====

This is an http server for storing and retrieving myCollar settings, using
MongoDB for storage.

Setup
=====

mcdata can run on any server or hosting environment where you can run python
and access MongoDB.

Ubuntu
------ 

Assuming you're running Ubuntu Linux, here are the steps to take to get
running:

    # Install MongoDB
    sudo apt-get install mongodb

    # Install python-virtualenv, for putting Python packages into isolated
    # environments
    sudo apt-get install python-virtualenv

    # clone the mcdata repo.  Assumes you have git installed.
    git clone https://github.com/nirea/mcdata.git 
    cd mcdata

    # Create a new virtualenv, enter it, and install the dependencies
    virtualenv --no-site-packages env
    source env/bin/activate
    pip install -r requirements.txt

    # Run the program.  Will start on port 5000 by default.  Requires the
    # MCDATA_SUPERUSER environment variable
    MCDATA_SUPERUSER="some av key" python app.py

    # Or run with gunicorn, which lets you start multiple workers.
    MCDATA_SUPERUSER="some av key" gunicorn app:app -w 2 -b 0.0.0.0:5000

(Those steps were tested on Oneiric Ocelot, but ought to work all the way back
to Lucid Lynx.)

Heroku
------

mcdata runs nicely on Heroku with the MongoLab addon.  You must have a Heroku
account, and the Heroku Toolbelt installed.  Heroku has [good instructions](http://devcenter.heroku.com/articles/quickstart).

Once your account is created and the toolbelt installed, follow these steps:

    # clone the mcdata repo.
    git clone https://github.com/nirea/mcdata.git 

    # Create a Heroku remote
    cd mcdata
    heroku create --stack cedar  

You should see output like this:

    Creating falling-wind-1624... done, stack is cedar
    http://falling-wind-1624.herokuapp.com/ | git@heroku.com:falling-wind-1624.git
    Git remote heroku added

The app name there is 'falling-wind-1624'.  Yours will be different.  You'll
need to use it in the next command to finish your git configuration.

    git remote add heroku git@heroku.com:<appname>.git

Just replace <appname> with the name given during the 'heroku create' step
above.

Set the MCDATA_SUPERUSER environment variable to your av key.

    heroku config:add MCDATA_SUPERUSER="some av key"

You probably want to use the [MongoLab
addon](http://devcenter.heroku.com/articles/mongolab), which has a free
"starter" tier that gives you 256MB of storage .  IMPORTANT: You'll need to
[verify your Heroku
account](http://devcenter.heroku.com/articles/account-verification) before
typing this next step.

    heroku addons:add mongolab:starter

You're now ready to push the code to Heroku.

    git push heroku master 

And start up your process

    heroku scale web=1 
