# 🔗 rival-microservice-connector

This is a library for common functionality in the python microservices.

If you want to test local changes without pushing them to github:
Just run ```pip install <<path-to-this-repo>>```

## Using a new version in the micro services
In this repository:
- ```git tag`` to list the tags
- ```git tag vx.y.z``` to create a tag, where  vx.y.z is the next tag
- ```git push --tags```

In the requirements.txt file of a micro service:
- update ```git+https://github.com/rival-xr/rival-microservice-connector.git@v0.26.0``` to the new tag