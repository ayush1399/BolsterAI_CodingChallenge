# BolsterAI_CodingChallenge

To run the API we need Postgres and rabbitmq installed locally. They can be installed on a mac using brew:

```
brew install postgresql

brew install rabbitmq
```

By default, homebrew creates a database by the name of 'postgres' and a user with the current system user in the postgress installation.
We need to update the DB config accordingly in consumer.py lines 11-17

Next, we need to create a new environment using `conda env create -f environment.yml`

Once the environment has been created and **activated**, we need to run `playwright install`

Now, we are ready to run the application.
To start the consumer process simply run, `python consumer.py`
To start the api `uvicorn server:app --reload`

E.g. call to the api using curl:

```
curl -X POST "http://localhost:8000/scan_url" \
     -H "Content-Type: application/json" \
     -d "{\"url\":\"https://www.google.com\"}"
```
