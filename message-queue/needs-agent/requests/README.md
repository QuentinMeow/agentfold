# requests/ — an agent's move

Durable work assigned by the owner or one agent/session to another. Each request names
the action, full source, observable completion, and dependency timing. The next relevant
agent claims it, acts or converts it into a task, and deletes it only with the completed
action or an explicit rejection.

File one with a timing-prefixed name by copying `templates/queue/request.md`.
