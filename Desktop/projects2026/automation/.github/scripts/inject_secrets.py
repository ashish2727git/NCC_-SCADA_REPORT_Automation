#!/usr/bin/env python3
"""
Injects AWS credentials and secrets into a rendered ECS task definition file.
Called by the CI/CD pipeline AFTER amazon-ecs-render-task-definition runs,
to prevent the render action from stripping injected environment variables.

Usage:
    python3 inject_secrets.py <task-definition-file>

Secrets are read from environment variables:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, TG_BOT_TOKEN, TG_ADMIN_CHAT, ADMIN_SECRET
"""
import json
import os
import sys

if len(sys.argv) < 2:
    print("Usage: inject_secrets.py <task-definition-file>")
    sys.exit(1)

task_def_file = sys.argv[1]

with open(task_def_file, encoding="utf-8") as f:
    td = json.load(f)

env = td["containerDefinitions"][0]["environment"]

# Keys to inject — remove any stale duplicates first
keys_to_inject = {
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION",
    "TG_BOT_TOKEN",
    "TG_ADMIN_CHAT",
    "ADMIN_SECRET",
    "GODADDY_API_KEY",
}
env = [e for e in env if e["name"] not in keys_to_inject]

# Read from environment (set by GitHub Actions secrets)
injected = []
for key in keys_to_inject:
    value = os.environ.get(key, "")
    if value:
        env.append({"name": key, "value": value})
        injected.append(key)
    elif key == "AWS_DEFAULT_REGION":
        env.append({"name": key, "value": "ap-south-1"})
        injected.append(key)

td["containerDefinitions"][0]["environment"] = env
td["taskRoleArn"] = "arn:aws:iam::802346121670:role/nexus-ecs-task-execution-role"

with open(task_def_file, "w", encoding="utf-8") as f:
    json.dump(td, f, indent=2)

print(f"Injected {len(injected)} secret env vars: {', '.join(sorted(injected))}")
print(f"Total env vars in container: {len(env)}")
