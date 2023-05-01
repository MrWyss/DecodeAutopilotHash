from flask import Flask, render_template, request
from utils.autopilotutility import convert_from_autopilot_hash

app = Flask(__name__)

version = 'v1.0.5'

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        hash_input = request.form['hash']
        hash_list = convert_from_autopilot_hash(Hash=hash_input)
        return render_template('home.html', result=hash_list, version=version)
    else:
        return render_template('home.html', version=version)

if __name__ == '__main__':
    app.run(debug=True)
