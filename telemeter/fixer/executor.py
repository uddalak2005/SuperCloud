import subprocess

class CommandExecutor:

    def run(self, command_array, timeout=90):
        try:
            result = subprocess.run(
                command_array,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()
            }

        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Timeout"
            }
