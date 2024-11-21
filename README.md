# 🔗 rival-microservice-connector

This is a library for common functionality in the python microservices.

If you want to test local changes without pushing them to github:
Just run ```pip install <<path-to-this-repo>>```

## Using a new version pushed to github
On every commit to main, a new git tag is made by github actions.

In this repository:
- ```git tag``` to list the tags

In the requirements.txt file of a micro service:
- update ```git+https://github.com/rival-xr/rival-microservice-connector.git@0.1.0``` to the new tag
