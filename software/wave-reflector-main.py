import subprocess
import time

def run_script(script_name, args):
    python_executable = r'C:\Users\alfredo\Desktop\wave-reflector\.venv\Scripts\python'
    return subprocess.Popen([python_executable, script_name] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    # Arguments for EEG_tcp_server_replay.py
    file_path = 'C:\\Users\\alfredo\\Desktop\\wave-reflector\\CyKit\\Examples\\epocx_readings\\a_eeg_data_1.txt'
    ports = ['9001', '9002', '9003']  # Use three ports
    sample_rate = '128'

    # Arguments for signalQ_tcp_client.py
    host = 'localhost'
    port = '9002'
    buffer_size = '512'
    image_path = 'C:\\Users\\alfredo\\Desktop\\wave-reflector\\1020-electrode-placement.png'

    # Arguments for ICAanalysis_tcp_client.py
    ica_host = 'localhost'
    ica_port = '9003'
    ica_buffer_size = '512'
    ica_sample_rate = '128'

    # Arguments for EEG_analysis_plot.py
    analysis_port = '9003'  # Use the same port as ICAanalysis_tcp_client.py

    # Run EEG_tcp_server_replay.py
    server_args = ['--file_path', file_path, '--ports'] + ports + ['--sample_rate', sample_rate]
    server_process = run_script('EEG_tcp_server_replay.py', server_args)

    # Give the server some time to start
    time.sleep(5)

    # Run signalQ_tcp_client.py
    client_args = ['--host', host, '--port', port, '--buffer_size', buffer_size, '--sample_rate', sample_rate, '--image_path', image_path]
    client_process = run_script('signalQ_tcp_client.py', client_args)

    # Give the client some time to start
    time.sleep(5)

    # Run ICAanalysis_tcp_client.py
    ica_args = ['--host', ica_host, '--port', ica_port, '--buffer_size', ica_buffer_size, '--sample_rate', ica_sample_rate]
    ica_process = run_script('ICAanalysis_tcp_client.py', ica_args)

    # Give the ICA analysis some time to start
    time.sleep(5)

    # Run EEG_analysis_plot.py
    analysis_args = ['--host', host, '--port', analysis_port, '--buffer_size', buffer_size, '--sample_rate', sample_rate]
    analysis_process = run_script('EEG_analysis_plot.py', analysis_args)

    try:
        # Wait for the processes to complete
        while True:
            output = server_process.stdout.readline()
            if output:
                print(f"Server: {output.decode().strip()}")
            output = client_process.stdout.readline()
            if output:
                print(f"Client: {output.decode().strip()}")
            output = ica_process.stdout.readline()
            if output:
                print(f"ICA: {output.decode().strip()}")
            output = analysis_process.stdout.readline()
            if output:
                print(f"Analysis: {output.decode().strip()}")

            if server_process.poll() is not None:
                print("Server process terminated.")
                break
            if client_process.poll() is not None:
                print("Client process terminated.")
                break
            if ica_process.poll() is not None:
                print("ICA process terminated.")
                break
            if analysis_process.poll() is not None:
                print("Analysis process terminated.")
                break

    except KeyboardInterrupt:
        print("Terminating processes...")
        server_process.terminate()
        client_process.terminate()
        ica_process.terminate()
        analysis_process.terminate()

    # Capture any remaining output
    server_out, server_err = server_process.communicate()
    client_out, client_err = client_process.communicate()
    ica_out, ica_err = ica_process.communicate()
    analysis_out, analysis_err = analysis_process.communicate()

    print(f"Server output: {server_out.decode()}")
    print(f"Server error: {server_err.decode()}")
    print(f"Client output: {client_out.decode()}")
    print(f"Client error: {client_err.decode()}")
    print(f"ICA output: {ica_out.decode()}")
    print(f"ICA error: {ica_err.decode()}")
    print(f"Analysis output: {analysis_out.decode()}")
    print(f"Analysis error: {analysis_err.decode()}")