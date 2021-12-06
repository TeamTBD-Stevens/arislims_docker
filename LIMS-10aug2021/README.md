# arisLIMS

arisLIMS is an in-house inventory management system designed for dealing with sample documentation and tracking.

## Installation

### Setting up the database on Linux (Ubuntu)
1. Create containers

```bash
docker-compose up
```

2. While app is running, check to see if all 3 containers are running
```bash
docker container ls
```

3. Enter the mysql container and log into mysql
```bash
docker exec -it CONTAINER_ID bash
mysql -u root -p
```

4. Enter the following commands
```bash
GRANT ALL PRIVILEGES ON *.* TO 'lims_admin' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO 'root' WITH GRANT OPTION;
flush privileges;
exit
```

5. arisLIMS can now be accessed on localhost:8080 with username & password both set to 'admin'

## Usage
- Home tab and message board
- Logging in and creating admin/non-admin users
- Sample tab, changing metadata, flagging samples as low quality missing
- Using the csv file to change several samples at once
- missing sample management tab for samples that may be missing or may just be misplaced
- Updating sample database

## Download link
[Columbia](https://hub.docker.com/repository/docker/columbiacpmg/aris_lims)