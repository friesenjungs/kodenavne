FROM backend-base

WORKDIR /flask-deploy

COPY . .

CMD ["bash", "./container-start-script.sh"]