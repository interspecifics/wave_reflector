import subprocess
import sys

# Define the bands and their corresponding titles
# bands = ['delta', 'theta', 'alpha', 'beta', 'gamma']
bands = ['theta', 'alpha', 'beta', 'gamma']

# Define the common parameters
interval = 5
ip = '192.168.0.100'
port = 5005

# Path to the current Python interpreter
python_executable = sys.executable

# Launch PSD_gradient_LFO.py for each band and store the process handles
processes = []
for band in bands:
    process = subprocess.Popen([
        python_executable, 'PSD_gradient_LFO.py',
        '--band', band,
        # '--interval', str(interval),
        '--ip', ip,
        '--port', str(port)
    ])
    processes.append(process)

# Wait for all subprocesses to complete
for process in processes:
    process.wait()

print("All PSD_gradient_LFO.py processes have completed.")