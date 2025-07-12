from flask import Flask, render_template, request, jsonify
import math

app = Flask(__name__)

def extrusion_calculator(setpoint_speed, runout_length, ratio, die_cavities, billet_temp_C=470, alloy='6xxx'):
    burp_psi = 800 + 1700 * ((math.log(ratio) - math.log(10)) / (math.log(100) - math.log(10)))
    if alloy == '7xxx':
        burp_psi *= 1.2
    burp_psi = min(2500, max(800, burp_psi))
    burp_psi = round(burp_psi / 100) * 100

    puller_speed_pct = (setpoint_speed / 15) * 100 * 1.03
    if alloy == '7xxx':
        puller_speed_pct *= 0.9
    puller_speed_pct = min(100, max(1, puller_speed_pct))

    torque_ramp_time = 0.1 + 9.9 * (setpoint_speed / 15) * (470 / billet_temp_C)
    if alloy == '7xxx':
        torque_ramp_time *= 1.1
    torque_ramp_time = min(10.0, max(0.1, torque_ramp_time))

    base_force = 500 + 1400 * ((die_cavities - 1) / 3)
    ratio_factor = 0.3 * ((math.log(ratio) - math.log(10)) / (math.log(100) - math.log(10)))
    temp_factor = 0.1 * ((500 - billet_temp_C) / 30)  # Hotter softens, less force
    speed_factor = 0.2 * (setpoint_speed / 15)
    length_factor = 0.05 * (runout_length / 41)
    puller_force = base_force * (1 + ratio_factor + temp_factor + speed_factor + length_factor)
    puller_force = min(1900, max(500, puller_force))
    puller_force = round(puller_force / 50) * 50

    return burp_psi, puller_speed_pct, torque_ramp_time, puller_force

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.form
    ratio = float(data.get('ratio') or 0)
    runout_length = float(data.get('runout') or 0)
    setpoint_speed = float(data.get('speed') or 0)
    die_cavities = int(data.get('cavities') or 1)
    billet_temp_C = float(data.get('billet_temp') or 470)
    alloy = data.get('alloy') or '6xxx'
    burp, puller_pct, ramp, force = extrusion_calculator(setpoint_speed, runout_length, ratio, die_cavities, billet_temp_C, alloy)
    return jsonify({'burp_psi': burp, 'puller_speed_pct': round(puller_pct), 'torque_ramp_time': round(ramp, 1), 'puller_force': round(force / 10)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)