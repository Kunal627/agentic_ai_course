
from agent_runtime.tools.errors import ToolPolicyError
from agent_runtime.tools.policies import ToolPolicy

policy = ToolPolicy(
    allowed_tools=frozenset({
        "calculator.add",
        "calculator.subtract",
    })
)

# An explicitly allowed tool should pass.
policy.check("calculator.add")
print("Allowed tool accepted.")

# A tool outside the allowlist should be rejected.
try:
    policy.check("filesystem.delete")
except ToolPolicyError as exc:
    print(f"Disallowed tool rejected: {exc}")
else:
    raise AssertionError("Disallowed tool was accepted.")

# An empty allowlist should deny every tool.
deny_all = ToolPolicy()

try:
    deny_all.check("calculator.add")
except ToolPolicyError:
    print("Empty allowlist denies execution.")
else:
    raise AssertionError("Empty allowlist should deny every tool.")

print("Tool policy tests passed.")
