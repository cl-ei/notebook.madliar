FROM python:3.7.3

EXPOSE 10091

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN echo 'export LANG="C.UTF-8"' >> /etc/profile


WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

CMD ["python", "run.py"]
