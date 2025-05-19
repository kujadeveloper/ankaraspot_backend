FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Istanbul

COPY ./ /app
WORKDIR /app
RUN apt update
RUN python -m pip install --upgrade pip
RUN pip install gunicorn
RUN apt-get install libmagic1
RUN apt-get install -y graphviz
RUN pip install --upgrade pip setuptools
RUN pip install -r requirement.txt
#RUN pip list --outdated | awk 'NR>2 {print $1}' | xargs -n1 pip install -U
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
EXPOSE 8000
CMD ["gunicorn", "-w", "10", "-b", "0.0.0.0:8000", "FiyatorBackend.wsgi:application", "--reload", "--log-level", "debug"]