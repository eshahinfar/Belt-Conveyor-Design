# Belt-Conveyor-Design

Engineering design utilities and references for belt conveyor projects. This repository now
includes a Django web application that collects quick calculators inspired by MITCalc for
estimating conveyor power, pulley torque, and belt tensions.

## Getting started

1. Create and activate a Python virtual environment (optional but recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Apply migrations and run the development server:
   ```bash
   cd engineering_site
   python manage.py migrate
   python manage.py runserver
   ```
4. Open http://127.0.0.1:8000/ in a browser to access the calculators.

## Calculators

- **Belt power** – estimates the drive power required based on throughput, lift height, and
  frictional losses.
- **Pulley torque** – converts motor power and rotational speed to delivered torque.
- **Belt tension** – evaluates tight-side belt tension using Euler's belt friction equation.

The results provide quick sizing guidance and should be verified with detailed engineering
standards (CEMA, ISO, etc.) before final design decisions.
