import json
from executor import CommandExecutor


class Fixer:

    def __init__(self, rulebook_path="rulebook.json"):
        with open(rulebook_path) as f:
            self.rulebook = json.load(f)

        self.executor = CommandExecutor()


    # 1️⃣ Entry point from backend
    def handle_incident(self, remediation_payload):
        issue_type = remediation_payload["issue_type"]
        target = remediation_payload.get("target", {})

        if issue_type not in self.rulebook["issues"]:
            raise Exception("Unknown issue type")

        issue_config = self.rulebook["issues"][issue_type]

        return self.execute_issue(issue_config, target)


    # 2️⃣ This is where your function goes
    def execute_issue(self, issue_config, target):
        steps = sorted(issue_config["steps"], key=lambda x: x["priority"])

        for step in steps:
            action_name = step["action"]

            command = self.resolve_action(action_name, target)

            print(f"Executing: {command}")

            result = self.executor.run(command)

            if result["exit_code"] != 0:
                print("Step failed:", result["stderr"])
                return self.handle_failure(issue_config, target)

        # After steps → run health check
        return self.run_health_check(issue_config, target)


    # 3️⃣ Action resolver
    def resolve_action(self, action_name, target):
        actions = self.rulebook["actions"]

        if action_name not in actions:
            raise Exception("Action not allowed")

        action_config = actions[action_name]
        command_template = action_config["command_template"]

        resolved_command = []

        for token in command_template:
            resolved_token = token.format(**target)
            resolved_command.append(resolved_token)

        return resolved_command


    # 4️⃣ Health check
    def run_health_check(self, issue_config, target):
        health_name = issue_config.get("health_check")

        if not health_name:
            return {"status": "success", "message": "No health check required"}

        health_config = self.rulebook["health_checks"][health_name]

        command = [
            token.format(**target)
            for token in health_config["command_template"]
        ]

        result = self.executor.run(command)

        criteria = health_config["success_criteria"]

        if "exit_code" in criteria:
            if result["exit_code"] == criteria["exit_code"]:
                return {"status": "success"}

        if "stdout_equals" in criteria:
            if result["stdout"] == criteria["stdout_equals"]:
                return {"status": "success"}

        return self.handle_failure(issue_config, target)


    # 5️⃣ Rollback
    def handle_failure(self, issue_config, target):
        rollback = issue_config.get("rollback")

        if rollback:
            print("Executing rollback...")
            command = self.resolve_action(rollback["action"], target)
            self.executor.run(command)

        return {"status": "failed"}


# 6️⃣ Local testing block
if __name__ == "__main__":
    sample_payload = {
        "incident_id": "abc-123",
        "issue_type": "memory_high",
        "target": {
            "container_name": "auth-container"
        }
    }

    fixer = Fixer()
    result = fixer.handle_incident(sample_payload)
    print(result)