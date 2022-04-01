# RAINA - Realtime Artificial Intelligent Nutrition Assistant

For information on the functionality of the latest version of RAINA, take a look at the `INFO.md`.

The folder structure in this repository must not be changed if you want to connect it to a RasaX instance, since RasaX
expects the folders to be in the top level of the connected repository (i.e. the structure created by the rasa init
command when creating a new assistant).

The image of the nutrition pyramid was retrieved from:  
https://www.bzfe.de/ernaehrung/die-ernaehrungspyramide/die-ernaehrungspyramide-eine-fuer-alle/

## Prerequisites for further development

### Local Development Setup

1. Anaconda installed
2. Docker and Docker Compose installed
3. Python 3.8.8 installed
4. NGROK installed
5. Owning an AWS S3 bucket and/or having access to the following credentials:  
   `AWS_ACCESS_KEY_ID`  
   `AWS_SECRET_ACCESS_KEY`  
   `AWS_BUCKET_NAME`  
   `AWS_BUCKET_URL`  
   *(The bucket needs to be publicly accessible!)*
6. Owning a Telegram Bot and having the following credentials:  
   `access_token`  
   `verify`

### RasaX Deployment

1. Linux VM hosted on a Server (e.g. DigitalOcean)
2. Domain for your server
3. Additional Telegram Bot

## Image display in chat interfaces

- Telegram and RasaX need public accessible image links
- generated images are uploaded to an AWS S3 bucket
- the link is sent via the chatbot
- the image can be rendered by telegram/rasaX
- access keys need to be specified in env vars of the action server
- env vars needed are:  
  `AWS_ACCESS_KEY_ID`  
  `AWS_SECRET_ACCESS_KEY`  
  `AWS_BUCKET_NAME`  
  `AWS_BUCKET_URL`
- contact anton.steuer@tum.de to get access keys or create an own AWS S3 bucket
- if using your own S3 bucket: set it to be publicly accessible!

## Local Development Setup

Prerequisites: you cloned the repository and have Anaconda, Python 3.8.8 and Docker Installed on your system. The
commands are executed in the top level of the cloned repository, if not specified otherwise.

### [Local Setup] Creating a Conda Environment

Make sure that the `Microsoft Visual C++ Build Tools` is installed on your system, otherwise the installation will
fail!   
The following commands have to be executed in the Anaconda Prompt:

1. create a new conda environment using python 3.8.8  
   `conda create --name <your env name> python==3.8.8`
2. activate the new conda environment  
   `conda activate <your env name>`
3. install UJSON  
   `conda install ujson`
4. install tensorflow  
   `conda install tensorflow`
5. install Rasa (for the thesis Rasa 2.8.13 has been used)  
   `pip install rasa`
6. validate install  
   `rasa -h`  
   (Source: https://www.youtube.com/watch?v=GlR60CvTh8A)

**Warning:**  
*Rasa 2.x is not compatible with Rasa 3.x out of the box! For migrating this project to Rasa 3.x take a look at:
https://rasa.com/docs/rasa/migration-guide*

### [Local Setup] Testing RAINA in an IDE

The IDE used for development was PyCharm. For testing the s3_client.py file, the environment variables were copied in
the environment variables of the run config for the s3_client.py.

WARNING: this local instance of the action server is not using the environment variables specified in PyCharm! Uncomment
and adjust the functions using the S3 bucket in the actions.py for local testing! The images will still be saved in the
backlog folder!

1. activate your conda environment  
   `conda activate <your env name>`
2. make sure to select the python version of your virtual environment as project interpreter
3. open four terminals in the folder 'raina'
4. [Terminal 1] run the rasa action server  
   `rasa run actions`
5. [Terminal 2] create a rasa shell to talk to RAINA  
   `rasa shell`
6. [Terminal 3] start duckling docker container  
   `docker run -p 8000:8000 rasa/duckling`
7. [Terminal 4] get container ID of duckling container using  
   `docker ps`
8. [Terminal 4] stop duckling container  
   `docker stop <container ID>`
9. [Terminal 2] stop RAINA in the chat  
   `/stop`
10. [Terminal 1] stop action server  
    `STRG + C`

### [Local Setup] Creating a Docker Image of the Action Server

For using the custom action server, a docker image can be created. Make sure docker is installed on your system, and you
have a docker-hub account!

1. activate your conda environment  
   `conda activate <your env name>`
2. install pipreqs for requirement file generation  
   `pip install pipreqs`
3. to generate a new requirements.txt file (only if you have imported additional libraries) use  
   `pipreqs .\actions\ --force`  
   (**Warning:** *Due to rasa3.x already being released versions might have to be downgraded according to docker
   instructions in the terminal!*)
4. build a new docker image  
   `docker build . -t <account_username>/<repository_name>:<custom_image_tag>`
5. log into your docker-hub account  
   `docker login --username <account_username> --password <account_password>`
6. push docker image to your DockerHub  
   `docker push <account_username>/<repository_name>:<custom_image_tag>`  
   (Source: https://rasa.com/docs/rasa/how-to-deploy/)

### [Local Setup] RAINA test setup using docker-compose

If you want to test RAINA locally you can use the docker-compose file. It will start a rasa service, a duckling service
and the custom action server specified in the docker-image provided in the docker-compose file.

**Warning:**
*Do not push any of the changes in the `config.yml` and `credentials.yml` to the git repository if you have it connected
to a deployed RasaX instance! These changes are for local use only!*

1. build a local docker image of the action server using, which will be used in the `docker-compose.yml`:  
   `docker build . -t action-server-local`
2. in the `credentials.yml` make sure that in the endpoints.yml the action endpoint is set to:  
   `url: http://app:5055/webhook`
3. in the `config.yml` make sure the Duckling Component uses:  
   `url: "http://duckling:8000"`
4. use NGROK to expose port 5005 (on which RAINA will be running):  
   `ngrok http 5005`
5. specify your Telegram Bot's credentials in the `credentials.yml` (pass the ngrok URL with `https` as webhook URL as
   demonstrated below):

```
telegram:
   access_token: "<your access token>"
   verify: "<your bot's name>"
   webhook_url: "https://<your NGROK URL>.ngrok.io/webhooks/telegram/webhook"
```

6. fill in the env-vars in the .env file
7. retrain the model using `rasa train` or use the existing one
8. run the command `docker-compose up` in your commandline
9. wait for rasa to be up and running (look for "root  - Rasa server is up and running." in the console)  
10. go to Telegram and start talking to your bot (default: @tum_raina_dev_bot)

### [Local Setup] Installing RasaX for local testing [unstable]

**Warning:**
*At the time of developing RAINA, this did not work as described in the docs and blog posts due to conflicts in the
dependency versions of Rasa and RasaX! I recommend using a deployed version of RasaX and connecting it to your
git-repository for development and testing (setup explained below).*

Sources:  
https://rasa.com/docs/rasa-x/installation-and-setup/install/local-mode/  
https://medium.com/co-learning-lounge/step-by-step-guide-to-install-rasa-x-in-windows-without-docker-85da8502bce

These commands have to be executed in the Anaconda prompt

1. activate your virtual environment  
   `conda activate <your new Environment>`
2. upgrade pip on your system  
   `python -m pip install --upgrade pip`
3. install RasaX on your system (may take several minutes)  
   `pip3 install rasa-x --extra-index-url https://pypi.rasa.com/simple --use-deprecated=legacy-resolver`
4. start rasaX by using:  
   `rasa x`
5. to set a custom password use:  
   `export RASA_X_PASSWORD="<your password>"`

## RasaX Deployment on a VM/Server

For using this project with RasaX you need to follow the instruction by Rasa to create a new instance on a server VM.
For developing RAINA RasaX was installed using docker-compose, following this guide:  
https://rasa.com/docs/rasa-x/installation-and-setup/install/docker-compose

All files will be located in `/etc/rasa` start RasaX with
`docker-compose up -d` and stop it with `docker-compose down`.  
The NLU models were trained via RasaX which was connected to the gitlab repository. The action server was dockerized and
added to th docker-compose file as specified below.  
(Disclaimer: all the steps below have to be done in order to get a working RasaX deployment)

### [SSH on VM / Server] Adding the action server to the RasaX docker-compose

Since the docker-compose.yml might change if RasaX is being updated, the part for the custom action server will be
written in a docker-compose.override.yml in the same folder as the docker-compose.yml.  
(Source: https://rasa.com/docs/rasa-x/installation-and-setup/customize#connecting-a-custom-action-server)

**Important:**  
*Make sure that you have built a docker image of the action server and pushed it to your docker-hub repository as
explained above! This image will be used in the docker-compose.override.yml!*

1. create a new docker-compose.override.yml  
   `touch docker-compose.override.yml`
2. add the following content to the created file  
   `nano docker-compose.override.yml`

```
version: '3.4'  
services:  
  app:  
    image: '<account_username>/<repository_name>:<custom_image_tag>'
    volumes:
      - './actions:/app/actions/db'
    environment:
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_BUCKET_NAME: ${AWS_BUCKET_NAME}
      AWS_BUCKET_URL: ${AWS_BUCKET_URL}
```

3. add the AWS S3 credentials directly or add them to the env-vars (.env)  
   `nano .env`

```
AWS_ACCESS_KEY_ID="<your accessKey>"
AWS_SECRET_ACCESS_KEY="<your secretKey>"
AWS_BUCKET_NAME="<your bucketname>"
AWS_BUCKET_URL="<your bucketURL>"
```

(Source: https://rasa.com/docs/rasa-x/installation-and-setup/customize#environment-variables)

### [SSH on VM / Server] Connecting a Telegram Bot to the RasaX Instance

The freshly installed RasaX instance has been modified including the following steps:

1. adding an SSL certificate to the VMs domain (necessary to link telegram)  
   https://rasa.com/docs/rasa-x/installation-and-setup/customize#securing-with-ssl  
   https://certbot.eff.org/instructions
2. adding the SSL certificate to be used by RasaX to the nginx config, see:  
   `nginx-config-files/rasax.nginx.template`
3. connecting the Telegram Bot created using 'botfather' in  
   `credentials.yml`

```
rasa:
  url: ${RASA_X_HOST}/api

telegram:
 access_token: "<your access token>"
 verify: "<your bot's name>"
 webhook_url: "https://<your domain>/webhooks/telegram/webhook"
```
