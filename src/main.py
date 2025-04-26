from flask import Flask, render_template, request, jsonify
from celery import Celery

app = Flask(__name__)

# Load configuration from config.py
app.config.from_object('config')

# Configure Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@app.route("/", methods=["GET", "POST"])
def primes():
    if request.method == "POST":
        # Get the number from the form
        number = request.form.get("prime-input")
        if number and number.isdigit():
            number = int(number)
            # Send the job to the Celery worker and wait for the result
            task = check_prime.delay(number)
            result = task.get(timeout=30)  # Wait for the task to complete (timeout in seconds)
            return render_template("index.html", is_prime=result['is_prime'], number=result['number'])
        else:
            return render_template("index.html", error="Please enter a valid number.")
    # Handle GET request
    return render_template("index.html", is_prime=None, number=None, error=None)

@app.route("/result/<task_id>")
def result(task_id):
    task = check_prime.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending...'}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result': task.result}
    else:
        response = {'state': task.state, 'status': str(task.info)}
    return jsonify(response)

@celery.task
def check_prime(number):
    is_prime = True
    if number < 2:
        is_prime = False
    else:
        for i in range(2, int(number**0.5) + 1):
            if number % i == 0:
                is_prime = False
                break
    return {'number': number, 'is_prime': is_prime}